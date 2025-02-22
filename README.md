# Oversteer - Steering Wheel Manager for Linux

<p align="center">
  <img src="data/oversteer-readme.png">
</p>

<a href="https://repology.org/project/unit/versions">
    <img src="https://repology.org/badge/vertical-allrepos/oversteer.svg" alt="Packaging status" align="right" style="margin-left:2em;">
</a>

[_Oversteer_](https://github.com/berarma/oversteer) manages steering wheels on
Linux using the features provided by the loaded modules. It doesn't provide
hardware support, you'll still need a driver module that enables the hardware
on Linux.

Most wheels will work but won't have FFB without specific drivers that support
that feature.

I can test only on a Logitech G29 Driving Force. Please, report your
results with other devices. More wheel models will be added to this list
as they are requested.

__Use at your own risk. Suggestions, bugs and pull requests welcome.__

## Supported devices

_Oversteer_ maintains a list of known wheel devices. If your wheel isn't
recognized, please contact me.

This section lists devices currently recognized. Being in this list doesn't
imply good hardware support. __When thinking about buying a wheel don't rely
solely on the information here__.

_Oversteer_ recognizes the following Logitech wheels which are supported by the
default in-kernel module:

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
- G29 Driving Force Racing Wheel (PS3 mode)
- G920 Driving Force Racing Wheel
- Logitech G923 for XBox (since Linux 6.3)
- OpenFFBoard, (https://github.com/Ultrawipf/OpenFFBoard).

Wheels using the Logitech driver (except XBOX/PC versions) can get improved
support using [new-lg4ff](https://github.com/berarma/new-lg4ff), with more
effects and features. Some games won't have full FFB without it.

The following wheels will need custom driver modules for FFB support.
These drivers are still being worked on. **(I'm NOT claiming they will fully
work. Please, check the related projects for more information.)**:

- Logitech G923 for PS/PC with [new-lg4ff](https://github.com/berarma/new-lg4ff).
- Thrustmaster T150 with [t150_driver](https://github.com/scarburato/t150_driver).
- Thrustmaster TMX Force Feedback with [t150_driver](https://github.com/scarburato/t150_driver).
- Thrustmaster T300 RS with [hid-tmff2](https://github.com/Kimplul/hid-tmff2).
- Thrustmaster T248 with [hid-tmff2](https://github.com/Kimplul/hid-tmff2).
- Thrustmaster TS-XW Racer with [hid-tmff2](https://github.com/Kimplul/hid-tmff2).
- FANATEC CSL Elite Wheel Base with [hid-fanatecff](https://github.com/gotzl/hid-fanatecff).
- FANATEC CSL Elite Wheel Base PS4 with [hid-fanatecff](https://github.com/gotzl/hid-fanatecff).
- FANATEC ClubSport Wheel Base V2 with [hid-fanatecff](https://github.com/gotzl/hid-fanatecff).
- FANATEC ClubSport Wheel Base V2.5 with [hid-fanatecff](https://github.com/gotzl/hid-fanatecff).
- FANATEC Podium Wheel Base DD1/DD2 with [hid-fanatecff](https://github.com/gotzl/hid-fanatecff).
- FANATEC CSL DD / GT DD Pro Wheel with [hid-fanatecff](https://github.com/gotzl/hid-fanatecff).

These wheels are recognized but don't have driver support (Force Feedback and
other features won't work):

- Thrustmaster Force Feedback Racing Wheel
- Thrustmaster TX Racing Wheel
- Thrustmaster T500 RS
- Thrustmaster T80
- Thrustmaster Ferrari 458


## Features

When supported by the device and the driver:

- Change rotation range.
- Change emulation/working modes.
- Combine accelerator/brakes pedals for games that use just one axis.
- Change autocentering force strength.
- Change force feedback gain.
- Device configuration profiles.
- Overlay window to display/configure range.
- Use wheel buttons to configure range.
- Hardware performance testing.
- Combine accelerator/clutch pedals. Useful for flight
  simulators. (Not supported with in-kernel modules)
- Change global force feedback gain. (Not supported with in-kernel modules)
- Change each conditional force feedback effect type gain. (Not supported with in-kernel modules)
- FFBmeter to monitor FFB clipping using wheel leds or overlay
  window. (Not supported with in-kernel modules)

## Installation

DISCLAIMER: When running commands starting with `sudo` you're requesting admin
rights to perform the operation. These commands will make changes to your
system that should only performed by a system administrator or someone knowing
what they're doing.

### Arch

Darvin Delgado (@DNModder) has kindly created an [AUR
package](https://aur.archlinux.org/packages/oversteer/). Install following
the [Arch Wiki
instructions](https://wiki.archlinux.org/index.php/Arch_User_Repository#Installing_packages).

### Gentoo

@gripped has kindly created a [Gentoo ebuild](https://github.com/gripped/Logitech-wheel-ebuilds).

### Flathub

Joshua John (@jo5huajohn) has kindly made a [Flatpak
package](https://flathub.org/apps/io.github.berarma.Oversteer) available at
Flathub.

#### Permissions

After installing the Flatpak package, permission files have to be installed manually.

Copy the contents of
[https://github.com/berarma/oversteer/tree/master/data/udev](https://github.com/berarma/oversteer/tree/master/data/udev)
into `/usr/lib/udev/rules.d`.

If you're using the terminal, these commands will install the permission files:

```
sudo wget https://raw.githubusercontent.com/berarma/oversteer/refs/heads/master/data/udev/99-fanatec-wheel-perms.rules -P /usr/lib/udev/rules.d/
sudo wget https://raw.githubusercontent.com/berarma/oversteer/refs/heads/master/data/udev/99-logitech-wheel-perms.rules -P /usr/lib/udev/rules.d/
sudo wget https://raw.githubusercontent.com/berarma/oversteer/refs/heads/master/data/udev/99-thrustmaster-wheel-perms.rules -P /usr/lib/udev/rules.d/
```

Restart your computer, or reload udev rules with command:

`sudo udevadm control --reload-rules && sudo udevadm trigger`.

### Other distributions

#### Requirements

Install all dependencies on Debian systems with the following command:

`sudo apt git install python3 python3-distutils python3-gi python3-gi-cairo
python3-pyudev python3-xdg python3-evdev gettext meson appstream-util
desktop-file-utils python3-matplotlib python3-scipy`

Install all dependencies on Fedora systems with the following command:

`sudo dnf git install python3 python3-distutils-extra python3-gobject
python3-pyudev python3-pyxdg python3-evdev gettext meson appstream
desktop-file-utils python3-matplotlib-gtk3 python3-scipy libappstream-glib`

Install all dependencies on OpenSUSE systems with the following command:

`sudo zypper in git python3 python3-distutils-extra python3-gobject
python3-pyudev python3-pyxdg python3-evdev meson AppStream desktop-file-utils
python3-matplotlib-gtk3 python3-scipy gettext-tools`

For other distributions, use your package manager to find and install the
equivalent packages.

#### Permissions

Accessing the wheel settings requires some permissions.

**_Oversteer_ will automatically install udev rules to grant these permissions
to any user in the system after a reboot.**

By default, the udev rules will be installed at
`/usr/local/lib/udev/rules.d` when installing to prefix `/usr/local` or
`/lib/udev/rules.d` when installing to any other prefix. The location can
be changed using meson option `udev_rules_dir` but it shouldn't be
required except maybe for packagers.

Older rules might be already installed at `/etc/udev/rules.d` or
`/lib/udev/rules.d`. You may need to remove these files manually in case
you're experiencing issues with permissions.

The installed udev rules files will have these names:

- `99-fanatec-wheel-perms.rules`
- `99-logitech-wheel-perms.rules`
- `99-thrustmaster-wheel-perms.rules`

#### Build and install

Start by downloading `Oversteer` and change your working directory to it. It
could be a release package or the master branch.

```
git clone https://github.com/berarma/oversteer.git
cd oversteer
```

Prepare build system:

```shell
meson setup build
cd build
```

Installing (needs administration rights):

`ninja install`

A reboot will be needed to reload the newly installed udev rules.
Alternatively, running the command `udevadm control --reload-rules && udevadm
trigger` will do the same.

#### Uninstalling

Run these commands inside the project directory to uninstall:

```shell
cd build
ninja uninstall
```

#### Updating

To avoid leaving old files behind, it's recommended to always uninstall the old
version first, then install the new version.

Follow the uninstall instructions for the old version, then follow the install
instructions for the new version.

## Using it

_Oversteer_ can be launched as any desktop application. It doesn't need to
be running for the settings to remain changed, but some features require
it.

It can also be used from the console to change wheel settings. Run
`oversteer --help` to see the command line help.

Leillo1975 has kindly created a [video explaining the basics of Oversteer
(Spanish)](https://www.youtube.com/watch?v=WdIV1FOkFsw).

### Using it as a companion app to your games

You can configure game launchers to run _Oversteer_ and load a profile or change
settings so that it automatically configures the wheel when the game runs. When
the game exits the app will close too. Please, refer to the command line help
for more info.

It can also stop before the game runs so you can change some settings manually
each time. This can be done from the command line or from a setting in the UI.

An example that would work for any Steam game would be:

`oversteer -p myprofile -g "%command%"`

## Known issues

- Most drivers don't support Global Gain and Autocenter settings, only
  `new-lg4ff` for now. The Linux API is used instead when they aren't
  available. If this happens, Oversteer has to reset their values everytime it
  starts. Also, games will be able to override these settings.

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
