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

## Installation

For now, it lacks a convenient installation method.

Download this repository and run ```./oversteer.py```.

### Dependencies

There's some required Python dependencies. Please, install the following
Python3 packages in case they're not installed already:

 - gi
 - pyudev
 - xdg

```jstest-gtk``` is launched when the test button is clicked.

On Debian derived distros you can use the following command to install them:

```apt install python3 python3-gi python3-pyudev python3-xdg jstest-gtk```

Other distros may use slightly different names for the same packages.

