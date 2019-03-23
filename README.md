# Oversteer - Steering Wheel Manager for Linux

https://github.com/berarma/oversteer

Graphical application to configure Logitech Wheels.

Features supported:
 - Setting the emulation mode.
 - Setting the rotation range.
 - Combine pedals for games that use just one axis for gas/brake.

This software uses the Linux driver for Logitech HID++ devices and thus it
could work on any model supported by said driver.

It's only been tested on the Logitech G29 Driving Force. It could work on other
models but it's untested.

Please, use at your own risk. Suggestions, bugs and pull requests welcome.

## Requirements

You can install all dependencies on Debian systems with the following command:

```apt install python3 python3-gi python3-pyudev python3-xdg meson appstream-util desktop-file-utils jstest-gtk```

Other distros may use slightly different names for the same packages.

```jstest-gtk``` is launched when the test button is clicked.

### Permissions

The app will ask for an administrator password if it doesn't have permissions
to write to the device driver.

You can make the driver files writable by anyone using udev rules. It will
allow using this app without administrator privileges and also make some driver
features available to games.

Install the udev rules file:

```cp data/udev/99-logitech-wheel-perms.rules /etc/udev/rules.d/```

Reload udev rules (or reboot your computer):

```sudo udevadm control --reload-rules && sudo udevadm trigger```

The changes will take effect next time the device is plugged.

## Build and install

Build:

```
meson build
ninja -C build
```

Trying it without installing:

```ninja -C build run```

Installing:

```ninja -C build install```

Uninstalling:

```ninja -C build uninstall```

