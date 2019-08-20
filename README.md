# Oversteer - Steering Wheel Manager for Linux

https://github.com/berarma/oversteer

Oversteer is a desktop application to configure Logitech Wheels.

Features (when supported by the device):
 - Change emulation mode.
 - Change rotation range.
 - Combine accelerator/brakes pedals for games that use just one axis.
 - Device configuration profiles.
 - Fix system permissions to access all device features.

This software uses the Linux driver for Logitech HID++ devices and thus it
could work on any model supported by said driver:

 - Driving Force / Formula EX
 - Driving Force Pro
 - Driving Force GT
 - Momo Force
 - Momo Racing Force
 - Speed Force Wireless
 - G25 Racing Wheel
 - G27 Racing Wheel
 - G29 Driving Force Racing Wheel
 - G920 Driving Force Racing Wheel

I can test only on a Logitech G29 Driving Force. Please, report your results
with different devices.

Use at your own risk. Suggestions, bugs and pull requests welcome.

## Installation

### Arch

There's an AUR package kindly created by DNModder.

[Install](https://wiki.archlinux.org/index.php/Arch_User_Repository#Installing_packages) the [Oversteer](https://aur.archlinux.org/packages/oversteer/) package.

### Other distributions

#### Requirements

You can install all dependencies on Debian systems with the following command:

```apt install python3 python3-gi python3-pyudev python3-xdg gettext meson appstream-util desktop-file-utils jstest-gtk```

Other distros may use slightly different names for the same packages.

```jstest-gtk``` is launched when the test button is clicked.

#### Permissions

The access to some device features might be restricted by permissions. The app
will ask for an administrator password when needed.

Device access can be permanently allowed to any user and application from the
preferences window. It will install a udev rule file for the Logitech wheels.

#### Build and install

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

## Collaboration

We could all benefit greatly benefit from your help as with any other free software project.

Reports about what works and what not on different devices and systems are very welcome. You can also help by contributing specific notes for your distro or doing the packaging work. Anything that you find useful might help others.
