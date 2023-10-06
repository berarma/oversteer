project('oversteer',
  version: '0.7.3',
  meson_version: '>= 0.56.0'
)

i18n = import('i18n')
pymod = import('python')
prefix = get_option('prefix')
pkgdatadir = join_paths(prefix, get_option('datadir'), meson.project_name())
py_installation = pymod.find_installation(get_option('python'))
py_path = py_installation.get_install_dir()

python3_required_modules = ['gi', 'pyudev', 'xdg', 'evdev', 'gettext', 'matplotlib', 'scipy', 'numpy']
foreach p : python3_required_modules
  script = 'import importlib.util; import sys; exit(1) if importlib.util.find_spec(\''+ p +'\') is None else exit(0)'
  if run_command(py_installation, '-c', script, check: true).returncode() != 0
    error('Required Python3 module \'' + p + '\' not found')
  endif
endforeach

udev_rules_dir = get_option('udev_rules_dir')
if udev_rules_dir == ''
  if prefix == '/usr/local'
    udev_rules_dir = '/usr/local/lib/udev/rules.d'
  else
    udev_dep = dependency('udev')
    udev_rules_dir = udev_dep.get_pkgconfig_variable('udevdir') + '/rules.d'
  endif
elif udev_rules_dir == 'packed'
  udev_rules_dir = pkgdatadir + '/udev'
endif

install_subdir('oversteer', install_dir: py_path)
subdir('data')
subdir('bin')
subdir('po')

meson.add_install_script('scripts/meson_post_install.py')
