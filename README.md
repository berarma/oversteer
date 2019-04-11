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

