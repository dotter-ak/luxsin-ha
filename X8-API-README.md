# Luxsin-X8-API

Luxsin X8 Web API notes, derived from the current `luxsin_x8` firmware source.

> Warning: These endpoints change live device settings. Keep values inside the
> ranges used by the product UI. Out-of-range values are not consistently
> validated by the firmware.

## Overview

- Protocol: HTTP
- Base URL: `http://<device-ip>/`
- Authentication: none.
- CORS: responses add `Access-Control-Allow-Origin: *`.
- Encoded responses: `sync`, `syncData`, and `syncPeq` return gzip-compressed custom-Base64 text. Browsers transparently decompress gzip when using `fetch()`, then the remaining response text must be custom-Base64 decoded.

## Custom Base64 Alphabet

Translate from the custom alphabet to the standard Base64 alphabet, then decode
with a normal Base64 decoder.


| Alphabet | Value                                                              |
| -------- | ------------------------------------------------------------------ |
| Custom   | `KLMPQRSTUVWXYZABCGHdefIJjkNOlmnopqrstuvwxyzabcghiDEF34501289+67/` |
| Standard | `ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/` |

For outbound POST control messages, encode UTF-8 JSON with standard Base64,
translate standard characters to the custom alphabet, then submit it as a form
field value, for example `json=<CUSTOM_BASE64>`.

## Endpoints

### Get full status with PEQ

`GET /dev/info.cgi?action=sync`

Returns encoded JSON with common status fields plus `peq`.

### Get common status/config

`GET /dev/info.cgi?action=syncData`

Despite the name, the X8 firmware maps `syncData` to `syncConfig()`: it returns
the common status/config fields without `peq`.

### Get PEQ only

`GET /dev/info.cgi?action=syncPeq`

Returns encoded JSON:


| Field       | Description                                                                                                                                                                                       |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `peqSelect` | Current PEQ preset index.                                                                                                                                                                         |
| `peqEnable` | PEQ enable flag.                                                                                                                                                                                  |
| `peq`       | PEQ preset array. Each item has`name`, `preamp`, `canDel`, `autoPre`, `filters`, and optional `brand`, `model`, `form`, `target`. `filters` is a JSON string in saved config, not a nested array. |
| `msgCount`  | State-change counter.                                                                                                                                                                             |

### Get device ID

`GET /dev/info.cgi?action=getId`

Returns plain JSON, not custom-Base64:

```json
{"mac":"AA:BB:CC:DD:EE:FF"}
```

### Update setting

`GET /dev/info.cgi?action=setting&<PARAM>=<VALUE>`

Multiple parameters can be combined in one request. A successful response is the
plain HTML text `Settings updated`.

### Poll change counter

`GET /msgCount`

Returns a plain integer. The firmware increments this counter when `sendData()`
is called after state changes. Poll this cheaply, then call `syncData` or `sync`
only when the value changes.

### Force increment change counter

`GET /msgAdd`

Increments `msgCount`. This appears to be a debug/helper endpoint.

### Device web entry

`GET /` or `GET /luxsin.com`

Redirects to:

`http://am.luxsinaudio.com/x8/v2/i.html?ip=<device-ip>`

### Static public files

`GET /public/<filename>`

Serves files from the public drive root.

## Common Status Fields

These fields are returned by `sync` and `syncData`. `sync` also includes `peq`.


