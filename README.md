# Oversteer - Steering Wheel Manager for Linux

https://github.com/berarma/oversteer

Graphical application to configure Logitech Wheels.

Features supported:
 - Emulation mode setting.
 - Rotation range setting.
 - Combine pedals setting for games that use just one axis for gas/brake.
 - Settings profiles.
 - System configuration allowing user access to all device features.

This software uses the Linux driver for Logitech HID++ devices and thus it
could work on any model supported by said driver:

 - Driving Force / Formula EX
 - Driving Force Pro
 - Driving Force GT
 - G25 Racing Wheel
 - G27 Racing Wheel
 - G29 Driving Force Racing Wheel

I can test only on a Logitech G29 Driving Force. Please, report on your results
with different devices.

Please, use at your own risk. Suggestions, bugs and pull requests welcome.

## Requirements

You can install all dependencies on Debian systems with the following command:

```apt install python3 python3-gi python3-pyudev python3-xdg gettext meson appstream-util desktop-file-utils jstest-gtk```

Other distros may use slightly different names for the same packages.

```jstest-gtk``` is launched when the test button is clicked.

### Permissions

The access to some device features might be restricted by permissions. The app
will ask for an administrator password when needed.

Device access can be permanently allowed to any user and application from the
preferences window. It will install a udev rule file for the Logitech wheels.

## Build and install

Build:

```
meson build
ninja -C build
```

Trying it without installing:

```ninja -C build run```

Installing (needs administration rights):

```sudo ninja -C build install```

Uninstalling (needs administration rights):

```sudo ninja -C build uninstall```

