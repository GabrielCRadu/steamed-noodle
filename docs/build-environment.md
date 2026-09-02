# Build environment and handoff

How to set up a machine for this project and get back to the state
[`verification-log.md`](verification-log.md) describes, plus what the next piece of work is.

Everything here has been done at least once, on Ubuntu 24.04 under WSL2. Where a step is a
recorded trap rather than a normal instruction, it says so.

**Nothing in this document flashes a phone.** See [Do not do this yet](#do-not-do-this-yet)
at the bottom before you get ideas.

---

## 0. What you need

- A Linux host. Ubuntu 24.04 is what every verified build in the log used. WSL2 counts.
- About **40 GB of free disk**. The kernel source, the pmbootstrap chroots and the generated
  images add up faster than you expect.
- No phone. Everything in sections 1 to 6 is hardware-independent.

---

## 1. WSL2 on Windows

Skip this section on a real Linux host.

### The trap

`wsl --install -d Ubuntu-24.04` on a clean Windows 11 machine can fail with:

```
Downloading: Windows Subsystem for Linux 2.7.12
Installing: Windows Subsystem for Linux 2.7.12
Catastrophic failure
```

That message is just `E_UNEXPECTED` and tells you nothing. The actual state on the machine
where this happened (Windows 11 Pro 26200, Ryzen 7 5700U):

```
VirtualMachinePlatform             disabled
Microsoft-Windows-Subsystem-Linux  disabled
HypervisorPlatform                 disabled
HypervisorPresent                  False
VirtualizationFirmwareEnabled      True     <- CPU/BIOS were fine
```

WSL 2.7.x installs itself as a Store package (MSIX) and had failed at that step without ever
enabling the Windows features it depends on. `VirtualMachinePlatform` is the virtualization
layer WSL2 runs its Linux kernel on top of, as a very thin virtual machine. Without it there
is nothing for WSL2 to run on.

### The fix

Enable the features by hand first, which is the documented manual route. In **PowerShell as
Administrator**:

```powershell
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
```

Both must answer `The operation completed successfully.`

**Reboot.** The hypervisor only loads at boot; skipping this makes the next step fail again.

Then install WSL on its own, before adding any distribution, so that a failure tells you which
half broke:

```powershell
wsl --install --no-distribution
wsl --install -d Ubuntu-24.04
```

Check it:

```powershell
wsl -l -v
```

You want `Ubuntu-24.04` at `VERSION 2`.

### If it still fails

Get the real error instead of guessing, as Administrator:

```powershell
Get-WinEvent -LogName Microsoft-Windows-AppXDeploymentServer/Operational -MaxEvents 30 |
  Where-Object { $_.LevelDisplayName -ne 'Information' } |
  Select-Object TimeCreated, Id, LevelDisplayName, Message | Format-List
```

You can also read feature state without Administrator rights, which is how the diagnosis above
was made:

```powershell
Get-CimInstance Win32_OptionalFeature |
  Where-Object { $_.Name -match 'Linux|VirtualMachine|Hyper-V|HypervisorPlatform' } |
  Select-Object Name, InstallState
```

`InstallState` is `1` for enabled, `2` for disabled.

---

## 2. Host packages

Inside Ubuntu:

```bash
sudo apt update
sudo apt install -y build-essential git clang lld llvm pipx \
                    gcc-aarch64-linux-gnu flex bison libssl-dev bc
pipx install pmbootstrap
pipx ensurepath
```

Then reopen the shell so `pmbootstrap` is on `PATH`.

Why both toolchains: the standalone kernel sanity build in section 6 uses the GCC cross
compiler (`gcc-aarch64-linux-gnu`), while `linux-oneplus-instantnoodle`'s APKBUILD builds with
`ARCH=arm64 LLVM=1`, matching the convention the packaged `linux-postmarketos-qcom-sm8250`
kernel uses. Both paths have been verified; keep both installed.

---

## 3. Passwordless sudo

**This is a recorded trap, not a preference.** Without it, `pmbootstrap`'s internal
`sudo losetup` and mount calls hang forever waiting for a password prompt that can never be
answered, with no error message. It silently hung twice before the cause was found.

```bash
echo "$USER ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/pmbootstrap
sudo chmod 0440 /etc/sudoers.d/pmbootstrap
```

---

## 4. Do not build on `/mnt/c`

WSL reaches the Windows drive through a translation layer that is several times slower for the
many-small-files workload a kernel build is. Keep the kernel clone, the pmaports checkout and
the pmbootstrap work directory in the Linux filesystem, under `~/`.

Editing this repo from the Windows side is fine. Building in it is not.

---

## 5. Rebuilding the verified state

This reproduces what [`verification-log.md` §7.5](verification-log.md) recorded.

### 5.1 Get the sources

```bash
cd ~
git clone https://github.com/GabrielCRadu/steamed-noodle.git
git clone --depth 1 https://gitlab.postmarketos.org/postmarketOS/pmaports.git
```

### 5.2 Drop the draft packages into pmaports

The four packages in this repo's `pmaports/` are not part of upstream pmaports. They have to be
copied into a local pmaports checkout for `pmbootstrap` to see them:

```bash
cp -r ~/steamed-noodle/pmaports/* ~/pmaports/device/testing/
```

### 5.3 Initialize pmbootstrap against that checkout

```bash
pmbootstrap init
```

Point it at `~/pmaports` when it asks for the aports path. Then answer:

- vendor: `oneplus`
- codename: `instantnoodle`
- user interface: `none` for now, see section 7

If the packages were copied correctly, `instantnoodle` appears as a valid codename alongside
the officially packaged `instantnoodlep` and `kebab`, with **no** "create new port" prompt.
If it offers to create a new port instead, the copy in 5.2 did not land where pmbootstrap
looks.

### 5.4 Checksums and build

```bash
pmbootstrap checksum linux-oneplus-instantnoodle
pmbootstrap -y build linux-oneplus-instantnoodle
pmbootstrap -y build device-oneplus-instantnoodle
pmbootstrap -y build firmware-oneplus-instantnoodle
pmbootstrap -y build alsa-ucm-conf-oneplus-instantnoodle
```

Expect roughly 18 to 20 minutes for the kernel on a cold cache, a few seconds for the rest.
The firmware package downloads the proprietary blobs from
`github.com/Xo666/linux-oneplus-instantnoodle` by commit hash; you do not need to extract them
from an OxygenOS image yourself. See the licensing caveat in that APKBUILD's header.

### 5.5 Build the images

```bash
pmbootstrap install --split
```

This produced `oneplus-instantnoodle-boot.img` (512 MB) and `oneplus-instantnoodle-root.img`
(829 MB) last time. That is the practical ceiling of what can be verified without the phone.

---

## 6. Optional: standalone kernel sanity build

Useful when you want to check a device tree change quickly without going through packaging.

```bash
cd ~
git clone --depth 1 -b 6.16.7 https://github.com/Xo666/mainline-instantnoodle.git
cd mainline-instantnoodle
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- op8_defconfig
make -j"$(nproc)" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- Image.gz dtbs
```

About 5m30s on 16 cores. Produces `arch/arm64/boot/Image.gz` and
`arch/arm64/boot/dts/qcom/sm8250-oneplus-instantnoodle.dtb`.

To inspect a device tree change, decompile the result and read it back:

```bash
dtc -I dtb -O dts arch/arm64/boot/dts/qcom/sm8250-oneplus-instantnoodle.dtb | less
```

That is how the charger port in §7.5 was verified not to disturb the zap-shader node.

---

## 7. What to do next

The work queue, in order, per [`verification-log.md` §7.6](verification-log.md).

### 7.1 The native layer, first

Write a UI package that starts `gamescope` at boot for this device port, in the shape of the
existing `postmarketos-ui-*` packages in `~/pmaports/main/`.

This is assembly, not porting. Alpine `aarch64` already ships everything it needs:

| Package | Version checked | Repo |
|---|---|---|
| `gamescope` | 3.16.24-r1 | community |
| `mesa-vulkan-freedreno` (Turnip) | 26.1.6-r1 | main |
| `vulkan-loader` | 1.4.360-r0 | main |
| `seatd`, `wlroots0.20`, `libliftoff`, `xwayland`, `mangohud` | | community |

Then rebuild the image from section 5.5 with that UI selected in `pmbootstrap init` and confirm
the packages resolve and install. That is as far as it can be verified without hardware.

### 7.2 The x86 translation layer, second

**Do not package FEX for musl.** §7.6.2 and §7.6.6 explain why at length. The short version:
it is not a supported configuration upstream, there is no CI for it, and nobody runs it that
way. Both documented postmarketOS routes put a glibc distribution in a container on top of the
musl host:

- `apk add distrobox`, Ubuntu 24.04 container, FEX from its Ubuntu PPA
- or a Debian container with box86/box64

Every container tool needed is already in Alpine `aarch64` (`distrobox`, `podman`,
`docker-engine`, `squashfuse`, `erofs-utils`), and `op8_defconfig` already has
`CONFIG_BINFMT_MISC` plus every container primitive. The one kernel gap is `CONFIG_EROFS_FS`,
which `erofs-fuse` covers in userspace.

Track FEX issue [#4120](https://github.com/FEX-Emu/FEX/issues/4120) while doing this. If it
lands, the Snapdragon 865 is on its published drop list, and box64 becomes the translator
rather than FEX.

---

## Do not do this yet

**Do not flash anything.** The images from section 5.5 have never been on real silicon, and a
pre-flight review found real gaps in the flashing procedure itself. Before any phone is
touched, these have to be resolved, and they are documented in the install-flow section of
`Gaming Mainline OnePlus 8.md`:

- **Step 0**: download and checksum a full OxygenOS restore package matching the exact model
  and region (IN2013/IN2010, not carrier variants), **before** unlocking the bootloader. This
  is the only real safety net.
- **Step 5**: compare the reported `super` partition size from `fastboot getvar all` against
  the actual rootfs image size. Neither `pmbootstrap` nor `fastboot` checks this for you.
- **Step 6**: `pmbootstrap flasher flash_vbmeta` before writing the rootfs, not after, or
  Android Verified Boot may reject the unsigned kernel. Whether the OnePlus 8 enforces this
  after bootloader unlock is itself unverified.
- `deviceinfo_super_partitions` in the draft port **does nothing**; it is not in the schema
  `pmbootstrap` actually reads. Do not treat it as a safety mechanism.

The other unresolved question is fork divergence (§1.4): no known kernel tree has a working
GPU, a working charger and clean USB-C orientation switching at the same time. The charger
patch in `pmaports/linux-oneplus-instantnoodle/` is a compile-verified candidate fix, not a
resolution.
