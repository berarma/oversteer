from .device_event_type import EventType

class DeviceEvent:

    def __init__(self, device_event_type, value):
        self.device_event_type = device_event_type
        self.code = self.device_event_type.event_type
        self.value = self.scale_int(value)

    def scale_int(self, value):
        return (value - self.device_event_type.min_value) * 65535 / (self.device_event_type.max_value - self.device_event_type.min_value)

    def get_value(self):
        return self.value

    def is_button(self):
        return self.device_event_type.min_value == 0 and self.device_event_type.max_value == 1

    def get_button(self):
        if self.is_button():
            return self.code.value - EventType.BTN_0.value
        else:
            return None
