from evdev import ecodes, ff
import numpy as np
from threading import Thread, Event
import time

class Test:

    def __init__(self, device, callback):
        self.device = device
        self.input_device = self.device.get_input_device()
        self.notify = callback
        self.collecting_data = False
        self.awaiting_action = False

    def get_input_values(self):
        return self.input_values

    def get_output_values(self):
        return self.output_values

    def get_minimum_level(self):
        return self.minimum_level

    def is_collecting_data(self):
        return self.collecting_data

    def is_awaiting_action(self):
        return self.awaiting_action

    def trigger_action(self):
        self.action_triggered = True

    def start(self):
        self.input_values = []
        self.output_values = []

        # Save wheel settings
        self.current_range = self.device.get_range()
        self.current_ff_gain = self.device.get_ff_gain()
        self.current_autocenter = self.device.get_autocenter()

        # Prepare wheel
        try:
            for effect_id in range(self.input_device.ff_effects_count):
                self.input_device.erase_effect(effect_id)
        except OSError:
            pass

        self.device.set_range(900)
        self.device.set_ff_gain(65535)
        self.device.set_autocenter(0)

    def stop(self):
        # Restore wheel settings
        self.device.set_range(self.current_range)
        self.device.set_ff_gain(self.current_ff_gain)
        self.device.set_autocenter(self.current_autocenter)

    def create_left_effect(self, level = 0x7fff):
        left_effect = ff.Effect(
            ecodes.FF_CONSTANT, -1, 0x4000,
            ff.Trigger(0, 0),
            ff.Replay(0, 0),
            ff.EffectType(ff_constant_effect=ff.Constant(level=level))
        )
        left_effect.id = self.input_device.upload_effect(left_effect)
        return left_effect

    def create_right_effect(self, level = 0x7fff):
        right_effect = ff.Effect(
            ecodes.FF_CONSTANT, -1, 0xc000,
            ff.Trigger(0, 0),
            ff.Replay(0, 0),
            ff.EffectType(ff_constant_effect=ff.Constant(level=level))
        )
        right_effect.id = self.input_device.upload_effect(right_effect)
        return right_effect

    def update_effect(self, effect):
        self.input_device.upload_effect(effect)

    def erase_effect(self, effect):
        self.input_device.erase_effect(effect.id)

    def run(self, test_id):
        if test_id == 0:
            Thread(target=self.test1).start()
        elif test_id == 1:
            Thread(target=self.test2).start()
        elif test_id == 2:
            Thread(target=self.test3).start()

    def append_data(self, timestamp, value):
        if self.collecting_data is False:
            return
        self.output_values.append((timestamp - self.test_starttime, (value - 32768) / 32768))

    def seed_axis_position(self):
        # Move the wheel a bit to start collecting data
        effect = self.create_left_effect(0x2000)
        self.input_device.write(ecodes.EV_FF, effect.id, 1)
        time.sleep(0.1)
        self.input_device.write(ecodes.EV_FF, effect.id, 0)
        self.erase_effect(effect)

    def center_wheel(self):
        # Center wheel
        self.device.set_autocenter(65535)
        time.sleep(1)
        self.device.set_autocenter(0)
        # Wait for wheel to stabilize and all events to arrive
        time.sleep(0.1)

    # Minimum torque test
    def test1(self):
        self.start()
        self.center_wheel()

        # Start test
        self.action_triggered = False
        self.awaiting_action = True

        while not self.action_triggered:
            time.sleep(0.5)

        self.action_triggered = False

        left_effect = self.create_left_effect(0)
        right_effect = self.create_right_effect(0)
        self.input_device.write(ecodes.EV_FF, left_effect.id, 1)
        self.input_device.write(ecodes.EV_FF, right_effect.id, 1)

        # Increasing force square effect
        for level in range(0, 0x7fff, 30):
            print(level)
            left_effect.u.ff_constant_effect.level = level
            self.update_effect(left_effect)
            time.sleep(0.1)
            left_effect.u.ff_constant_effect.level = 0
            self.update_effect(left_effect)
            right_effect.u.ff_constant_effect.level = level
            self.update_effect(right_effect)
            time.sleep(0.1)
            right_effect.u.ff_constant_effect.level = 0
            self.update_effect(right_effect)
            if self.action_triggered:
                self.minimum_level = level
                break

        self.erase_effect(left_effect)
        self.erase_effect(right_effect)

        # Stop test
        self.awaiting_action = False
        self.stop()

        # Notify application the test is done
        self.notify()

    def test2(self):
        self.start()
        self.seed_axis_position()
        self.center_wheel()

        left_effect = self.create_left_effect(0)
        right_effect = self.create_right_effect(0)

        # Set the starting points for the test
        starting_wheel_pos = (self.device.get_last_axis_value(ecodes.ABS_X) - 32768) / 32768
        self.input_values = [(0, 0)]
        self.output_values = [(0, starting_wheel_pos)]
        self.test_starttime = time.time()
        time.sleep(0.1)

        # Start collecting data
        self.collecting_data = True

        for level in np.arange(0, 0x8000, 0x7fff / 50):
            level = int(round(level))

            # Move wheel right
            right_effect.u.ff_constant_effect.level = level
            self.update_effect(right_effect)
            self.input_device.write(ecodes.EV_FF, right_effect.id, 1)
            self.input_values.append((time.time() - self.test_starttime, -level / 0x7fff))
            time.sleep(0.3)
            self.input_device.write(ecodes.EV_FF, right_effect.id, 0)

            # Move wheel left
            left_effect.u.ff_constant_effect.level = level
            self.update_effect(left_effect)
            self.input_device.write(ecodes.EV_FF, left_effect.id, 1)
            self.input_values.append((time.time() - self.test_starttime, level / 0x7fff))
            time.sleep(0.3)
            self.input_device.write(ecodes.EV_FF, left_effect.id, 0)

        # Stop collecting data
        self.collecting_data = False

        # Notify application the test is done
        self.notify()

    def test3(self):
        self.start()
        self.seed_axis_position()
        self.center_wheel()

        left_effect = self.create_left_effect()
        right_effect = self.create_right_effect()

        # Set the starting points for the test
        starting_wheel_pos = (self.device.get_last_axis_value(ecodes.ABS_X) - 32768) / 32768
        self.input_values = [(0, 0)]
        self.output_values = [(0, starting_wheel_pos)]
        self.test_starttime = time.time()
        time.sleep(0.1)

        # Start collecting data
        self.collecting_data = True

        # Move wheel right at top speed
        self.input_values.append((time.time() - self.test_starttime, 1))
        self.input_device.write(ecodes.EV_FF, right_effect.id, 1)
        time.sleep(0.3)
        self.input_device.write(ecodes.EV_FF, right_effect.id, 0)

        # Move wheel left at top speed
        self.input_values.append((time.time() - self.test_starttime, -1))
        self.input_device.write(ecodes.EV_FF, left_effect.id, 1)
        time.sleep(0.3)
        self.input_device.write(ecodes.EV_FF, left_effect.id, 0)

        # Move wheel right at top speed
        self.input_values.append((time.time() - self.test_starttime, 1))
        self.input_device.write(ecodes.EV_FF, right_effect.id, 1)
        time.sleep(0.3)
        self.input_device.write(ecodes.EV_FF, right_effect.id, 0)
        self.input_values.append((time.time() - self.test_starttime, 0))

        # Keep collecting deceleration data
        time.sleep(0.5)
        self.input_values.append((time.time() - self.test_starttime, 0))

        # Stop collecting data
        self.collecting_data = False

        # Notify application the test is done
        self.notify()
