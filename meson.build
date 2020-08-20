project('oversteer',
  version: '0.4.1',
  meson_version: '>= 0.50.0'
)

i18n = import('i18n')
pymod = import('python')
prefix = get_option('prefix')
pkgdatadir = join_paths(prefix, get_option('datadir'), meson.project_name())
py_installation = pymod.find_installation('python3')
py_path = py_installation.get_path('purelib')

install_subdir('oversteer', install_dir: py_path)
subdir('data')
subdir('bin')
subdir('po')

meson.add_install_script('scripts/meson_post_install.py')
