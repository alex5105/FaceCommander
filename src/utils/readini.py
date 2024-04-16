# Standard library imports in alphabetical order.
#
# INI file parser, used to get the version number.
# https://docs.python.org/3/library/configparser.html
from configparser import ConfigParser
#
# Object oriented path handling.
# https://docs.python.org/3/library/pathlib.html
from pathlib import Path

def get_ini_value(iniPath, section, key):
    ini = ConfigParser()
    # Use .read_file() not .read() so that FileNotFoundError is raised if the
    # file doesn't exist.
    ini.read_file(Path(iniPath).open())
    return ini[section][key]

if __name__ == "__main__":
    # Argument parsing module.
    # https://docs.python.org/3/library/argparse.html
    from argparse import ArgumentParser

    argumentParser = ArgumentParser(
        description=
        'Print a value from a .ini file in a key=value format for a GitHub'
        ' workflow output.'
    )
    argumentParser.add_argument(
        "path", metavar="File.ini", type=Path, help='Path of the .ini file.')
    argumentParser.add_argument(
        "section", type=str, help=
        'Within the file, the section name that contains the key.'
        ' Section names are enclosed in square brackets in .ini files, like'
        ' [Release].')
    argumentParser.add_argument(
        "key", type=str, help=
        'Within the section, the key whose value is to be printed.')
    argumentParser.add_argument(
        "alias", type=str, nargs='?', help=
        'Optional key to appear in the output.'
        ' Default is to use the same key that appears in the .ini file.')
    arguments = argumentParser.parse_args()
    print('='.join((
        arguments.key if arguments.alias is None else arguments.alias,
        get_ini_value(arguments.path, arguments.section, arguments.key)
    )))
