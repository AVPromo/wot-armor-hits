# -*- coding: utf-8 -*-
"""Build the .wotmod package (and optionally install it into the game).

Run with the game's Python version (2.7):
    C:\\Python27\\python.exe build.py            -> build/<id>_<version>.wotmod
    C:\\Python27\\python.exe build.py --install  -> also copy into the game mods folder
"""
import glob
import os
import py_compile
import re
import shutil
import sys
import tempfile
import zipfile
from xml.sax.saxutils import escape

MOD_ID = 'sagtary.armor_hits'
MOD_NAME = 'Armor Hits by Sagtary'
MOD_DESCRIPTION = 'Hangar viewer of hits received and dealt in battle.'
MOD_SCRIPT = 'mod_sagtary_armor_hits'

GAME_DIR = os.environ.get('WOT_DIR', r'D:\programs\World_of_Tanks_EU')

ROOT = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.join(ROOT, 'src', 'gui', 'mods')
# The entry module the game loads; it holds __version__.
SOURCE = os.path.join(SOURCE_DIR, MOD_SCRIPT + '.py')
# Files under resources/ go to res/ in the package as they are (icons, textures, ...).
RESOURCES_DIR = os.path.join(ROOT, 'resources')
BUILD_DIR = os.path.join(ROOT, 'build')
PACKAGE_SCRIPT_DIR = 'res/scripts/client/gui/mods/'
PACKAGE_RESOURCES_DIR = 'res/'

META_XML = """<root>
  <id>{id}</id>
  <version>{version}</version>
  <name>{name}</name>
  <description>{description}</description>
</root>
"""


def read_version():
    with open(SOURCE) as f:
        match = re.search(r"^__version__ = '([^']+)'", f.read(), re.M)
    if not match:
        sys.exit('__version__ not found in ' + SOURCE)
    return match.group(1)


def read_game_version():
    # The mods folder is named after the client version: <version> v.2.4.1.0 #977 </version>.
    path = os.path.join(GAME_DIR, 'version.xml')
    with open(path) as f:
        match = re.search(r'<version>\s*v\.([\d.]+)', f.read())
    if not match:
        sys.exit('version not found in ' + path)
    return match.group(1)


def files_under(directory, extension=''):
    # Every file under directory as a path relative to it with '/' separators, sorted.
    found = []
    for current, _, names in os.walk(directory):
        for name in names:
            if name.endswith(extension):
                found.append(os.path.relpath(os.path.join(current, name), directory).replace(os.sep, '/'))
    return sorted(found)


def compile_scripts(tmp_dir):
    # {package path: bytecode}.
    compiled = {}
    for relative in files_under(SOURCE_DIR, '.py'):
        pyc = os.path.join(tmp_dir, relative.replace('/', '_') + 'c')
        # dfile keeps the local source path out of tracebacks in game.log.
        py_compile.compile(os.path.join(SOURCE_DIR, relative), cfile=pyc, dfile='gui/mods/' + relative, doraise=True)
        with open(pyc, 'rb') as f:
            compiled[PACKAGE_SCRIPT_DIR + relative + 'c'] = f.read()
    return compiled


def read_resources():
    # {package path: content}.
    resources = {}
    if os.path.isdir(RESOURCES_DIR):
        for relative in files_under(RESOURCES_DIR):
            with open(os.path.join(RESOURCES_DIR, relative), 'rb') as f:
                resources[PACKAGE_RESOURCES_DIR + relative] = f.read()
    return resources


def write_package(path, version, files):
    meta = META_XML.format(id=MOD_ID, version=version, name=escape(MOD_NAME), description=escape(MOD_DESCRIPTION))
    # The game expects an uncompressed zip with explicit directory entries.
    directories = set()
    for name in files:
        parts = name.split('/')[:-1]
        directories.update('/'.join(parts[:i]) + '/' for i in range(1, len(parts) + 1))
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_STORED) as z:
        z.writestr('meta.xml', meta)
        for directory in sorted(directories):
            z.writestr(directory, '')
        for name in sorted(files):
            z.writestr(name, files[name])


def install(package):
    mods_dir = os.path.join(GAME_DIR, 'mods', read_game_version())
    if not os.path.isdir(mods_dir):
        sys.exit('mods folder not found: ' + mods_dir)
    for old in glob.glob(os.path.join(mods_dir, MOD_ID + '_*.wotmod')):
        print('remove  ' + old)
        os.remove(old)
    shutil.copy2(package, mods_dir)
    print('install ' + os.path.join(mods_dir, os.path.basename(package)))


def main():
    if sys.version_info[:2] != (2, 7):
        sys.exit('Run with Python 2.7 (the game bytecode version), got ' + sys.version.split()[0])

    version = read_version()
    tmp_dir = tempfile.mkdtemp()
    try:
        files = compile_scripts(tmp_dir)
    finally:
        shutil.rmtree(tmp_dir)
    files.update(read_resources())

    if not os.path.isdir(BUILD_DIR):
        os.makedirs(BUILD_DIR)
    package = os.path.join(BUILD_DIR, '%s_%s.wotmod' % (MOD_ID, version))
    write_package(package, version, files)
    print('build   ' + package)

    if '--install' in sys.argv[1:]:
        install(package)


if __name__ == '__main__':
    main()
