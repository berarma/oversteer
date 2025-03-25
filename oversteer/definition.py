import logging
from evdev import ecodes
from .device_event_type import DeviceEventType, EventType

class Definition:

    def __init__(self, data):
        self.vendor = data['vendor']
        self.product = data['product']
        self.rotation = data['rotation']
        self.input_map = {}
        for src_event_type, src_events in data['input_map'].items():
            src_event_type = ecodes.ecodes[src_event_type]
            if not src_event_type in self.input_map:
                self.input_map[src_event_type] = {} 
            for src_event, event_translation in src_events.items():
                if type(src_event) is not int:
                    src_event = ecodes.ecodes[src_event]
                if isinstance(event_translation, list):
                    event_type, params = event_translation
                else:
                    event_type = event_translation
                    params = {}
                if event_type in EventType.__members__:
                    self.input_map[src_event_type][src_event] = DeviceEventType(event_type, params)
                else:
                    logging.error("Event type %s doesn't exist.", event_type)