| Field                     | Description                                                               |
| ------------------------- | ------------------------------------------------------------------------- |
| `device`                  | Device model, normally`Luxsin-X8`.                                        |
| `version`                 | Numeric firmware version from`getLuxsinVersion()`.                        |
| `mac`                     | Wi-Fi MAC address. Present on non-WIN32 builds.                           |
| `language`                | UI language:`0` English, `1` Traditional Chinese, `2` Simplified Chinese. |
| `volume`                  | DAC volume,`0..200`.                                                      |
| `soundStep`               | Volume step setting.                                                      |
| `input`                   | Input source index. See values below.                                     |
| `output`                  | Output index. If headphone detect is active, firmware reports`2`.         |
| `audioFormat`             | Current audio format string, for example PCM/DSD sample info.             |
| `msgCount`                | State-change counter.                                                     |
| `screenLight`             | Screen brightness setting.                                                |
| `screenOff`               | Screen-off mode.                                                          |
| `autoHome`                | Auto-return-home mode.                                                    |
| `sleep`                   | Standby/sleep timer mode.                                                 |
| `vu`                      | VU display style index.                                                   |
| `vu_count`                | VU style count. X8 source defines`16`.                                    |
| `vuSensor`                | VU sensor mode.                                                           |
| `buttonLight`             | Button light brightness/mode.                                             |
| `knob_breathlight`        | Knob breathing light mode.                                                |
| `pcm`                     | PCM filter setting.                                                       |
| `dreMode`                 | DAC DRE mode.                                                             |
| `dacGain`                 | Headphone gain setting.                                                   |
| `balance`                 | Left/right balance setting.                                               |
| `xlr`                     | XLR polarity.                                                             |
| `dacVolumeDirect`         | DAC volume-direct mode.                                                   |
| `dacImpedance`            | DAC impedance setting.                                                    |
| `hdmimutepolar`           | HDMI mute polarity.                                                       |
| `hdmiType`                | HDMI type; firmware also derives`hdmiSwapMute = hdmiType % 2`.            |
| `uac_ver`                 | USB audio class/version mode.                                             |
| `dsp_enable`              | DSP enable flag.                                                          |
| `audio_enable`            | DSP audio-processing enable flag.                                         |
| `peqEnable`               | PEQ enable flag.                                                          |
| `peqSelect`               | PEQ preset index.                                                         |
| `effect_enable`           | Effect enable flag.                                                       |
| `effect_value`            | Effect value/index.                                                       |
| `width_enable`            | Soundstage width enable flag.                                             |
| `width_value`             | Soundstage width value.                                                   |
| `scene_enable`            | Scene mode enable flag.                                                   |
| `scene_value`             | Scene mode value.                                                         |
| `crossfeed_enable`        | Crossfeed enable flag.                                                    |
| `crossfeed_value`         | Crossfeed preset value.                                                   |
| `color_enable`            | Tone/color enable flag.                                                   |
| `color_bass_gain`         | Bass color gain, stored as integer tenths.                                |
| `color_mid_gain`          | Mid color gain, stored as integer tenths.                                 |
| `color_treble_gain`       | Treble color gain, stored as integer tenths.                              |
| `loudness_enable`         | Loudness enable flag.                                                     |
| `loudness_bass_gain`      | Loudness bass gain.                                                       |
| `loudness_treble_gain`    | Loudness treble gain.                                                     |
| `loudness_threshold_gain` | Loudness threshold gain.                                                  |
| `led_enable`              | Ambient/motor LED enable flag.                                            |
| `led_red`                 | LED red channel.                                                          |
| `led_green`               | LED green channel.                                                        |
| `led_blue`                | LED blue channel.                                                         |
| `bt_status`               | Bluetooth status. Present on non-WIN32 builds.                            |
| `bt_srcname`              | Connected Bluetooth device name. Present on non-WIN32 builds.             |
| `bt_title`                | Bluetooth track title. Present on non-WIN32 builds.                       |
| `bt_artist`               | Bluetooth track artist. Present on non-WIN32 builds.                      |

## Enumerations

### Input source


| Value | Name      |
| ----- | --------- |
| `0`   | USB       |
| `1`   | USB-C     |
| `2`   | Coaxial   |
| `3`   | Optical   |
| `4`   | Bluetooth |
| `5`   | IIS       |

The source defines `INPUT_COUNT` as `6`, but the enum contains values `0..7`.
Use only values exposed by the product UI for the target firmware build.

### Output


| Value | Name      |
| ----- | --------- |
| `0`   | XLR       |
| `1`   | RCA       |
| `2`   | Headphone |
| `3`   | XLR + RCA |

### PEQ filter type

For JSON that uses numeric filter types, the firmware enum is:


| Value | Type         |
| ----- | ------------ |
| `0`   | `LOW_PASS`   |
| `1`   | `HIGH_PASS`  |
| `2`   | `BAND_PASS`  |
| `3`   | `NOTCH`      |
| `4`   | `PEAKING`    |
| `5`   | `LOW_SHELF`  |
| `6`   | `HIGH_SHELF` |
| `7`   | `ALL_PASS`   |
| `8`   | `LPF_1ST`    |
| `9`   | `HPF_1ST`    |
| `10`  | `BYPASS`     |

Saved PEQ config uses string names such as `PEAKING` and `LOW_SHELF`.

## Writable GET Parameters

All parameters below are handled by:

`GET /dev/info.cgi?action=setting&<param>=<value>`


