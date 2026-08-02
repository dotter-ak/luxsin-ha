# Luxsin-X9-API

Luxsin X9 Web API notes, derived from the current `luxsin_x9` firmware source.

> Warning: These endpoints change live device settings. Keep values inside the
> ranges used by the product UI. Out-of-range values are not consistently
> validated by the firmware.

## Overview

- Protocol: HTTP
- Base URL: `http://<device-ip>/`
- Authentication: none.
- CORS: responses add `Access-Control-Allow-Origin: *`.
- Encoded responses: `sync`, `syncData`, and `syncPeq` return gzip-compressed
  custom-Base64 text. Browsers transparently decompress gzip when using
  `fetch()`, then the remaining response text must be custom-Base64 decoded.

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

Returns encoded JSON with common status fields without `peq`.

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

Multiple parameters can be combined in one request. A successful response is:

```html
<html><body>Settings updated</body></html>
```

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

`http://am.luxsinaudio.com/x9/v2/i.html?ip=<device-ip>`

### Static public files

`GET /public/<filename>`

Serves files from the public drive root.

## Common Status Fields

These fields are returned by `sync` and `syncData`. `sync` also includes `peq`.


| Field                     | Description                                                               |
| ------------------------- | ------------------------------------------------------------------------- |
| `device`                  | Device model, normally`Luxsin-X9`.                                        |
| `version`                 | Numeric firmware version from build version macros.                       |
| `mac`                     | Wi-Fi MAC address. Present on non-WIN32 builds.                           |
| `language`                | UI language:`0` English, `1` Traditional Chinese, `2` Simplified Chinese. |
| `volume`                  | DAC volume,`0..200`.                                                      |
| `isDacMetuVolume`         | DAC mute flag as stored by firmware.                                      |
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
| `vu_count`                | VU style count. X9 source defines`16`.                                    |
| `vuSensor`                | VU sensor offset, stored in 0.5 dB steps.                                 |
| `buttonLight`             | Button/knob light brightness mode.                                        |
| `knob_breathlight`        | Knob breathing light mode.                                                |
| `pcm`                     | PCM filter setting.                                                       |
| `dacGain`                 | Headphone gain setting.                                                   |
| `dacArc`                  | ARC/EARC mode.                                                            |
| `balance`                 | Left/right balance setting.                                               |
| `xlr`                     | XLR polarity.                                                             |
| `dacVolumeDirect`         | DAC volume-direct mode.                                                   |
| `dacImpedance`            | DAC impedance setting.                                                    |
| `dsp_enable`              | DSP enable flag.                                                          |
| `audio_enable`            | DSP audio-processing enable flag.                                         |
| `peqEnable`               | PEQ enable flag.                                                          |
| `peqSelect`               | PEQ preset index.                                                         |
| `effect_enable`           | Effect enable flag.                                                       |
| `effect_value`            | Effect preset value.                                                      |
| `width_enable`            | Soundstage width enable flag.                                             |
| `width_value`             | Soundstage width value.                                                   |
| `scene_enable`            | Scene mode enable flag; returned in status, not handled by GET setting.   |
| `scene_value`             | Scene mode value; returned in status, not handled by GET setting.         |
| `crossfeed_enable`        | Crossfeed enable flag.                                                    |
| `crossfeed_value`         | Crossfeed preset value.                                                   |
| `crossfeed_custom_fc`     | Custom crossfeed frequency in Hz.                                         |
| `crossfeed_custom_gain`   | Custom crossfeed attenuation, stored as integer tenths of dB.             |
| `subwoofer_enable`        | Subwoofer enable flag.                                                    |
| `subwoofer_value`         | Subwoofer crossover frequency in Hz.                                      |
| `subwoofer_rate`          | Subwoofer slope index.                                                    |
| `subwoofer_hpf_enable`    | Main-speaker high-pass bypass/full-range flag.                            |
| `subwoofer_lpf_enable`    | Subwoofer low-pass bypass/full-range flag.                                |
| `subwoofer_mix_type`      | Subwoofer output type.                                                    |
| `subwoofer_gain`          | Subwoofer gain in dB.                                                     |
| `subwoofer_delay_main`    | Left main-speaker delay tap count.                                        |
| `subwoofer_delay`         | Left subwoofer delay tap count.                                           |
| `subwoofer_delay_main_r`  | Right main-speaker delay tap count.                                       |
| `subwoofer_delay_r`       | Right subwoofer delay tap count.                                          |
| `analogGain`              | Analog input gain, stored in 0.5 dB steps.                                |
| `color_enable`            | Tone/color EQ enable flag.                                                |
| `color_bass_gain`         | Bass color gain, stored as integer tenths of dB.                          |
| `color_mid_gain`          | Mid color gain, stored as integer tenths of dB.                           |
| `color_treble_gain`       | Treble color gain, stored as integer tenths of dB.                        |
| `loudness_enable`         | Loudness enable flag.                                                     |
| `loudness_bass_gain`      | Loudness bass gain, stored as integer tenths of dB.                       |
| `loudness_treble_gain`    | Loudness treble gain, stored as integer tenths of dB.                     |
| `loudness_threshold_gain` | Loudness threshold in dB.                                                 |
| `hearing_enable`          | Hearing compensation enable flag.                                         |
| `hearing_select`          | Selected hearing profile index.                                           |
| `hearing_data`            | Saved hearing profile JSON string.                                        |
| `bt_status`               | Bluetooth status. Present on non-WIN32 builds.                            |
| `bt_srcname`              | Connected Bluetooth device name. Present on non-WIN32 builds.             |
| `bt_title`                | Bluetooth track title. Present on non-WIN32 builds.                       |
| `bt_artist`               | Bluetooth track artist. Present on non-WIN32 builds.                      |

