project('oversteer',
  version: '0.4.1',
  meson_version: '>= 0.40.0'
)

i18n = import('i18n')
python3 = import('python3')
prefix = get_option('prefix')
pkgdatadir = join_paths(prefix, get_option('datadir'), meson.project_name())
pythondir = python3.sysconfig_path('purelib')

install_subdir('oversteer', install_dir: pythondir)
subdir('data')
subdir('bin')
subdir('po')

meson.add_install_script('scripts/meson_post_install.py')
