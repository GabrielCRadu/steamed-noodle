# steamed-noodle

Research and build notes for turning a OnePlus 8 (codename `instantnoodle`, Qualcomm
SM8250) into a dedicated Linux gaming handheld, running a mainline-adjacent kernel instead
of Android.

## How this is built

This project is developed with AI assistance, using models including Claude Sonnet 5 and
Claude Opus 5, doing the research, source verification, packaging, and build work
alongside the author. Every non-obvious claim in `docs/verification-log.md` is traced to a
primary source (a real file, a real build, a real API response) specifically so the work
can be checked rather than taken on faith - that's the point of that file existing at all.
If you think AI involvement automatically makes a project worthless, this isn't the repo
for you; no need to spend your time on it.

## Status

Nothing has been flashed to real hardware yet. Everything below has been verified as far
as it can be without the phone in hand: the kernel source compiles, the full device
package set builds through the real postmarketOS packaging pipeline, and a bootable
image has been assembled. None of that proves the phone actually boots it. A pre-flight
review turned up real gaps in the flashing procedure itself (verified boot handling,
no backup step before overwriting the rootfs partition) that still need resolving before
anyone flashes anything - see `docs/verification-log.md` for what is tracked there.

## Why this exists

Mainline Linux support for this exact phone does not exist upstream, and is not
officially packaged in postmarketOS. It only exists as unofficial, mutually incompatible
community kernel forks. This repo tracks what was actually checked against those forks
and the real toolchain, as opposed to a first-draft research document whose numeric
claims turned out to only be partially correct.

## Repo layout

- `Gaming Mainline OnePlus 8.md` - the main architecture and how-to document (in
  Romanian). Covers the kernel/device tree situation, the Vulkan/Mesa graphics stack,
  Proton/FEX for running Windows games, power and thermal behavior, and the install flow.
- `docs/verification-log.md` - the actual audit trail. Every claim in the main document,
  checked against pmaports, the kernel forks, and a real build, with sources. This is
  the file to read if you want to know what is actually confirmed versus assumed.
- `reference/dts/` - the three known community device trees for this phone (from three
  different forks), pulled for direct comparison. They disagree with each other on
  several points, including which one has a working GPU versus a working battery
  charger.
- `pmaports/` - draft postmarketOS packages (kernel, device port, firmware, ALSA config)
  for this phone. Not part of upstream pmaports. Built and verified locally through the
  real `abuild`/`pmbootstrap` pipeline.
- `tools/inline-doc-values.py` - a one-off script used to recover numeric values that had
  been embedded as images in the original source document.
- `CLAUDE.md` - writing-style rules used while working on this repo with an AI assistant.

## Key finding so far

No single kernel fork currently has a working GPU, a working battery charger, and clean
USB-C orientation switching all at the same time. Picking a fork means picking which of
those to give up, unless someone does the work of porting the missing pieces across.
Details and sources are in `docs/verification-log.md`.

## Target device

OnePlus 8, global variant (IN2013/IN2010), codename `instantnoodle`. Android is wiped
entirely. No modem, calls, or SMS.

## License and attribution

This repo's own content (the documents, the verification log, `tools/inline-doc-values.py`,
and the drafted `pmaports/` packaging files, which follow the same MIT convention the real
postmarketOS pmaports project uses for packaging metadata) is MIT licensed - see `LICENSE`.

The three files under `reference/dts/` are not original to this repo. They are device tree
source files pulled verbatim from three independent community kernel forks for this phone,
kept here for side-by-side comparison:

- `sm8250-oneplus-instantnoodle.dts` - from
  [Xo666/mainline-instantnoodle](https://github.com/Xo666/mainline-instantnoodle) (Xiaoou),
  licensed `GPL-2.0 OR BSD-3-Clause`.
- `sm8250-oneplus-instantnoodle-obikeahloa.dts` - from
  [ObiKeahloa/linux](https://gitlab.com/ObiKeahloa/linux), licensed
  `GPL-2.0-only OR BSD-2-Clause`.
- `sm8250-oneplus-instantnoodle-wuerfeldev.dts` - from
  [WuerfelDev/linux-sm8250](https://gitlab.postmarketos.org/WuerfelDev/linux-sm8250),
  licensed `GPL-2.0-only OR BSD-2-Clause`.

Each file carries its own SPDX header and copyright notice; those are not altered here. All
three are dual-licensed with a permissive option, which is why the repo as a whole can stay
MIT rather than being pulled entirely under GPL by their presence - but the credit for
writing them belongs to their respective authors and forks, not to this project.

The firmware referenced (but not included - see `.gitignore`) by
`pmaports/firmware-oneplus-instantnoodle/` is proprietary Qualcomm/OnePlus-signed material
with no clear redistribution license; see `docs/verification-log.md` for the caveat.
