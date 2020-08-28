# Oversteer - Steering Wheel Manager for Linux

https://github.com/berarma/oversteer

Oversteer is an application to configure Logitech Wheels.

Features (when supported by the device):
 - Change emulation mode.
 - Change rotation range.
 - Combine accelerator/brakes pedals for games that use just one axis.
 - Change autocentering force strength.
 - Change force feedback gain.
 - Device configuration profiles.
 - Fix system permissions to access all device features.
 - Overlay window to display/configure range.
 - Use wheel buttons to configure range.

Additional features when using [new-lg4ff](https://github.com/berarma/new-lg4ff):
 - Combine accelerator/clutch pedals (for flight simulators).
 - Change global force feedback gain.
 - Change each conditional force feedback effect type gain.
 - FFBmeter to monitor FFB clipping using wheel leds or overlay window.

This software supports the same wheel models supported by the Logitech Linux
driver:
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
 - Experimental support for the Thrustmaster T300RS wheel when using https://github.com/Kimplul/hid-tmff2.

I can test only on a Logitech G29 Driving Force. Please, report your results
with other devices.

Use at your own risk. Suggestions, bugs and pull requests welcome.

## Installation

### Arch

There's an AUR package kindly created by DNModder.

[Install](https://wiki.archlinux.org/index.php/Arch_User_Repository#Installing_packages) the [Oversteer](https://aur.archlinux.org/packages/oversteer/) package.

### Gentoo

There's an ebuild created by gripped [here](https://github.com/gripped/Logitech-wheel-ebuilds)

### Other distributions

#### Requirements

You can install all dependencies on Debian systems with the following command
(I'm using the meson package in Buster backports):

`apt install python3 python3-gi python3-pyudev python3-xdg python3-evdev gettext meson appstream-util desktop-file-utils`

You can install all dependencies on Fedora systems with the following command:

`dnf install python3 python3-gobject python3-pyudev python3-pyxdg python3-libevdev gettext meson appstream desktop-file-utils`

In other distributions use the available tools to install the packages that
will have similar names.

#### Permissions

The access to some device features might be restricted by permissions. If
that's the case, Oversteer will ask to install a udev rule file for the
Logitech wheels that gives permissions to access the device settings to any
user.

#### Build and install

Build:

```
meson build
ninja -C build
```

Trying it without installing:

`ninja -C build run`

Installing (needs administration rights):

`sudo ninja -C build install`

Uninstalling (needs administration rights):

`sudo ninja -C build uninstall`

## Using it

Oversteer can be launched as any desktop application.

It's also possible to use it from the console. Type `oversteer --help` to see
the command line help.

You can configure game launchers to run oversteer to load a profile or change
settings so that it automatically configures the wheel when the game runs.

@Leillo1975 has kindly created a [video explaining the basics of Oversteer
(Spanish)](https://www.youtube.com/watch?v=WdIV1FOkFsw).

## Updating translations (for translators)

```
ninja -C build oversteer-pot
ninja -C build oversteer-update-po
```

## Contributing

We could all greatly benefit from your help as with any other free software
project.

Reports about what works and what not on different devices and systems are very
welcome. You can also help by contributing specific notes for your distro, or
doing the packaging work and everything else.

## Disclaimer

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
