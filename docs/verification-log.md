# Verification Log

Every load-bearing claim in [`Gaming Mainline OnePlus 8.md`](../Gaming%20Mainline%20OnePlus%208.md),
checked against primary sources. The original document is research output with no
citations to working code; this log records what survived contact with the actual
kernel tree, device tree, and package repositories.

**Target device:** OnePlus 8, global IN2013/IN2010, codename `instantnoodle`, SM8250 (kona).
**Intended use:** dedicated Linux handheld. Android wiped. No modem/calls/SMS required.

**All checks performed 2026-08-24.** Anything marked OPEN needs hardware to settle.

Verdict key: **CONFIRMED** · **WRONG** · **PARTIAL** - right in outline, wrong in detail · **OPEN** - undecidable without the device.

---

## 1. Device enablement

### 1.1 `instantnoodle` is supported in postmarketOS - **WRONG**

The doc's install flow ([line 141](../Gaming%20Mainline%20OnePlus%208.md#L141)) says to run `pmbootstrap init`
and choose codename `instantnoodle`. That fails today: there is no such device package.

pmaports `device/` contains exactly these OnePlus ports:

| Package | Device |
|---|---|
| `device/community/device-oneplus-enchilada` | OnePlus 6 |
| `device/community/device-oneplus-fajita` | OnePlus 6T |
| `device/testing/device-oneplus-bacon` | OnePlus One |
| `device/testing/device-oneplus-billie2` | Nord N100 |
| `device/testing/device-oneplus-guacamole` | OnePlus 7 Pro |
| `device/testing/device-oneplus-instantnoodlep` | **OnePlus 8 Pro** |
| `device/testing/device-oneplus-kebab` | **OnePlus 8T** |

The Pro and the 8T are packaged. The plain OnePlus 8 is not. The doc's parenthetical
- "`instantnoodle` (sau `instantnoodlep` pentru varianta Pro)" - has the support
situation backwards.

*Source:* pmaports GitLab API, `repository/tree?path=device/{main,community,testing}`.

### 1.2 Upstream mainline has an SM8250 OnePlus device tree - **WRONG**

`arch/arm64/boot/dts/qcom` in torvalds/linux master has 628 files. The SM8250 boards
present are: `hdk`, `mtp`, `samsung-r8q`, `samsung-x1q`, `sony-xperia-edo-pdx203`,
`sony-xperia-edo-pdx206`, `xiaomi-elish-{boe,csot}`, `xiaomi-pipa`. **No OnePlus SM8250
board exists upstream at all** - not the 8, not the 8 Pro, not the 8T.

Even postmarketOS's own SM8250 kernel fork (`soc/qualcomm-sm8250/linux`, tag `sm8250-7.1.0`,
described as "Mainline kernel fork for SM8250") carries only `sm8250-oneplus-instantnoodlep.dts`
and `sm8250-oneplus-kebab.dts`.

So "mainline support" for this device means *a fork of mainline*, not mainline. This
distinction runs through the whole document and is the single biggest correction.

*Source:* GitHub contents API on torvalds/linux; pmOS GitLab API on the SM8250 kernel fork.

### 1.3 The device boots mainline anyway - **CONFIRMED**

The postmarketOS wiki page for `oneplus-instantnoodle` reports `booting = yes`,
`packaged = no`, `category = testing`, `pmoskernel = 6.17.0`, and critically
`status_3d = Y`. Maintainers listed: ObiKeahloa, Xiaoou.

The port lives in two out-of-tree forks:

