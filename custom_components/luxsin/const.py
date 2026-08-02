"""Constants for the Luxsin X8/X9 integration."""

DOMAIN = "luxsin"

# How often to poll /msgCount (cheap change counter). The full status
# (/dev/info.cgi?action=sync, which includes PEQ presets) is only fetched
# when the counter changes.
DEFAULT_SCAN_INTERVAL = 3
DEFAULT_TIMEOUT = 3.0

# --------------------------------------------------------------------------
# X8 and X9 share the same wire protocol (endpoints, custom Base64
# alphabet, and most fields are identical per the manufacturer-provided
# X8-API-README.md / X9-API-README.md), but their input enumerations
# differ. The model is detected from the "device" field in the status
# payload ("Luxsin-X8" / "Luxsin-X9").
#
# INPUT_NAMES_BY_MODEL:
#   - "x8": 6 inputs (0-5), confirmed by X8-API-README.md and by a real
#     X8 device.
#   - "x9": 8 inputs (0-7), confirmed by X9-API-README.md. X9 has
#     HDMI-EARC/Audio-in/Local inputs X8 doesn't, and X8's input 0 is
#     named "USB" vs X9's "USB-B".
#
# OUTPUT_NAMES is identical for both models per both documents (0: XLR,
# 1: RCA, 2: Headphone, 3: XLR + RCA), so it isn't split per-model.
#
# The bigger protection against X8/X9 differences isn't these tables
# though - it's that light/number/switch/select entities (LED, balance,
# DSP/loudness/PEQ) are only created when the corresponding field is
# actually present in a given device's status payload (see entity.py:
# has_fields()). For example, X9-API-README.md doesn't mention the LED
# fields at all - if a real X9 doesn't return them, the light entity
# simply won't be created, with no per-model code needed for that case.
# --------------------------------------------------------------------------
DEFAULT_MODEL_KEY = "x8"  # fallback if the model can't be recognized

INPUT_NAMES_BY_MODEL: dict[str, list[str]] = {
    "x8": ["USB", "USB-C", "Coaxial", "Optical", "Bluetooth", "IIS"],
    "x9": [
        "USB-B",
        "USB-C",
        "Coaxial",
        "Optical",
        "Bluetooth",
        "HDMI-EARC",
        "Audio-in",
        "Local",
    ],
}
OUTPUT_NAMES = ["XLR", "RCA", "Headphone", "XLR + RCA"]


def normalize_model_key(device_field: str | None) -> str:
    """'Luxsin-X8' -> 'x8', 'Luxsin-X9' -> 'x9', else DEFAULT_MODEL_KEY."""
    if device_field:
        upper = device_field.upper()
        if "X9" in upper:
            return "x9"
        if "X8" in upper:
            return "x8"
    return DEFAULT_MODEL_KEY


def input_names_for(model_key: str) -> list[str]:
    return INPUT_NAMES_BY_MODEL.get(model_key, INPUT_NAMES_BY_MODEL[DEFAULT_MODEL_KEY])


# Native volume scale of the device, confirmed by both X8-API-README.md and
# X9-API-README.md ("volume: 0..200").
MAX_VOLUME = 200

# --------------------------------------------------------------------------
# Balance: confirmed identical for both models (-150..150 raw, displayed as
# -15.0..+15.0 dB) by X8-API-README.md and X9-API-README.md. The number
# entity works directly in dB and converts to/from the raw integer when
# talking to the device.
# --------------------------------------------------------------------------
BALANCE_MIN_DB = -15.0
BALANCE_MAX_DB = 15.0
BALANCE_STEP_DB = 0.1
BALANCE_SCALE = 10  # raw = round(dB * BALANCE_SCALE)

# Screen (LCD) brightness: confirmed identical for both models by
# X8-API-README.md / X9-API-README.md ("screenLight: 0..2, Set LCD
# brightness"). A 3-level discrete setting, not a continuous 0-100% range -
# exposed as a plain integer number rather than inventing specific level
# names (e.g. "Low/Medium/High") that aren't documented.
SCREEN_BRIGHTNESS_MIN = 0
SCREEN_BRIGHTNESS_MAX = 2
