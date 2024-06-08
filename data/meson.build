app_id = 'io.github.berarma.Oversteer'

desktop_conf = configuration_data()
desktop_conf.set('bindir', join_paths(prefix, get_option('bindir')))

tmp_desktop_file = configure_file(
  input: app_id + '.desktop.in',
  output: app_id + '.desktop.tmp',
  configuration: desktop_conf
)

desktop_file = i18n.merge_file(
  input: tmp_desktop_file,
  output: app_id + '.desktop',
  type: 'desktop',
  po_dir: '../po',
  install: true,
  install_dir: join_paths(get_option('datadir'), 'applications')
)

appstream_file = i18n.merge_file(
  input: app_id + '.appdata.xml.in',
  output: app_id + '.appdata.xml',
  po_dir: '../po',
  install: true,
  install_dir: join_paths(get_option('datadir'), 'metainfo')
)

icondir = join_paths(get_option('datadir'), 'icons/hicolor/scalable/apps')
install_data(app_id + '.svg',
  install_dir: icondir
)

install_subdir('udev',
  install_dir: udev_rules_dir,
  strip_directory: true
)

# ---- Tests ----

appstream_util = find_program('appstream-util', required: false)
if appstream_util.found()
  test('Validate appstream file', appstream_util,
    args: ['validate-relax', appstream_file]
  )
endif

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils,
    args: [desktop_file]
  )
endif