| Parameter                 | Value range        | Effect                                                         |
| ------------------------- | ------------------ | -------------------------------------------------------------- |
| `volume`                  | `0..200`           | Set DAC volume.                                                |
| `input`                   | `0..7`             | Set input source.                                              |
| `output`                  | `0..3`             | Set output.                                                    |
| `bt_next`                 | `1, 0`             | Bluetooth transport control:`1` next, `0` previous.            |
| `bt_play`                 | `1`                | Bluetooth play/pause toggle.                                   |
| `language`                | `0..2`             | Set UI language. Firmware clamps to max`2`.                    |
| `screenLight`             | `0..2`             | Set LCD brightness.                                            |
| `vu`                      | `0..15`            | Set VU display style.                                          |
| `sleep`                   | `0..4`             | Set standby/sleep mode.                                        |
| `screenOff`               | `0..4`             | Set screen-off mode.                                           |
| `buttonLight`             | `0..3`             | Set button light mode.                                         |
| `buttonShort`             | `0..2`             | Set short-press function, inferred from power-key options.     |
| `pcm`                     | `0..5`             | Set PCM DAC filter.                                            |
| `dreMode`                 | `0..1`             | Set DAC DRE mode.                                              |
| `dacGain`                 | `0..3`             | Set headphone gain.                                            |
| `xlr`                     | `0..1`             | Set XLR polarity.                                              |
| `soundStep`               | `0..3`             | Set volume step.                                               |
| `bootSound`               | `0..10`            | Set boot volume mode.                                          |
| `balance`                 | `-150..150`        | Set balance and reapply volume; displayed as`-15.0..+15.0 dB`. |
| `autoHome`                | `0..3`             | Set auto-home mode.                                            |
| `knob_breathlight`        | `0..1`             | Set knob breathing light.                                      |
| `dacVolumeDirect`         | `0..2`             | Set volume-direct mode.                                        |
| `dacImpedance`            | `0..1`             | Set impedance mode.                                            |
| `vuSensor`                | `-40..40`          | Set VU sensor offset; displayed as`-20.0..+20.0 dB`.           |
| `hdmimutepolar`           | `0..1`             | Set HDMI mute polarity and refresh HDMI mute state.            |
| `hdmiType`                | `0..7`             | Set HDMI/IIS type.                                             |
| `power`                   | any value          | Power off.                                                     |
| `led_enable`              | `0..1`             | Enable ambient LED.                                            |
| `led_red`                 | `0..255` expected  | Set LED red channel.                                           |
| `led_green`               | `0..255` expected  | Set LED green channel.                                         |
| `led_blue`                | `0..255` expected  | Set LED blue channel.                                          |
| `uac_ver`                 | `0..1`             | Set USB audio class/version mode:`0` UAC 2.0, `1` UAC 1.0.     |
| `dsp_enable`              | `0..1`             | Queue remote DSP enable/disable.                               |
| `audio_enable`            | `0..1`             | Enable/disable DSP audio processing path.                      |
| `crossfeed_value`         | `0..2`             | Set crossfeed preset;                                          |
| `crossfeed_enable`        | `0..1`             | Enable crossfeed.                                              |
| `effect_value`            | `0..15`            | Set effect value.                                              |
| `effect_enable`           | `0..1`             | Enable effect.                                                 |
| `width_enable`            | `0..1`             | Enable soundstage width.                                       |
| `width_value`             | `0..100`           | Set width; firmware sends`0.02 * value` to DSP.                |
| `color_enable`            | `0..1`             | Enable tone/color EQ.                                          |
| `color_bass_gain`         | `-100..100`        | Set bass color gain; displayed as`-10.0..+10.0 dB`.            |
| `color_mid_gain`          | `-100..100`        | Set mid color gain; displayed as`-10.0..+10.0 dB`.             |
| `color_treble_gain`       | `-100..100`        | Set treble color gain; displayed as`-10.0..+10.0 dB`.          |
| `loudness_enable`         | `0..1`             | Enable loudness.                                               |
| `loudness_bass_gain`      | `0..100`           | Set loudness bass gain; displayed as`0.0..10.0 dB`.            |
| `loudness_threshold_gain` | `-40..0`           | Set loudness threshold.                                        |
| `loudness_treble_gain`    | `0..100`           | Set loudness treble gain; displayed as`0.0..10.0 dB`.          |
| `peqSelect`               | `0..(peq_count-1)` | Select PEQ preset.                                             |
| `peqEnable`               | `0..1`             | Queue remote PEQ enable/disable.                               |

## PEQ POST Control

`POST /dev/info.cgi`

The X8 source collects POST form data, decodes the field value as custom-Base64,
and passes the decoded JSON to `OnReceiveControlMsg(decoded)`. The form field
name is not checked by this source, but `json=<CUSTOM_BASE64>` is the clearest
client convention.

The handler implementation is not present in this project folder, so treat these
shapes as firmware-dependent and verify on a device build before exposing
destructive controls.

Known PEQ node shape from the local PEQ code:

```json
{
  "peqChange": {
    "name": "Custom preset",
    "brand": "Optional brand",
    "model": "Optional model",
    "form": "Optional form",
    "target": "Optional target",
    "preamp": -3.0,
    "canDel": 1,
    "autoPre": 0,
    "filters": [
      {"type": 4, "fc": 80, "gain": 0, "q": 0.7},
      {"type": 4, "fc": 150, "gain": 0, "q": 0.7}
    ]
  }
}
```

The saved `peq` array returned by `sync`/`syncPeq` uses string filter type names
inside a JSON string:

```json
{
  "name": "none",
  "preamp": 0,
  "canDel": 0,
  "autoPre": 0,
  "filters": "[{\"type\":\"PEAKING\",\"fc\":80,\"gain\":0,\"q\":0.1}]"
}
```

## Examples

Get common status:

```bash
curl "http://<device-ip>/dev/info.cgi?action=syncData" --compressed
```

Set volume and input:

```bash
curl "http://<device-ip>/dev/info.cgi?action=setting&volume=120&input=4"
```

Poll changes:

```bash
curl "http://<device-ip>/msgCount"
```

See `sample.html` for a browser example with decode/encode helpers.
