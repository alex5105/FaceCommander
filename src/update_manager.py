# Standard library imports, in alphabetical order.
#
# Date and time module.
# https://docs.python.org/3/library/datetime.html#datetime-objects
from datetime import datetime
#
# Email utilities, used to parse the Date header from the releases data API.
# https://docs.python.org/3/library/email.utils.html#email.utils.parsedate_to_datetime
from email.utils import parsedate_to_datetime
#
# HTTP module.
# https://docs.python.org/3/library/http.client.html#http.client.HTTPSConnection
from http.client import HTTPSConnection
# Also for reference but without explicit imports.
# https://docs.python.org/3/library/http.client.html#httpresponse-objects
#
# JSON module.
# https://docs.python.org/3/library/json.html
import json
#
# Logging module.
# https://docs.python.org/3/library/logging.html
import logging
#
# Object oriented path handling.
# https://docs.python.org/3/library/pathlib.html
from pathlib import Path
#
# Multi-threading module.
# https://docs.python.org/3/library/threading.html
from threading import Thread, Lock


#
# URL parsing module.
# https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urlparse
# from urllib.parse import urlparse



#
# Local imports.
#
from src.app import App
from src.singleton_meta import Singleton

# TOTH
# https://github.com/sjjhsjjh/captive-web-view/blob/main/harness/command_handler/fetch.py

logger = logging.getLogger("UpdateManager")

RELEASES_RAW_FILENAME = "releases_raw.json"
RELEASES_INDENTED_FILENAME = "releases_indented.json"
RELEASES_HEADERS_FILENAME = "releases_headers.json"

REQUEST_HEADERS_BASE = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}
USER_AGENT_HEADER = "User-Agent"
USER_AGENT_SUFFIX = "-App"
DATE_HEADER = "Date"

class UpdateManager(metaclass=Singleton):

    def __init__(self):
        self._releasesRawPath = App().updateDirectory / RELEASES_RAW_FILENAME
        self._releasesIndentedPath = Path(
            App().updateDirectory, RELEASES_INDENTED_FILENAME)
        self._releasesHeadersPath = Path(
            App().updateDirectory, RELEASES_HEADERS_FILENAME)

        self._releasesStartLock = Lock()
        self._releasesDataLock = Lock()
        with self._releasesDataLock:
            self._lastFetch = None
        self._releasesThread = None

        self._started = False

    def start(self):
        if not self._started:
            self._started = True
            App().updateDirectory.mkdir(parents=True, exist_ok=True)
            #
            # If release data hasn't been fetched, start a thread to fetch it
            # now.
            if self.lastFetch is None:
                self.releases_retrieval(True)
            if self.lastFetch is None:
                logger.info("Release data has never been fetched.")
            else:
                logger.info(
                    f'Release data fetched: {self.lastFetch.strftime("%c")}.')

    def releases_retrieval(self, start=False):
        with self._releasesStartLock:
            # Clean up any finished thread.
            if (
                self._releasesThread is not None
                and not self._releasesThread.is_alive()
            ):
                self._releasesThread.join()
                self._releasesThread = None

            started = False
            if start and self._releasesThread is None:
                self._releasesThread = Thread(target=self._fetch_releases)
                self._releasesThread.start()
                started = True

            return self._releasesThread is not None, started

    @property
    def lastFetch(self):
        with self._releasesDataLock:
            if self._lastFetch is None:
                if self._releasesHeadersPath.is_file():
                    with self._releasesHeadersPath.open() as file:
                        self._set_last_fetch_from_release_headers(file)
                if self._lastFetch is None and self._releasesRawPath.exists():
                    # Fall back to the modified date of the raw retrieval file,
                    # if any.
                    logger.info("Last fetch set from modified time.")
                    self._lastFetch = datetime.fromtimestamp(
                        self._releasesRawPath.stat().st_mtime)
        return self._lastFetch
    
    def _set_last_fetch_from_release_headers(self, file):
        for pair in json.load(file):
            if pair[0] == DATE_HEADER:
                try:
                    # TOTH https://stackoverflow.com/a/1472336/7657675
                    self._lastFetch = (
                        parsedate_to_datetime(pair[1]).astimezone())
                    logger.info(
                        f'Last fetch set from stored header {pair}.')
                    break
                except ValueError as valueError:
                    logger.error(valueError)
                    self._lastFetch = None

    def _fetch_releases(self):
        # References for the request.
        #
        # https://docs.github.com/en/rest/releases/releases?apiVersion=2022-11-28#list-releases-for-a-repository
        #
        # "All API requests must include a valid User-Agent header."
        # https://docs.github.com/en/rest/using-the-rest-api/getting-started-with-the-rest-api?apiVersion=2022-11-28#user-agent

        # "https://api.github.com/repos/AceCentre/FaceCommander/releases"
        # /repos/{owner}/{repo}/releases
        url = App().releasesAPI
        host = url.hostname
        port = 443 if url.port is None else url.port
        logger.info(f"Fetching release information from {url} ...")
        connection = HTTPSConnection(host, port=port)
        connection.connect()
        connection.request('GET', url.path, headers={
            **REQUEST_HEADERS_BASE
            # Comment out the next line to force a 403.
            , USER_AGENT_HEADER: App().name + USER_AGENT_SUFFIX
        })
        response = connection.getresponse()
        logger.info(
            f'Response {response.status} "{response.reason}"'
            f' {response.headers.items()}')
        responseBytes = response.read()
        logger.info(f'Response bytes:{len(responseBytes)}')
        connection.close()

        if response.status < 200 or response.status >= 300:
            logger.error(
                f'Failed to fetch releases information. {responseBytes}')
        else:
            with self._releasesDataLock:
                self._lastFetch = None
                with self._releasesHeadersPath.open("w") as file:
                    json.dump(response.headers.items(), file, indent=4)
                self._releasesRawPath.write_bytes(responseBytes)
                with self._releasesIndentedPath.open("w") as file:
                    json.dump(json.loads(responseBytes), file, indent=4)


        # releases = [{
        #     "name": release.name,
        #     "prerelease": true,
        #     "created_at": "2024-04-16T15:23:39Z",
        #     "published_at": "2024-04-16T15:29:42Z",
        # } for release in responseArray]
