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

if __name__ == "__main__":
    # Argument parsing module.
    # https://docs.python.org/3/library/argparse.html
    from argparse import ArgumentParser
    argumentParser = ArgumentParser(
        description='''
Print the version number from the assets/Version.ini file in a key=value format
for a GitHub workflow output.'''
    )
    argumentParser.add_argument(
        "key", type=str, default="version_number", help=
        'Key name. Default: version_number')
    arguments = argumentParser.parse_args()
    print(f'{arguments.key}={ini_version()}')
