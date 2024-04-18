# Standard library imports.
#
# Object oriented path handling.
# https://docs.python.org/3/library/pathlib.html
from pathlib import Path
#
# URL parsing module.
# https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urlparse
from urllib.parse import urlunparse
#
# Local imports.
#
from src.singleton_meta import Singleton
#
# PIP modules.
#
# https://platformdirs.readthedocs.io/en/latest/api.html
from platformdirs import user_data_dir
#
# Local imports.
#
from src.utils.readini import get_ini_value

APP_NAME = "FaceCommander"
APP_AUTHOR = "AceCentre"

LOG_FILENAME = "log.txt"

VERSION_INI_FILE = ("assets", "Version.ini")
VERSION_INI_SECTION = "Release"
VERSION_INI_KEY = "VersionNumber"

PROFILES_SUBDIRECTORY = ("configs",)

HOME_PAGE_UNPARSE = (
    "https", "github.com", "/".join((APP_AUTHOR, APP_NAME)) , None, None, None)

class App(metaclass=Singleton):

    def __init__(self):
        self._name = APP_NAME

        self._installationRoot = Path(__file__).parents[1]
        self._dataRoot = None

        self._version = None

        self._logPath = None
        self._profilesDirectory = None
        self._builtInProfilesDirectory = None

        self._homePageURL = urlunparse(HOME_PAGE_UNPARSE)

    @property
    def name(self):
        return self._name

    @property
    def version(self):
        if self._version is None:
            self._version = get_ini_value(
                Path(self.installationRoot, *VERSION_INI_FILE),
                VERSION_INI_SECTION, VERSION_INI_KEY)
        return self._version

    @property
    def installationRoot(self):
        return self._installationRoot
    
    @property
    def dataRoot(self):
        if self._dataRoot is None:
            self._dataRoot = Path(user_data_dir(
                appname=APP_NAME, appauthor=APP_AUTHOR))
        return self._dataRoot
    
    @property
    def profilesDirectory(self):
        if self._profilesDirectory is None:
            self._profilesDirectory = Path(
                self.dataRoot, *PROFILES_SUBDIRECTORY)
        return self._profilesDirectory

    @property
    def builtInProfilesDirectory(self):
        if self._builtInProfilesDirectory is None:
            self._builtInProfilesDirectory = Path(
                self.installationRoot, *PROFILES_SUBDIRECTORY)
        return self._builtInProfilesDirectory

    @property
    def logPath(self):
        if self._logPath is None:
            self._logPath = Path(self.dataRoot, LOG_FILENAME)
        return self._logPath
    
    @property
    def homePageURL(self):
        return self._homePageURL