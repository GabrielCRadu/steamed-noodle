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

The port lives in at least **three** out-of-tree trees, and they do not agree with each other:

- [`github.com/Xo666/mainline-instantnoodle`](https://github.com/Xo666/mainline-instantnoodle) - branch `6.16.7`, pushed 2026-01-14, single branch. **This is the tree audited as `reference/dts/sm8250-oneplus-instantnoodle.dts`.** Authored by `Xiaoou <xo666@postmarketos.org>`.
- [`gitlab.com/ObiKeahloa/linux`](https://gitlab.com/ObiKeahloa/linux/-/tree/sm8250/v6.13-instantnoodle) - branch `sm8250/v6.13-instantnoodle`, single relevant branch on that account. **Not independently audited** - no DTS pulled from this tree yet, only its existence confirmed.
- [`gitlab.postmarketos.org/WuerfelDev/linux-sm8250`](https://gitlab.postmarketos.org/WuerfelDev/linux-sm8250/-/tree/6.17.0-instantnoodle) - branch `6.17.0-instantnoodle`, the account's **default branch**, last commit 2025-12-11. **This is the tree the wiki Infobox's `pmoskernel = 6.17.0` actually points to** - not either of the two forks originally treated as "the" sources in this log. Pulled and saved as `reference/dts/sm8250-oneplus-instantnoodle-wuerfeldev.dts`.

**This is the project's foundation, and it's fragmented.** No single tree currently has
everything working - see the divergence table below. Whoever builds this has to pick a tree
knowing what they're trading away, not assume "the mainline fork" is one coherent thing.

#### Fork divergence: what actually works, by tree

Directly diffed `reference/dts/sm8250-oneplus-instantnoodle.dts` (Xo666, `6.16.7`) against
`reference/dts/sm8250-oneplus-instantnoodle-wuerfeldev.dts` (WuerfelDev, `6.17.0-instantnoodle`,
pulled 2026-08-24) node by node. ObiKeahloa's tree is not included below - not yet audited.

| Feature | Xo666 `6.16.7` | WuerfelDev `6.17.0-instantnoodle` (wiki's tracked kernel) |
|---|---|---|
| **GPU (`&gpu`)** | `status = "okay"`, zap-shader node configured | **`status = "disabled"`, unconditionally, at the top of the file** |
| **Charger (`&pm8150b_charger`)** | Node does not exist | `status = "okay"`, wired to ADC channels; `&pm8150b_fg` (PMIC-integrated fuel gauge) also `"okay"` |
| **USB-C SBU mux / orientation-switch** | `status` unset (defaults **okay**); has both `mode-switch` and `orientation-switch`; endpoint wired to `pm8150b_typec_sbu_out` | `status = "disabled"`, comment reads "Currently unconfigured"; endpoint is an empty stub |
| **Fuel gauge chip** | External `ti,bq27411` @ i2c16 addr 0x55, bus `status = "okay"` | External `ti,bq27541` @ i2c16 addr 0x55 present but bus `status = "disabled"` (vestigial) - real gauge is `&pm8150b_fg` instead |
| **Panel `compatible` string** | `samsung,amb655uv01` | `oneplus,instantnoodle-panel` (different string, likely a later wrapper/rename - not confirmed to be a different physical driver path) |
| **Touchscreen, NFC, flash LED** | All present, matches §2 below | Same nodes present (`samsung,s6sy761`, `nxp,nxp-nci-i2c`, `pm8150l_flash`) |

**The practical read: as of 2026-08-24, no tree has GPU, charging, and clean USB-C orientation
switching all at once.** Xo666 gives you graphics (existential for a gaming project) and a
correctly-wired SBU mux, but zero charging support. WuerfelDev - the tree the wiki's own status
badges (`status_3d = Y`, charger `feature-yes`) implicitly describe as "this device" - currently
ships with **the GPU explicitly disabled in DTS**, which contradicts `status_3d = Y` outright.
That could be a temporary WIP state (mid-bisect, debugging something unrelated) rather than a
permanent regression, but it means the wiki's per-feature summary cannot be read as "true of one
tree simultaneously" - it's more likely an aggregate across forks, possibly not even fully
current. **For a gaming handheld, Xo666 is the only verified-working starting point for GPU**,
full stop; treat WuerfelDev as a source to cherry-pick the charger/fuel-gauge nodes from, not as
a drop-in replacement.

#### A fourth resource: prebuilt firmware + ALSA package

[`github.com/Xo666/linux-oneplus-instantnoodle`](https://github.com/Xo666/linux-oneplus-instantnoodle)
(same author, separate repo, pushed 2026-01-20) is **not a kernel tree** despite its README
saying "Mainline Kernel, Firmware package, ALSA configs" - it contains only
`firmware-oneplus-instantnoodle/usr/lib/firmware/` and `alsa-oneplus-instantnoodle/usr/lib/`.
The firmware directory actually contains the proprietary signed blobs this log's §3 says must
be extracted from an OxygenOS dump: `a650_zap.mbn`, `adsp.mbn`, `cdsp.mbn`, `slpi.mbn`,
`venus.mbn`, plus the open `a650_gmu.bin`/`a650_sqe.fw`.

Two things worth flagging before using it:

- **Path mismatch.** The repo nests the OnePlus blobs under `qcom/sm8250/OnePlus8/`, but the
  DTS's `firmware-name` properties (confirmed by grepping `reference/dts/`) expect
  `qcom/sm8250/OnePlus/adsp.mbn` etc. - no digit. Copy or symlink `OnePlus8/` to `OnePlus/`, or
  the firmware loader won't find any of it.
- **Provenance.** These are OnePlus/Qualcomm-signed proprietary blobs, redistributed on a public
  GitHub repo with no stated license for that content. Convenient - skips extracting them from
  an OxygenOS image yourself - but treat the legal status as unresolved, same as any other
  redistributed proprietary firmware mirror.

*Source:* postmarketOS wiki (MediaWiki API and full page source supplied by the user);
GitHub API (`gh api`); GitLab API (`gitlab.com` and `gitlab.postmarketos.org`, both via `curl`);
direct diff of both DTS files now checked into `reference/dts/`.

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
| Adreno 650 works via Turnip/`msm` | `&gpu status = "okay"` **on the Xo666 tree only**, needs `a650_zap.mbn`. Disabled outright on the wiki's own tracked tree - see §1.4 fork divergence table | **CONFIRMED, tree-dependent** |
| GPU boosts to 670 MHz | 670 MHz is the Snapdragon **865+** clock. Plain 865 tops at 587 MHz | **WRONG** |
| `pm8150b-charger` manages charging | Absent from Xo666 (audited here); present and `okay` on WuerfelDev's tree - the two trees trade this against GPU. See §1.4 | **PARTIAL, tree-dependent** |
| USB-C SuperSpeed orientation quirk | `fcs,fsa4480` SBU mux present; orientation behaviour untested | **OPEN** |

### Update 2026-08-24 (later): full wiki Infobox/feature table obtained

The user supplied the complete `oneplus-instantnoodle` wiki page source (Infobox + feature
tables), not just the summary previously scraped via the MediaWiki API. This resolves one open
question and adds hardware the DTS audit above didn't surface:

- **Charging is explicitly `feature-yes` on the wiki**: "Charger | `qcom,pm8150b-charger` |
  Allows charging at 5W". Fast charging is separately listed and marked `feature-no`:
  "`oplus,stm8s-fastcg` | Enables 5V6A/Warp Charging, currently no driver exists". So base
  charging at 5 W is a confirmed, working feature - not the fully open question §4 originally
  treated it as. Only Warp/fast charging is confirmed absent.
- **This does not contradict the DTS finding above so much as date it.** The wiki's Infobox
  declares `pmoskernel = 6.17.0`, which points at a different, newer kernel tree
  (`gitlab.postmarketos.org/WuerfelDev/linux-sm8250`, tag `6.17.0-instantnoodle`) than the
  `reference/dts/` snapshot audited in this repo (Xo666 fork, branch `6.16.7`). The charger
  node most likely landed between those two trees. Treat `reference/dts/sm8250-oneplus-instantnoodle.dts`
  as one version behind the currently wiki-tracked kernel on this specific point.
- **NFC confirmed working**: `nxp,nxp-nci-i2c` @ 0x28 on i2c1 - **absent from the document
  and from this log entirely until now.**
- **Flash LED confirmed working**: `qcom,spmi-flash-led`, wired through the `pm8150l` PMIC's
  SPMI bus - also previously unmentioned.
- **Audio bus addresses pinned down**: both `nxp,tfa9874` amps sit on i2c15, earpiece at
  0x34 and main speaker at 0x35 - consistent with, and more precise than, the DTS audit above.
- **SBU mux (`fcs,fsa4480`) address given**: 0x42 on i2c15 (the DTS audit only confirmed its
  presence, not its address).
- Full feature matrix from the wiki, for completeness: screen, battery, front camera, GPU,
  WiFi, Bluetooth, USB OTG all **Y**; rear camera **P** (marked partial on the wiki, though the
  DTS audit above found the node absent entirely - treat as effectively non-functional);
  modem, sensors (`slpi` loads unconfigured), haptics all **N**, matching the "known-broken"
  list below.

**Correction to the bullet above (2026-08-24, still later that day):** "not the fully open
question §4 originally treated it as" undersold what pulling the actual WuerfelDev tree turned
up. That same tree, at its current HEAD, has **`&gpu { status = "disabled"; }`** - unconditionally.
The wiki's `status_3d = Y` and this tree's own DTS disagree with each other. Charging at 5 W is
real on *a* tree; that tree does not currently give you a working GPU. See the fork-divergence
table in §1.4 - this is the actual state of play, not the charging-only framing above.

### Additional hardware the doc never mentions

- **`&mdss_dp { status = "okay" }`** - DisplayPort alt-mode over USB-C is enabled. Relevant
  to a docked handheld setup and absent from the document entirely.
- **`&pm8150b_vbus`**, 500 mA-3 A source regulator - the phone can power USB accessories (OTG out).
- **Battery**: `simple-battery`, 16.37 Wh design energy, 4270 mAh, 3.4-4.435 V.
- **Fuel gauge**: `ti,bq27411` - accurate charge reporting.
- **Front camera only** confirmed functional (`sony,imx471`). Rear `imx586` is absent from
  the audited DTS and marked only partial on the wiki.
- **NFC**: `nxp,nxp-nci-i2c` @ 0x28 on i2c1.
- **Flash LED**: `qcom,spmi-flash-led` via the pm8150l PMIC.

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

## 4. Power and thermals - narrowed, but now entangled with GPU

> **Read §1.4 before this section.** The "confirmed 5 W charging" finding below comes from the
> WuerfelDev `6.17.0-instantnoodle` tree, which currently ships with **the GPU disabled in DTS**.
> The Xo666 tree this whole document otherwise relies on for graphics has the opposite problem:
> working GPU, zero charger node. As of 2026-08-24 you cannot get both from one unmodified tree.
> The numbers below describe the charging-capable tree's power budget, not the build this
> document otherwise recommends.

The document's thermal architecture rests on passthrough power: the GameSir X3 Pro's
Peltier cooler keeps the SoC at 45-52 °C, so the CPU never throttles, and the phone charges
through the controller meanwhile. The cooling half of that is sound - the Peltier draws
10-12 W **from the wall charger, not from the phone**, so active cooling works regardless
of what the phone's charging stack does.

The charging half was flagged OPEN in the first pass of this log, because the wiki's summary
claimed 5 W charging while the Xo666 DTS audited in `reference/dts/` declared no charger node
at all. **The full wiki feature table (obtained later, §2) resolves this**: base charging via
`qcom,pm8150b-charger` is listed as a confirmed, working feature at **5 W**. Only Warp/fast
charging (`oplus,stm8s-fastcg`, 5V/6A) is confirmed absent - "currently no driver exists," per
the wiki itself. The likely explanation for the DTS discrepancy: the wiki's Infobox declares
`pmoskernel = 6.17.0`, a newer kernel snapshot than the `6.16.7` Xo666 branch this repo
audited; the charger node most likely landed in that gap. `pm8150b_typec` (present in the
audited DTS) also declares sink PDOs of `PDO_FIXED(5000, 3000)` (5 V/3 A) plus
`PDO_VAR(5000, 12000, 5000)` (5-12 V variable) and `op-sink-microwatt = <10000000>`.

**What this means practically:** at a system draw of 8-11 W under load against a confirmed
5 W input, net deficit is 3-6 W. On a 16.37 Wh battery that's roughly **2.7-5.5 hours of play
while slowly draining** - narrower and more grounded than the original "maybe it doesn't charge
at all" framing, but still not indefinite. "Plug in and play forever" remains unestablished;
"plug in and roughly double your unplugged session length" is now the reasonable claim.

The doc's remedies are correspondingly unreliable:

- Fixing the PD profile at 5 V/3 A in DTS ([line 36](../Gaming%20Mainline%20OnePlus%208.md#L36)) -
  the DTS already declares this; no evidence it's the problem.
- `echo 0 > /sys/class/power_supply/battery/charging_enabled`
  ([line 186](../Gaming%20Mainline%20OnePlus%208.md#L186)) - a **downstream** sysfs node. Mainline
  `power_supply` exposes `charge_control_limit` / `input_current_limit` instead. This command
  will almost certainly fail.

**Still resolve at G3/G7 with hardware** - the 5 W figure and the 3-6 W deficit math are both
still projections, not measurements, taken from a tree (WuerfelDev) that does not currently boot
this device's GPU. The actual top risk is no longer "does charging work" but **"can the
charger node from WuerfelDev be ported onto the Xo666 tree without breaking the GPU or the SBU
mux"** - a merge/patch job nobody has done yet, as far as this log can tell. The Steam ARM64
client plumbing (§5.2) is the next-biggest source of uncertainty after that.

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

**Done (2026-08-24), first pass.** [`Gaming Mainline OnePlus 8.md`](../Gaming%20Mainline%20OnePlus%208.md)
was corrected against every WRONG/PARTIAL/OPEN item logged at that point: the
device-enablement chapter now describes the Xo666/ObiKeahloa forks instead of a fictional
`pmbootstrap init instantnoodle` flow, touchscreen/panel/audio/UFS claims match the DTS,
GPU clock is corrected to 587 MHz, `gamescope` is removed as an install option, the Steam
ARM64 client section covers the Drakulix fexwrap/SteamRT4 plumbing, and the benchmark table
carries an explicit "projection, not measurement" caveat.

**Done (2026-08-24), second pass.** The doc's power/charging section, risk table entry, and
conclusion were updated to the "5 W confirmed, Warp absent" framing, plus NFC and flash LED
were added to the hardware table.

**Follow-up needed (2026-08-24, third pass - current).** Pulling the actual WuerfelDev tree
(rather than trusting the wiki's feature table as description of one coherent kernel) found
that tree ships with **`&gpu` disabled** - so the second pass's charging framing, while
individually accurate, reads as better news than the project's real state supports. The doc
needs a further edit: charging and GPU are not simultaneously available from any known
unmodified tree (§1.4), and that fork-divergence problem - not charging, not Steam ARM64 -
is now the most fundamental open risk. This is a correction to the *previous* correction, not
a reversal of it: 5 W charging is still real, it's just real on a tree without graphics.

## 8. Summary

**Alive, on the Xo666 tree specifically.** The device boots mainline with working 3D on at
least one tree - that was the one thing that could have ended the project, and it's answered,
but not universally: the wiki's own tracked kernel (WuerfelDev) currently ships with the GPU
disabled. Graphics and compatibility chapters are broadly sound for whoever uses Xo666, and
Valve's Steam Frame work is actively pushing exactly this stack forward.

**Rewrite required.** The device-enablement chapter is wrong in its central claim: this is
a fork of mainline maintained by one contributor, not upstream support, and the documented
install flow does not run. *(Addressed - see §7.)*

**Watch.** The project's real bottleneck is **fork fragmentation**: no single tree currently
has GPU, charging, and clean USB-C orientation switching all working at once (§1.4). Someone
has to either accept Xo666's "graphics but no charger" tradeoff, or do the work of porting
WuerfelDev's charger/fuel-gauge nodes onto Xo666's tree - nobody has done that yet, as far as
this log can tell. The Steam/FEX plumbing (§5.2) is the next-biggest source of uncertainty
after that.
