from enum import IntEnum

EventType = IntEnum('EventType', [
    'STEERING', # [0, 65535]
    'THROTTLE', # [0, 255]
    'BRAKES', # [0, 255]
    'CLUTCH', # [0, 255]
    'HANDBRAKE', # [0, 255]
    'HAT0_X', # [-1, 1]
    'HAT0_Y', # [-1, 1]
    'GEAR_DOWN',
    'GEAR_UP',
    'GEAR_1',
    'GEAR_2',
    'GEAR_3',
    'GEAR_4',
    'GEAR_5',
    'GEAR_6',
    'GEAR_7',
    'GEAR_8',
    'GEAR_R',
    'BTN_0',
    'BTN_1',
    'BTN_2',
    'BTN_3',
    'BTN_4',
    'BTN_5',
    'BTN_6',
    'BTN_7',
    'BTN_8',
    'BTN_9',
    'BTN_10',
    'BTN_11',
    'BTN_12',
    'BTN_13',
    'BTN_14',
    'BTN_15',
    'BTN_16',
    'BTN_17',
    'BTN_18',
    'BTN_19',
    'BTN_20',
    'BTN_21',
    'BTN_22',
    'BTN_23',
    'BTN_24',
    'BTN_25',
    'BTN_26',
    'BTN_27',
    'BTN_28',
    'BTN_29',
])

class DeviceEventType:

    def __init__(self, event_type, params):
        self.event_type = EventType[event_type]
        if params:
            self.min_value = params[0]
            self.max_value = params[1]
        else:
            self.min_value = 0
            self.max_value = 1

