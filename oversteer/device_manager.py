from enum import Enum
import functools
import glob
import logging
import os
import pyudev
import re
import select
import time
from .device import Device

logging.basicConfig(level=logging.DEBUG)

class DeviceManager:

    VENDOR_LOGITECH = '046d'
    VENDOR_THRUSTMASTER = '044f'

    LG_G29 = '046d:c24f'
    LG_G920 = '046d:c262'
    LG_DF = '046d:c294'
    LG_MOMO = '046d:c295'
    LG_DFP = '046d:c298'
    LG_G25 = '046d:c299'
    LG_DFGT = '046d:c29a'
    LG_G27 = '046d:c29b'
    LG_SFW = '046d:c29c'
    LG_MOMO2 = '046d:ca03'
    TM_T300RS = '044f:b66e'

    supported_wheels = []

    def __init__(self):
        self.supported_wheels = [
            self.LG_G29,
            self.LG_G920,
            self.LG_DF,
            self.LG_MOMO,
            self.LG_DFP,
            self.LG_G25,
            self.LG_DFGT,
            self.LG_G27,
            self.LG_SFW,
            self.LG_MOMO2,
            self.TM_T300RS,
        ]
        self.reset()

    def reset(self):
        self.devices = {}

        context = pyudev.Context()
        for device in context.list_devices(subsystem='input', ID_INPUT_JOYSTICK=1):
            if str(device.get('ID_VENDOR_ID')) + ':' + str(device.get('ID_MODEL_ID')) in self.supported_wheels:
                self.add_udev_data(device)

        logging.debug('Devices:' + str(self.devices))

    def add_udev_data(self, device):
        seat_id = device.get('ID_FOR_SEAT')

        if seat_id not in self.devices:
            data = {
                'seat_id': seat_id,
                'vendor': device.get('ID_VENDOR_ID'),
                'model': device.get('ID_MODEL_ID'),
                'usb_id': device.get('ID_VENDOR_ID') + ':' + device.get('ID_MODEL_ID'),
            }
            self.devices[seat_id] = data
        else:
            data = self.devices[seat_id]

        if device.get('DEVNAME'):
            if 'event' in device.get('DEVNAME'):
                data['dev_name'] = device.get('DEVNAME')
        else:
            data['dev_path'] = os.path.join(device.sys_path, 'device')
            data['name'] = device.get('NAME').strip('"')

    def wait_for_device(self, seat_id):
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by('input')
        for device in iter(functools.partial(monitor.poll, 2), None):
            if device.action == 'add' and device.get('ID_FOR_SEAT') == seat_id:
                self.add_udev_data(device)

    def first_device(self):
        if self.devices:
            return self.get_device(next(iter(self.devices)))
        return None

    def list_devices(self):
        device_list = []
        for key, device in self.devices.items():
            device_list.append([key, device['name']])
        return device_list

    def get_device(self, id):
        if id in self.devices:
            return Device(self, self.devices[id])
        else:
            for seat_id, device in self.devices:
                if device['dev_name'] == id:
                    return Device(self, device)
        return None
