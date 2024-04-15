# Standard library imports in alphabetical order.
#
# INI file parser, used to get the version number.
# https://docs.python.org/3/library/configparser.html
from configparser import ConfigParser
#
# Object oriented path handling.
# https://docs.python.org/3/library/pathlib.html
from pathlib import Path

def ini_version():
    versionINIPath = Path(__file__).parents[2] / "assets" / "Version.ini"
    versionINI = ConfigParser()
    versionINI.read(versionINIPath)
    return versionINI['Release']['VersionNumber']

if __name__ == "__main__": print(ini_version())
