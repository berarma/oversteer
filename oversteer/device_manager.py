import logging
import os
import pyudev
import time
import glob
import yaml
from .device import Device
from .definition import Definition
from evdev import ecodes
from yaml import load
from yaml import Loader

class DeviceManager:

    def __init__(self):
        self.devices = {}
        self.changed = True
        self.definitions = {}
        for file in glob.glob("data/definitions/*.yaml"):
            logging.debug("Reading definitions file: %s", file)
            with open(file, 'r') as stream:
                try:
                    data = load(stream, Loader=Loader)
                    definition = Definition(data)
                    self.definitions[definition.vendor + ":" + definition.product] = definition
                except yaml.YAMLError as exc:
                    logging.error("Error in definition file: %s", exc)

    def start(self):
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by('input')
        self.observer = pyudev.MonitorObserver(monitor, self.register_event)
        self.init_device_list()
        self.observer.start()

    def stop(self):
        self.observer.stop()

    def register_event(self, action, udevice):
        id = udevice.device_path
        if id is None:
            return
        logging.debug("Udev event %s: %s", action, id)
        if action == 'add':
            self.update_device_list(udevice)
            device = self.get_device(id)
            if device:
                time.sleep(5)
                device.enable()
                self.changed = True
        if action == 'remove':
            device = self.get_device(id)
            if device:
                device.disable()
                self.changed = True

    def init_device_list(self):
        context = pyudev.Context()
        for udevice in context.list_devices(subsystem='input', ID_INPUT_JOYSTICK=1):
            self.update_device_list(udevice)

        logging.debug('Devices: %s', self.devices)

        for key in self.devices:
            logging.debug("%s: %s", key, vars(self.devices[key]))

        self.changed = True

    def update_device_list(self, udevice):
        id = udevice.device_path
        device_node = udevice.device_node

        if not id or not device_node or not 'event' in udevice.get('DEVNAME'):
            return

        usb_id = str(udevice.get('ID_VENDOR_ID')) + ':' + str(udevice.get('ID_MODEL_ID'))
        if not usb_id in self.definitions:
            return

        logging.debug("update_device_list: %s %s", id, device_node)

        if id not in self.devices:
            self.devices[id] = Device(self, {})

        device = self.devices[id]

        logging.debug("%s: ID_VENDOR_ID: %s ID_MODEL_ID: %s", device_node,
                      udevice.get('ID_VENDOR_ID'), udevice.get('ID_MODEL_ID'))

        device.set({
            'id': id,
            'vendor_id': udevice.get('ID_VENDOR_ID'),
            'product_id': udevice.get('ID_MODEL_ID'),
            'usb_id': usb_id,
            'dev_name': device_node,
            'dev_path': os.path.realpath(os.path.join(udevice.sys_path, 'device', 'device')),
            'name': bytes(udevice.get('ID_VENDOR_ENC') + ' ' + udevice.get('ID_MODEL_ENC'),
                          'utf-8').decode('unicode_escape'),
            'rotation': self.definitions[usb_id].rotation,
            'input_map': self.definitions[usb_id].input_map,
            })

    def first_device(self):
        if self.devices:
            return self.get_device(next(iter(self.devices)))
        return None

    def get_devices(self):
        return list(self.devices.values())

    def get_device(self, did):
        if did is None:
            return None
        if did in self.devices:
            return self.devices[did]
        return next((item for item in self.devices.values() if item.dev_name == did), None)

    def is_changed(self):
        changed = self.changed
        self.changed = False
        return changed
