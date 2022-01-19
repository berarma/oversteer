import logging
import os
import pyudev
from .device import Device
from . import wheel_ids as wid

logging.basicConfig(level=logging.DEBUG)

class DeviceManager:

    def __init__(self):
        self.supported_wheels = {
            wid.LG_G29: 900,
            wid.LG_G920: 900,
            wid.LG_G923X: 900,
            wid.LG_G923P: 900,
            wid.LG_DF: 270,
            wid.LG_MOMO: 270,
            wid.LG_DFP: 900,
            wid.LG_G25: 900,
            wid.LG_DFGT: 900,
            wid.LG_G27: 900,
            wid.LG_SFW: 270,
            wid.LG_MOMO2: 270,
            wid.LG_WFG: 180,
            wid.LG_WFFG: 180,
            wid.TM_T150: 1080,
            wid.TM_T300RS: 1080,
            wid.TM_T500RS: 1080,
            wid.FT_CSL_ELITE: 1080,
            wid.FT_CSL_ELITE_PS4: 1080,
            wid.FT_CSV2: 900,
            wid.FT_CSV25: 900,
            wid.FT_PDD1: 1080,
        }
        self.supported_pedals = {
            wid.TM_TLCM,
        }
        self.devices = {}
        self.pedals = {}
        self.changed = True

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
        usb_id = str(udevice.get('ID_VENDOR_ID')) + ':' + str(udevice.get('ID_MODEL_ID'))
        if usb_id not in self.supported_wheels:
            return
        seat_id = udevice.get('ID_FOR_SEAT')
        logging.debug("%s: %s", action, seat_id)
        if seat_id is None:
            return
        if action == 'add':
            self.update_device_list(udevice)
            device = self.get_device(seat_id)
            device.reconnect()
            self.changed = True
        if action == 'remove':
            device = self.get_device(seat_id)
            device.disconnect()
            self.changed = True

    def init_device_list(self):
        context = pyudev.Context()
        for udevice in context.list_devices(subsystem='input', ID_INPUT_JOYSTICK=1):
            usb_id = str(udevice.get('ID_VENDOR_ID')) + ':' + str(udevice.get('ID_MODEL_ID'))
            if usb_id in self.supported_wheels:
                self.update_device_list(udevice, usb_id)
            if usb_id in self.supported_pedals:
                self.update_pedal_list(udevice, usb_id)

        logging.debug('Devices: %s', self.devices)
        logging.debug('Pedals: %s', self.pedals)

    def update_device_list(self, udevice, usb_id):
        seat_id = udevice.get('ID_FOR_SEAT')
        logging.debug("update_device_list: %s", seat_id)
        if seat_id is None:
            return

        if seat_id not in self.devices:
            self.devices[seat_id] = Device(self, {
                'seat_id': seat_id,
            })

        device = self.devices[seat_id]

        if 'DEVNAME' in udevice:
            if 'event' in udevice.get('DEVNAME'):
                device.set({
                    'vendor_id': udevice.get('ID_VENDOR_ID'),
                    'product_id': udevice.get('ID_MODEL_ID'),
                    'usb_id': usb_id,
                    'dev_name': udevice.get('DEVNAME'),
                    'max_range': self.supported_wheels[usb_id],
                })
        else:
            device.set({
                'dev_path': os.path.join(udevice.sys_path, 'device'),
                'name': udevice.get('NAME').strip('"'),
            })

    def update_pedal_list(self, udevice, usb_id):
        logging.debug("update_pedal_list: %s", usb_id)

        if usb_id not in self.pedals:
            self.pedals[usb_id] = Device(self, {
                'usb_id': usb_id,
            })

        pedals = self.pedals[usb_id]

        if pedals.vendor_id is None:
            pedals.vendor_id = udevice.get('ID_VENDOR_ID')

        if pedals.product_id is None:
            pedals.product_id = udevice.get('ID_MODEL_ID')

        if pedals.seat_id is None:
            seat_id = udevice.get('ID_FOR_SEAT')
            if seat_id is not None:
                pedals.seat_id = seat_id

        if pedals.dev_path is None:
            dev_path = os.path.join(udevice.sys_path, 'device')
            if dev_path is not None:
                pedals.dev_path = dev_path

        if pedals.name is None:
            name = udevice.get('NAME').strip('"')
            if name is not None:
                pedals.name = name

        if pedals.dev_name is None:
            dev_name = udevice.get('DEVNAME')
            if dev_name is not None and 'event' in dev_name:
                pedals.dev_name = dev_name

    def first_device(self):
        if self.devices:
            return self.get_device(next(iter(self.devices)))
        return None

    def get_devices(self):
        self.changed = False
        return list(self.devices.values())

    def get_pedals(self):
        return list(self.pedals.values())

    def get_pedal(self, pid):
        if pid is None:
            return None
        if pid in self.pedals:
            return self.pedals[pid]
        return next((item for item in self.pedals.values() if item.dev_name == pid), None)

    def get_device(self, did):
        if did is None:
            return None
        if did in self.devices:
            return self.devices[did]
        return next((item for item in self.devices.values() if item.dev_name == did), None)

    def is_changed(self):
        return self.changed
