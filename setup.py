from glob import glob
import setuptools
from distutils.command.build import build
import codecs
import logging
import os
from lxml import etree
from babel.messages.pofile import read_po

class Build(build):
    sub_commands = [('compile_catalog', None)] + build.sub_commands

    def run(self):
        translate_desktop_file('data/org.berarma.Oversteer.desktop.in', 'data/org.berarma.Oversteer.desktop', 'locale')
        translate_appdata_file('data/org.berarma.Oversteer.appdata.xml.in', 'data/org.berarma.Oversteer.appdata.xml', 'locale')
        build.run(self)

with open("README.md", "r") as fh:
    long_description = fh.read()

mofiles = []
for mofile in glob('locale/*/*/*.mo'):
    mofiles.append(('share/' + os.path.dirname(mofile), [mofile]))

def extract_glade(fileobj, keywords, comment_tags, options):
    tree = etree.parse(fileobj)
    root = tree.getroot()
    to_translate = []
    for elem in root.iter():
        # do we need to check if the element starts with "gtk-"?
        if elem.get("translatable") == "yes":
            line_no = elem.sourceline
            func_name = None
            message = elem.text
            comment = []
            if elem.get("comments"):
                comment = [elem.get("comments")]
            to_translate.append([line_no, func_name, message, comment])
    return to_translate

def extract_desktop(fileobj, keywords, comment_tags, options):
    # All localestrings from https://specifications.freedesktop.org/desktop-entry-spec/latest/ar01s05.html
    TRANSLATABLE = (
        'Name',
        'GenericName',
        'Comment',
        'Icon',
        'Keywords',
    )

    for lineno, line in enumerate(fileobj, 1):
        if line.startswith(b'[Desktop Entry]'):
            continue

        for t in TRANSLATABLE:
            if not line.startswith(t.encode('utf-8')):
                continue
            else:
                l = line.decode('utf-8')
                comments = []
                key_value = l.split('=', 1)
                key, value = key_value[0:2]

                funcname = key # FIXME: Why can I not assign that name to funcname?
                funcname = ''
                message = value
                comments.append(key)
                yield (lineno, funcname, message.strip(), comments)

def translate_desktop_file(infile, outfile, localedir):
    log = logging.getLogger(__name__)

    infp = codecs.open(infile, 'rb', encoding='utf-8')
    outfp = codecs.open(outfile, 'wb', encoding='utf-8')

    catalogs = get_catalogs(localedir)

    for line in (x.strip() for x in infp):
        log.debug('Found in original (%s): %r', type(line), line)
        # We intend to ignore the first line
        if line.startswith('[Desktop'):
            additional_lines = []
        else:
            additional_lines = []
            # This is a rather primitive approach to generating the translated
            # desktop file.  For example we don't really care about all the
            # keys in the file.  But its simplicity is a feature and we
            # ignore the runtime overhead, because it should only run centrally
            # once.
            key, value = line.split('=', 1)
            log.debug("Found key: %r", key)
            for locale, catalog in catalogs.items():
                translated = catalog.get(value)
                log.debug("Translated %r[%r]=%r: %r (%r)",
                          key, locale, value, translated,
                          translated.string if translated else '')
                if translated and translated.string \
                              and translated.string != value:
                    additional_line = u'{keyword}[{locale}]={translated}'.format(
                                        keyword=key,
                                        locale=locale,
                                        translated=translated.string,
                                    )
                    additional_lines.append(additional_line)
                log.debug("Writing more lines: %s", additional_lines)

        # Write the new file.
        # First the original line found it in the file, then the translations.
        outfp.writelines((outline+'\n' for outline in ([line] + additional_lines)))

def translate_appdata_file(infile, outfile, localedir):
    log = logging.getLogger(__name__)

    catalogs = get_catalogs(localedir)
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(infile, parser)
    root = tree.getroot()
    for elem in root.iter():
        # We remove any possible tailing whitespaces to allow lxml to format the output
        elem.tail = None
        if elem.get("translatable") == "yes":
            elem.attrib.pop("translatable", None)
            elem.attrib.pop("comments", None)  # Are comments allowed?
            message = elem.text
            parent = elem.getparent()
            pos = parent.getchildren().index(elem) + 1
            for locale, catalog in catalogs.items():
                translated = catalog.get(message)
                if translated and translated.string \
                        and translated.string != message:
                    log.debug("Translated [%s]%r: %r (%r)",
                              locale, message, translated, translated.string)
                    tr = etree.Element(elem.tag)
                    attrib = tr.attrib
                    attrib["{http://www.w3.org/XML/1998/namespace}lang"] = str(locale)
                    tr.text = translated.string
                    parent.insert(pos, tr)
    tree.write(outfile, encoding='utf-8', pretty_print=True)

def get_catalogs(localedir):
    # glob in Python 3.5 takes ** syntax
    # pofiles = glob.glob(os.path.join(localedir, '**.po', recursive=True))
    pofiles = [os.path.join(dirpath, f)
               for dirpath, dirnames, files in os.walk(localedir)
               for f in files if f.endswith('.po')]
    logging.debug('Loading %r', pofiles)
    catalogs = {}

    for pofile in pofiles:
        catalog = read_po(open(pofile, 'r'))
        catalogs[catalog.locale] = catalog
        logging.info("Found %d strings for %s", len(catalog), catalog.locale)
        # logging.debug("Strings for %r", catalog, catalog.values())
    if not catalogs:
        logging.warning("Could not find pofiles in %r", pofiles)
    return catalogs

setuptools.setup(
    name = "oversteer",
    version = "0.1.3",
    author = "Bernat Arlandis",
    author_email = "berarma@hotmail.com",
    description = "Steering Wheel Manager",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/berarma/oversteer",
    packages = ['oversteer'],
    package_dir = {'oversteer':'oversteer'},
    include_package_data = True,
    data_files = [
        ( 'share/applications', ['data/org.berarma.Oversteer.desktop']),
        ( 'share/metainfo', ['data/org.berarma.Oversteer.appdata.xml']),
        ( 'share/icons/hicolor/scalable/apps', ['data/org.berarma.Oversteer.svg']),
        ( 'share/oversteer', ['data/udev/99-logitech-wheel-perms.rules']),
    ] + mofiles,
    exclude_package_data = {
        'oversteer': ['locale/*/*/*.po'],
    },
    install_requires = [
        "pygobject",
        "pyudev",
        "pyxdg",
    ],
    setup_requires=[
        "babel",
        "lxml",
    ],
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
        "Development Status :: 3 - Alpha",
    ],
    message_extractors = {
        'oversteer': [
            ('**.py', 'python', None),
            ('**.ui', extract_glade, None),
        ],
        '': [
            ('**.desktop.in', extract_desktop, None),
            ('**.appdata.xml.in', extract_glade, None),
        ],
    },
    cmdclass = {
        'build': Build,
    },
)
