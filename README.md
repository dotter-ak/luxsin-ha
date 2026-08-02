# Luxsin X8/X9 Amplifier — Home Assistant integration
**Custom Home Assistant integration for the Luxsin X8 and X9 amplifiers, based on API, provided by the manufacturer.**

## What it creates

A single Home Assistant device with several entities:

**`media_player`**
- **volume_level** — scaled from the device's native 0-200 range
- **source** — input selection
- **sound_mode** — output selection: XLR / RCA / Headphone / XLR + RCA
- **media_title / media_artist**, **play/pause/next/prev** — shown only
  while the active source is Bluetooth (fields `bt_title`/`bt_artist`/
  `bt_status`; actions `bt_play`/`bt_next`)
- **turn_off** — powers the device off. There is no way to power it back on remotely - once off, the device (and its Wi-Fi) is unreachable
- **raw_status** (attribute) — the full decoded JSON status, kept around
  for fields not yet mapped to a dedicated entity

**`sensor`**
- **Audio Format** — currently detected signal format (e.g. "PCM 44.1 kHz")

**`light`**
- **LED Light** — on/off + RGB color of the ambient LED (only for X8)

**`number`**
- **Balance** — L/R balance, **-15.0..+15.0 dB**
- **Screen Brightness** — LCD brightness, **0..2**

**`switch`**
- **DSP Bypass** — ON means DSP processing is skipped
- **PEQ** — master on/off for parametric EQ processing (separate from
  **PEQ Profile**, which picks which saved preset is active)

**`select`**
- **Input** / **Output** — standalone alternatives to media_player's
  source/sound_mode, for dashboards and automations that don't otherwise
  use the media_player domain; both write through the same coordinator
  methods, so state stays in sync with media_player
- **VU Meter Style** — choose between 16 built-in VU display styles
- **PEQ Profile** — choose a saved PEQ preset

## Installation

### HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=dotter-ak&repository=luxsin-ha)

Or manually:

1. Open **HACS** → **Integrations**.
2. Click the three-dot menu → **Custom repositories**.
3. Add `https://github.com/dotter-ak/luxsin-ha` as an **Integration**.
4. Search for **Luxsin** and install.
5. Restart Home Assistant.

### Manual

1. Download the [latest release](https://github.com/dotter-ak/luxsin-ha/releases/latest).
2. Copy `custom_components/luxsin-ha` into your Home Assistant `custom_components` directory.
3. **Restart Home Assistant**.

## Changelog
- v 0.1.0 - Initial Release

## Support

If this integration is useful to you, you're welcome to say thanks with a small donation:

[![Monobank](https://img.shields.io/badge/Donate-Monobank-black?style=flat-square)](https://send.monobank.ua/jar/8ff8Xbyw9p)

##
>
>This project is not
> affiliated with, endorsed by, or supported by Luxsin Audio, and comes
> with no warranty.
>
> "Luxsin" and the Luxsin logo
> are trademarks of their respective owner, used here only to identify
> the hardware this integration controls.

## License

[MIT](LICENSE).
