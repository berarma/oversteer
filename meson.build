project('oversteer',
  version: '0.5.0',
  meson_version: '>= 0.50.0'
)

i18n = import('i18n')
pymod = import('python')
prefix = get_option('prefix')
pkgdatadir = join_paths(prefix, get_option('datadir'), meson.project_name())
py_installation = pymod.find_installation('python3')
py_path = py_installation.get_path('purelib')

python3_required_modules = ['gi', 'pyudev', 'xdg', 'evdev', 'gettext', 'matplotlib', 'scipy', 'numpy']
foreach p : python3_required_modules
  script = 'import importlib.util; import sys; exit(1) if importlib.util.find_spec(\''+ p +'\') is None else exit(0)'
  if run_command(py_installation, '-c', script).returncode() != 0
    error('Required Python3 module \'' + p + '\' not found')
  endif
endforeach

install_subdir('oversteer', install_dir: py_path)
subdir('data')
subdir('bin')
subdir('po')

meson.add_install_script('scripts/meson_post_install.py')
