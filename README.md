# Oversteer - Steering Wheel Manager for Linux [![Packaging status](https://repology.org/badge/tiny-repos/oversteer.svg)](https://repology.org/project/oversteer/versions)

[https://github.com/berarma/oversteer]

This is an application to configure steering wheels on Linux. It doesn't
provide direct hardware support, you'll still need a driver module that
provides the hardware support.

Oversteer recognizes the following Logitech wheels fully supported the default
kernel module:

- Wingman Formula GP
- Wingman Formula Force GP
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

The G923 models is not supported yet by the Logitech module but there's some
work going on to get them supported. [Patch for PS4
version](https://github.com/berarma/new-lg4ff/pull/50) and [patch for XBox
version](https://patchwork.kernel.org/project/linux-input/list/?series=489571).

Additionally, more features are available for these wheels when using
[new-lg4ff](https://github.com/berarma/new-lg4ff) where possible. Not supported
by Logitech G920 and G923 XBox version.

These other wheels need custom driver modules that are still being worked on:

- Thrustmaster T150 with [https://github.com/scarburato/t150_driver].
- Thrustmaster T300RS with [https://github.com/Kimplul/hid-tmff2].
- Thrustmaster T500RS with [https://github.com/Kimplul/hid-tmff2].
- FANATEC CSL Elite Wheel Base with [https://github.com/gotzl/hid-fanatecff].
- FANATEC CSL Elite Wheel Base PS4 with [https://github.com/gotzl/hid-fanatecff].
- FANATEC ClubSport Wheel Base V2 with [https://github.com/gotzl/hid-fanatecff].
- FANATEC ClubSport Wheel Base V2.5 with [https://github.com/gotzl/hid-fanatecff].
- FANATEC Podium Wheel Base DD1 with [https://github.com/gotzl/hid-fanatecff].

The features available on these wheels will depend on the state of the driver.

Features (when supported by the device and the driver):

- Change emulation mode.
- Change rotation range.
- Combine accelerator/brakes pedals for games that use just one axis.
- Change autocentering force strength.
- Change force feedback gain.
- Device configuration profiles.
- Fix system permissions to access all device features.
- Overlay window to display/configure range.
- Use wheel buttons to configure range.
- Hardware performance testing.
- (only new-lg4ff) Combine accelerator/clutch pedals, useful for flight
  simulators.
- (only new-lg4ff) Change global force feedback gain (with new-lg4ff).
- (only new-lg4ff) Change each conditional force feedback effect type gain.
- (only new-lg4ff) FFBmeter to monitor FFB clipping using wheel leds or overlay
  window.

I can test only on a Logitech G29 Driving Force. Please, report your results
with other devices.

More wheel models will be added to this list as they are requested.

Use at your own risk. Suggestions, bugs and pull requests welcome.

## Installation

[![Packaging status](https://repology.org/badge/vertical-allrepos/oversteer.svg)](https://repology.org/project/oversteer/versions)

### Arch

DNModder has created an [AUR
package](https://aur.archlinux.org/packages/oversteer/). Follow [install
instructions](https://wiki.archlinux.org/index.php/Arch_User_Repository#Installing_packages).

### Gentoo

gripped has created a [Gentoo ebuild](https://github.com/gripped/Logitech-wheel-ebuilds).

### Other distributions

#### Requirements

You can install all dependencies on Debian systems with the following command
(I'm using the meson package in Buster backports):

`apt install python3 python3-distutils python3-gi python3-pyudev python3-xdg
python3-evdev gettext meson appstream-util desktop-file-utils
python3-matplotlib python3-scipy`

You can install all dependencies on Fedora systems with the following command:

`dnf install python3 python3-distutils python3-gobject python3-pyudev
python3-pyxdg python3-evdev gettext meson appstream desktop-file-utils
python3-matplotlib-gtk3 python3-scipy`

In other distributions, use the available tools to install the packages that
will have similar names.

#### Permissions

The access to some device features might be restricted by permissions. If
that's the case, Oversteer will ask to install a udev rule file that gives
permissions to access the device settings to any user.

#### Build and install

Prepare build system:

```shell
meson build
cd build
```

Installing (needs administration rights):

`ninja install`

Uninstalling (needs administration rights):

`ninja uninstall`

Updating should be done by first uninstalling the previous version, updating
the code, then doing the full procedure again to install.

## Using it

Oversteer can be launched as any desktop application.

It's also possible to use it from the console. Type `oversteer --help` to see
the command line help.

Leillo1975 has kindly created a [video explaining the basics of Oversteer
(Spanish)](https://www.youtube.com/watch?v=WdIV1FOkFsw).

### Using it as a companion app to your games

You can configure game launchers to run oversteer and load a profile or change
settings so that it automatically configures the wheel when the game runs. When
the game exits the app will close too. Please, refer to the command line help
for more info.

It can also stop before the game runs so you can change some settings manually
each time. This can be done from the command line or from a setting in the UI.

An example that would work for any Steam game would be:

`oversteer -p myprofile -g "%command%"`

## Updating translations (for translators)

From the project root directory:

```shell
ninja oversteer-pot
ninja oversteer-update-po
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
