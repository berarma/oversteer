from collections import namedtuple
from enum import Enum


ABS_mode = namedtuple("ABS_mode", ["id", "name"])


class AxisMode(Enum):
    NORMAL                      = ABS_mode(0, "Normal")
    INVERTED                    = ABS_mode(1, "Inverted")
    HALF                        = ABS_mode(2, "Half")
    HALF_INVERTED               = ABS_mode(3, "Half inverted")
    CENTERED_HALF               = ABS_mode(4, "Centered half")
    CENTERED_HALF_INVERTED      = ABS_mode(5, "Centered half inverted")
    CENTERED_SWITCHING          = ABS_mode(6, "Centered switching")
    CENTERED_SWITCHING_INVERTED = ABS_mode(7, "Centered switching inverted")
    CENTERED_LOOPING            = ABS_mode(8, "Centered looping")
    CENTERED_LOOPING_INVERTED   = ABS_mode(9, "Centered looping inverted")


class CombinedPedals:
    NONE = 0
    COMBINE_BRAKES = 1
    COMBINE_CLUTCH = 2


def get_modified_value(mode, value):
    if mode == AxisMode.NORMAL:
        return value

    elif mode == AxisMode.INVERTED:
        return 255 - value

    elif mode == AxisMode.HALF:
        return value + int((255 - value + 1) / 2)

    elif mode == AxisMode.HALF_INVERTED:
        return (int(value / 2) - int(255 / 2)) * -1

    elif mode == AxisMode.CENTERED_HALF:
        return int(value / 2)

    elif mode == AxisMode.CENTERED_HALF_INVERTED:
        return 255 - int(value / 2)

    elif mode == AxisMode.CENTERED_SWITCHING:
        value = value - int(255 / 2) - 1
        if value < 0:
            value = (value * -1) + int(255 / 2)
        return value

    elif mode == AxisMode.CENTERED_SWITCHING_INVERTED:
        if value > int(255 / 2):
            value = int(255 + 255 / 2) - value + 1
        return value

    elif mode == AxisMode.CENTERED_LOOPING:
        value = value - int(255 / 2) - 1
        if value < 0:
            value += 256
        return value

    elif mode == AxisMode.CENTERED_LOOPING_INVERTED:
        value = int(255 / 2) - value
        if value < 0:
            value += 256
        return value

    return value