- [`github.com/Xo666/mainline-instantnoodle`](https://github.com/Xo666/mainline-instantnoodle) - branch `6.16.7`, pushed 2026-01-14. **Verified to contain `sm8250-oneplus-instantnoodle.dts`.** Authored by `Xiaoou <xo666@postmarketos.org>`, © 2025.
- [`gitlab.com/ObiKeahloa/linux`](https://gitlab.com/ObiKeahloa/linux/-/tree/sm8250/v6.13-instantnoodle) - branch `sm8250/v6.13-instantnoodle`.

**This is the project's foundation.** It is one contributor's branch, not an upstream
guarantee - but the author has a postmarketOS address, which is a reasonable signal the
work may eventually be packaged.

*Source:* postmarketOS wiki (MediaWiki API); GitHub API.

---

## 2. Hardware claims, checked against the device tree

Audited against `reference/dts/sm8250-oneplus-instantnoodle.dts` (Xo666 fork, branch `6.16.7`,
1643 lines). This is the authoritative statement of what the port actually drives.

| Doc claim | Reality | Verdict |
|---|---|---|
| Touchscreen is `goodix` or `synaptics_dsx` over I²C | `samsung,s6sy761` @ 0x48 on i2c13 | **WRONG** |
| Panel over **two** MIPI-DSI lanes | `samsung,amb655uv01`, single link on `mdss_dsi0` | **WRONG** |
| Panel 1080×2400, 90 Hz | Confirmed; wiki notes 60/90 Hz both supported | **CONFIRMED** |
| UFS 3.0 | DTS/wiki declare `jedec,ufs-2.0` | **PARTIAL** |
| Audio via WCD9385 + LPASS/Hexagon | `qcom,wcd9380-codec` present, **plus** 2× `nxp,tfa9874` speaker amps on i2c15 | **PARTIAL** |
| ADSP/CDSP firmware needed | Confirmed - `adsp.mbn`, `cdsp.mbn` both required | **CONFIRMED** |
| Adreno 650 works via Turnip/`msm` | `&gpu status = "okay"`, needs `a650_zap.mbn` | **CONFIRMED** |
| GPU boosts to 670 MHz | 670 MHz is the Snapdragon **865+** clock. Plain 865 tops at 587 MHz | **WRONG** |
| `pm8150b-charger` manages charging | **No charger node exists in this DTS at all** | **OPEN** - see §4 |
| USB-C SuperSpeed orientation quirk | `fcs,fsa4480` SBU mux present; orientation behaviour untested | **OPEN** |

### Additional hardware the doc never mentions

- **`&mdss_dp { status = "okay" }`** - DisplayPort alt-mode over USB-C is enabled. Relevant
  to a docked handheld setup and absent from the document entirely.
- **`&pm8150b_vbus`**, 500 mA-3 A source regulator - the phone can power USB accessories (OTG out).
- **Battery**: `simple-battery`, 16.37 Wh design energy, 4270 mAh, 3.4-4.435 V.
- **Fuel gauge**: `ti,bq27411` - accurate charge reporting.
- **Front camera only** (`sony,imx471`). Rear `imx586` is absent from the DTS.

### Known-broken, per wiki

Modem (`sdx55m`), sensors (`slpi` loads but is unconfigured), haptics (`awinic,aw8697`),
rear camera. **None of these matter for a dedicated handheld** except haptics, which is
a comfort loss only.

---

## 3. Required firmware blobs

`&gpu` will not probe without its zap shader, so this is a hard prerequisite for the
entire graphics stack. All five are proprietary and must be extracted from an OxygenOS
image into `/lib/firmware/qcom/sm8250/OnePlus/`:

| Blob | Purpose | Consequence if missing |
|---|---|---|
| `a650_zap.mbn` | GPU zap shader (signed) | **No GPU. Project stops.** |
| `adsp.mbn` | Audio DSP | No audio |
| `cdsp.mbn` | Compute DSP | No compute offload |
| `venus.mbn` | Video decode | No hardware video |
| `slpi.mbn` | Sensor DSP | No sensors (already broken) |

Note the vendor subdirectory `.../sm8250/OnePlus/` - the doc says `/lib/firmware/qcom/sm8250/`
([line 39](../Gaming%20Mainline%20OnePlus%208.md#L39)), which is the wrong path.

Additionally from `linux-firmware` (open, not device-specific): `a650_sqe.fw`, `a650_gmu.bin`,
ath11k QCA6390 WiFi, and QCA Bluetooth firmware.

**These can be sourced without the phone** - an OxygenOS payload dump is enough.

---

## 4. Power and thermals - the biggest open question

The document's thermal architecture rests on passthrough power: the GameSir X3 Pro's
Peltier cooler keeps the SoC at 45-52 °C, so the CPU never throttles, and the phone charges
through the controller meanwhile. The cooling half of that is sound - the Peltier draws
10-12 W **from the wall charger, not from the phone**, so active cooling works regardless
of what the phone's charging stack does.

The charging half is unverified and looks doubtful:

- The wiki reports charging works at **5 W** via `qcom,pm8150b-charger`, and that Warp/fast
  charging needs `oplus,stm8s-fastcg`, **for which no driver exists**.
- But the Xo666 DTS **declares no charger node whatsoever**. It configures `pm8150b_typec`
  with sink PDOs of `PDO_FIXED(5000, 3000)` (5 V/3 A) plus `PDO_VAR(5000, 12000, 5000)`
  (5-12 V variable), and `op-sink-microwatt = <10000000>` - but PD sink advertisement is
  not the same thing as a driver that charges the battery.

**What this means practically:** at a system draw of 8-11 W under load against an input
that may be as low as 5 W, on a 16.37 Wh battery, expect roughly **3 hours of play while
slowly draining** - not indefinite gaming. Sessions are viable; "plug in and play forever"
is not established.

The doc's remedies are correspondingly unreliable:

- Fixing the PD profile at 5 V/3 A in DTS ([line 36](../Gaming%20Mainline%20OnePlus%208.md#L36)) -
  the DTS already declares this; no evidence it's the problem.
- `echo 0 > /sys/class/power_supply/battery/charging_enabled`
  ([line 186](../Gaming%20Mainline%20OnePlus%208.md#L186)) - a **downstream** sysfs node. Mainline
  `power_supply` exposes `charge_control_limit` / `input_current_limit` instead. This command
  will almost certainly fail.

**Resolve at G3/G7 with hardware.** This is the top open risk for the handheld use case.

---

## 5. Userspace - better than expected

This is where the document holds up. My initial scepticism about Section 3 was too strong,
and is corrected here.

### 5.1 Proton 11 ARM64 - **CONFIRMED**

Real and shipping. Proton 11.0-1 Beta 3 (May 2026) ships FEX-2604; FEX 2608 landed
August 2026 as the current monthly release. The whole effort is driven by Valve's **Steam
Frame**, a Snapdragon 8 Gen 3 device running SteamOS - an Adreno a6xx-family GPU, the same
Turnip driver lineage as the Adreno 650. Valve publishes ARM64 build instructions for Proton.

The ARM64EC / thunking model the doc describes at
[line 77](../Gaming%20Mainline%20OnePlus%208.md#L77) matches how this actually works.

*Sources:* GamingOnLinux, Phoronix, ValveSoftware/Proton#7553.

### 5.2 Native ARM64 Steam client - **PARTIAL**

It exists, but it is an unannounced automated build, not the Steam Frame client. Per
Drakulix's [detailed write-up of running it on postmarketOS](https://blog.drakulix.de/taming-the-steam-arm64-client-on-pmos/):

- It is "totally oblivious to being compiled for arm64" and defaults to launching an x86_64 runtime.
- Valve does build SteamLinuxRuntime 4.0 and Proton for arm64, but the client won't fetch either.
- The Proton arm64 depot **ships without a `toolmanifest.vdf`**, so you must write one -
  which **vindicates the doc's step at [line 84](../Gaming%20Mainline%20OnePlus%208.md#L84)**.
- Making it work requires real plumbing: SteamRT4 arm64 as the client's own runtime, a
  `steam-runtime-launcher-service` on a custom bus name, and a `fexwrap` shim injecting FEX
  and graphics drivers into the pressure-vessel `bwrap` invocation.
- Grab the `steamdeck_stable` arm build rather than `publicbeta` - it carries the Deck-specific behaviour.

Achievable, but hand-rolled and fragile. This is the highest-risk gate in the plan.

### 5.3 Mesa Turnip on Adreno 650 - **CONFIRMED**

Uncontroversial. Turnip is a conformant Vulkan 1.3 driver on a6xx, and the extension set
the doc lists (`VK_EXT_graphics_pipeline_library`, `descriptor_buffer`, `custom_border_color`,
`image_drm_format_modifier`) is standard for current Mesa. The TBDR/GMEM discussion is
accurate, and GMEM on the 650 is indeed **1024 KB**.

### 5.4 `gamescope` as a pmbootstrap UI option - **WRONG**

There is no `postmarketos-ui-gamescope`. The full UI list is: buffyboard, cage, console,
cosmic, fbkeyboard, gnome, gnome-mobile, i3wm, kodi, lomiri, lxqt, mate, moonlight, niri,
openbox, os-installer, phosh, plasma-bigscreen, plasma-desktop, plasma-mobile, retroarch,
shelli, sway, sxmo (×4), weston, windowmaker, xfce4.

The doc's `pmbootstrap init` → "User Interface: gamescope" step does not exist. Gamescope
must be packaged. Nearest shipped gaming UIs are `retroarch` and `moonlight`.

There are also **no `fex`, `proton`, `steam`, or `box64` packages** anywhere in pmaports.
The entire userspace gaming stack is unpackaged work.

---

## 6. Recovered figures

Every numeric value in the source document was a base64-encoded LaTeX PNG, making the
markdown unreadable as text. All 32 were decoded and inlined by
[`tools/inline-doc-values.py`](../tools/inline-doc-values.py):

GMEM 1024 KB · Prime 2.84 GHz / 512 KB L2 · Gold 2.42 GHz / 256 KB L2 · Silver 1.80 GHz /
128 KB L2 · GPU 587→670 MHz · throttle at 70-75 °C down to 1.40 GHz / 305 MHz · Peltier
10-12 W · cooled junction 45-52 °C · system TDP 8-11 W · input latency < 2 ms.

**Benchmarks are projections, not measurements**, and they assume a 670 MHz GPU the plain
865 does not have - so they are optimistic by roughly 12% before accounting for FEX
translation overhead, which is the larger unknown. Treat the table as an upper bound.

---

## 7. Rewrite status

**Done (2026-08-24).** [`Gaming Mainline OnePlus 8.md`](../Gaming%20Mainline%20OnePlus%208.md)
has been corrected in place against every WRONG/PARTIAL/OPEN item logged above: the
device-enablement chapter now describes the Xo666/ObiKeahloa forks instead of a fictional
`pmbootstrap init instantnoodle` flow, touchscreen/panel/audio/UFS claims match the DTS,
GPU clock is corrected to 587 MHz, the charging section is rewritten around "no charger
node exists" instead of a downstream sysfs bypass, `gamescope` is removed as an install
option, the Steam ARM64 client section now covers the Drakulix fexwrap/SteamRT4 plumbing,
and the benchmark table carries an explicit "projection, not measurement" caveat.

## 8. Summary

**Alive.** The device boots mainline with working 3D - that was the one thing that could
have ended the project, and it's answered. Graphics and compatibility chapters are broadly
sound, and Valve's Steam Frame work is actively pushing exactly this stack forward.

**Rewrite required.** The device-enablement chapter is wrong in its central claim: this is
a fork of mainline maintained by one contributor, not upstream support, and the documented
install flow does not run.

**Watch.** Charging behaviour (§4) is the top unknown, and the Steam/FEX plumbing (§5.2) is
the most likely place to get stuck.