## Enumerations

### Input source


| Value | Name      |
| ----- | --------- |
| `0`   | USB-B     |
| `1`   | USB-C     |
| `2`   | Coaxial   |
| `3`   | Optical   |
| `4`   | Bluetooth |
| `5`   | HDMI-EARC |
| `6`   | Audio-in  |
| `7`   | Local     |

The source defines `INPUT_COUNT` as `7`, but the enum and product UI expose
values `0..7`.

### Output


| Value | Name      |
| ----- | --------- |
| `0`   | XLR       |
| `1`   | RCA       |
| `2`   | Headphone |
| `3`   | XLR + RCA |

### Subwoofer slope


| Value | Name      |
| ----- | --------- |
| `0`   | 6 dB/oct  |
| `1`   | 12 dB/oct |
| `2`   | 18 dB/oct |
| `3`   | 24 dB/oct |
| `4`   | 30 dB/oct |
| `5`   | 36 dB/oct |
| `6`   | 42 dB/oct |
| `7`   | 48 dB/oct |

### Crossfeed preset


| Value | Name                         |
| ----- | ---------------------------- |
| `0`   | BS2B default, 700 Hz, 4.5 dB |
| `1`   | BS2B popular, 700 Hz, 6 dB   |
| `2`   | BS2B relax, 650 Hz, 9.5 dB   |
| `3`   | Custom                       |

### Effect preset

`effect_value` is `0..15`. The UI list has one Off item plus 16 effect presets;
when a preset is selected, firmware sends `effect_value = list_index - 1`.

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

Saved PEQ config uses string names such as `PEAKING` and `LOW_SHELF`.

## Writable GET Parameters

All parameters below are handled by:

`GET /dev/info.cgi?action=setting&<param>=<value>`


| Parameter                 | Value range                   | Effect                                                         |
| ------------------------- | ----------------------------- | -------------------------------------------------------------- |
| `volume`                  | `0..200`                      | Set DAC volume.                                                |
| `isDacMetuVolume`         | presence;`1` recommended      | Queue CEC/mute-volume event; firmware ignores the value.       |
| `input`                   | `0..7`                        | Set input source.                                              |
| `output`                  | `0..3`                        | Set output.                                                    |
| `bt_next`                 | `1, 0`                        | Bluetooth transport control:`1` next, `0` previous.            |
| `bt_play`                 | presence;`1` recommended      | Bluetooth play/pause toggle; firmware ignores the value.       |
| `language`                | `0..2`                        | Set UI language. Firmware clamps to max`2`.                    |
| `screenLight`             | `0..2`                        | Set LCD brightness.                                            |
| `vu`                      | `0..15`                       | Set VU display style.                                          |
| `sleep`                   | `0..4`                        | Set standby/sleep mode.                                        |
| `screenOff`               | `0..4`                        | Set screen-off mode.                                           |
| `buttonLight`             | `0..3`                        | Set button/knob light mode.                                    |
| `pcm`                     | `0..5`                        | Set PCM DAC filter.                                            |
| `dacGain`                 | `0..3`                        | Set headphone gain.                                            |
| `xlr`                     | `0..1`                        | Set XLR polarity.                                              |
| `soundStep`               | `0..3`                        | Set volume step.                                               |
| `bootSound`               | `0..10`                       | Set boot volume mode.                                          |
| `dacArc`                  | `0..1`                        | Set ARC/EARC mode.                                             |
| `balance`                 | `-150..150`                   | Set balance and reapply volume; displayed as`-15.0..+15.0 dB`. |
| `autoHome`                | `0..3`                        | Set auto-home mode.                                            |
| `knob_breathlight`        | `0..1`                        | Set knob breathing light.                                      |
| `analogGain`              | `-24..24`                     | Set analog gain; displayed as`-12.0..+12.0 dB`.                |
| `dacVolumeDirect`         | `0..2`                        | Set volume-direct mode: Off, 0 dB, or -12 dB.                  |
| `dacImpedance`            | `0..1`                        | Set impedance mode.                                            |
| `vuSensor`                | `0..40`                       | Set VU sensor offset; displayed as`+0.0..+20.0 dB`.            |
| `power`                   | presence;`1` recommended      | Power off.                                                     |
| `dsp_enable`              | `0..1`                        | Queue remote DSP enable/disable.                               |
| `audio_enable`            | `0..1`                        | Enable/disable DSP audio processing path.                      |
| `crossfeed_custom_fc`     | `500..1000`                   | Set custom crossfeed frequency in Hz.                          |
| `crossfeed_custom_gain`   | `10..150`                     | Set custom crossfeed attenuation; displayed as`1.0..15.0 dB`.  |
| `crossfeed_value`         | `0..3`                        | Set crossfeed preset.                                          |
| `crossfeed_enable`        | `0..1`                        | Enable crossfeed.                                              |
| `effect_value`            | `0..15`                       | Set effect preset.                                             |
| `effect_enable`           | `0..1`                        | Enable effect.                                                 |
| `width_enable`            | `0..1`                        | Enable soundstage width.                                       |
| `width_value`             | `0..100`                      | Set width; firmware sends`0.02 * value` to DSP.                |
| `color_enable`            | `0..1`                        | Enable tone/color EQ.                                          |
| `color_bass_gain`         | `-100..100`                   | Set bass color gain; displayed as`-10.0..+10.0 dB`.            |
| `color_mid_gain`          | `-100..100`                   | Set mid color gain; displayed as`-10.0..+10.0 dB`.             |
| `color_treble_gain`       | `-100..100`                   | Set treble color gain; displayed as`-10.0..+10.0 dB`.          |
| `loudness_enable`         | `0..1`                        | Enable loudness.                                               |
| `loudness_bass_gain`      | `0..100`                      | Set loudness bass gain; displayed as`0.0..10.0 dB`.            |
| `loudness_threshold_gain` | `-30..0`                      | Set loudness threshold in dB.                                  |
| `loudness_treble_gain`    | `0..100`                      | Set loudness treble gain; displayed as`0.0..10.0 dB`.          |
| `subwoofer_enable`        | `0..1`                        | Enable subwoofer.                                              |
| `subwoofer_value`         | `40..300`                     | Set subwoofer crossover frequency in Hz.                       |
| `subwoofer_rate`          | `0..7`                        | Set subwoofer slope.                                           |
| `subwoofer_hpf_enable`    | `0..1`                        | Toggle main-speaker high-pass bypass/full-range mode.          |
| `subwoofer_lpf_enable`    | `0..1`                        | Toggle subwoofer low-pass bypass/full-range mode.              |
| `subwoofer_mix_type`      | `0..1`                        | Set subwoofer output type:`0` mix, `1` stereo.                 |
| `subwoofer_gain`          | `-15..15`                     | Set subwoofer gain in dB.                                      |
| `subwoofer_delay_main`    | `0..1920`                     | Set left main-speaker delay; one tap is about`1/48 ms`.        |
| `subwoofer_delay`         | `0..1920`                     | Set left subwoofer delay; one tap is about`1/48 ms`.           |
| `subwoofer_delay_main_r`  | `0..1920`                     | Set right main-speaker delay; one tap is about`1/48 ms`.       |
| `subwoofer_delay_r`       | `0..1920`                     | Set right subwoofer delay; one tap is about`1/48 ms`.          |
| `hearing_enable`          | `0..1`                        | Enable hearing compensation.                                   |
| `hearing_select`          | `0..(hearing_result_count-1)` | Select saved hearing profile; firmware supports max 5 results. |
| `peqSelect`               | `0..(peq_count-1)`            | Select PEQ preset.                                             |
| `peqEnable`               | `0..1`                        | Queue remote PEQ enable/disable.                               |

## Hearing Data

`hearing_data` is a JSON string containing up to 5 hearing profiles. Current X9
source uses 10 frequency points:

`125, 250, 500, 1000, 2000, 3000, 4000, 5000, 6000, 8000 Hz`

Each profile stores left/right threshold arrays with keys `l` and `r`. Older
7-point arrays are accepted and expanded by the firmware.

## PEQ POST Control

`POST /dev/info.cgi`

The X9 source collects POST form data, decodes the field value as custom-Base64.

The form field name is not checked by this source, but `json=<CUSTOM_BASE64>` is the clearest
client convention.

Known control shapes include `peq`, `peqChange`, `peqApply`, `peqRename`, and
`peqRemove`. Common add/update shape:

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
curl "http://<device-ip>/dev/info.cgi?action=setting&volume=120&input=5"
```

Poll changes:

```bash
curl "http://<device-ip>/msgCount"
```

See `sample.html` for a browser example with decode/encode helpers.
