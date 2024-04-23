# Standard library imports, in alphabetical order.
#
# Date and time module.
# https://docs.python.org/3/library/datetime.html#datetime-objects
# https://docs.python.org/3/library/datetime.html#datetime.datetime.astimezone
from datetime import datetime
#
# Email utilities, used to parse the Date header from the releases data API.
# https://docs.python.org/3/library/email.utils.html#email.utils.parsedate_to_datetime
from email.utils import parsedate_to_datetime
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
# Temporary file module.
# https://docs.python.org/3/library/tempfile.html
from tempfile import NamedTemporaryFile

from tkinter import StringVar


#
# Subprocess management module, used to launch a downloaded installer.
# https://docs.python.org/3/library/subprocess.html
import subprocess
#
# Multi-threading module.
# https://docs.python.org/3/library/threading.html
from threading import Thread, Lock
#
# URL parsing module.
# https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urlparse
from urllib.parse import urlparse
#
# PIP modules, in alphabetic order.
#
# HTTP request module.
# https://docs.python-requests.org
import requests
# -   Downloading in a stream so that progress can be monitored.
#     https://docs.python-requests.org/en/latest/user/advanced/#body-content-workflow
#     https://docs.python-requests.org/en/latest/api/#requests.Response.iter_content
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

REQUEST_HEADERS_BASE = {"X-GitHub-Api-Version": "2022-11-28"}
REQUEST_HEADERS_JSON = {
    **REQUEST_HEADERS_BASE, "Accept": "application/vnd.github+json"}
REQUEST_HEADERS_BINARY = {
    **REQUEST_HEADERS_BASE, "Accept": "application/octet-stream"}
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

        self._requestAgentHeader = (
            {USER_AGENT_HEADER: App().name + USER_AGENT_SUFFIX}
            if App().userAgentHeader else {} )

        self._releasesStartLock = Lock()
        self._releasesDataLock = Lock()
        with self._releasesDataLock:
            self._lastFetch = None
        self._releasesThread = None

        self.lastFetchMessage = StringVar()

        self._installerPID = None

        self._started = False
    
    @property
    def installerPID(self):
        return self._installerPID

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
            # self._analyse_releases()

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
                self._set_last_fetch_from_release_headers()
                if self._lastFetch is None and self._releasesRawPath.exists():
                    # Fall back to the modified date of the raw retrieval file,
                    # if any.
                    logger.info("Last fetch set from modified time.")
                    self._lastFetch = datetime.fromtimestamp(
                        self._releasesRawPath.stat().st_mtime)
            self.lastFetchMessage.set(
                "Never" if self._lastFetch is None else
                self._lastFetch.strftime("%c"))
        return self._lastFetch
    
    def _set_last_fetch_from_release_headers(self):
        if not self._releasesHeadersPath.is_file():
            self._lastFetch = None
            return

        headers = json.loads(self._releasesHeadersPath.read_text())
        try:
            value = headers[DATE_HEADER]
            # TOTH https://stackoverflow.com/a/1472336/7657675
            self._lastFetch = parsedate_to_datetime(value).astimezone()
            logger.info(
                "Last fetch set from stored header"
                f' "{DATE_HEADER}": "{value}".')
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
        logger.info(f"Fetching release data from {url} ...")

        downloadPath = None
        responseHeaders = None
        with requests.get(
            url, stream=True,
            headers={**REQUEST_HEADERS_JSON, **self._requestAgentHeader}
        ) as response:
            status = response.status_code
            if status < 200 or status >= 300:
                logger.error(
                    f'Fetch failed {status} "{response.reason}"'
                    f' {response.text}')
            else:
                with NamedTemporaryFile(
                    mode='wb', delete=False, dir=App().updateDirectory,
                    prefix="tmp" + self._releasesRawPath.stem,
                    suffix=self._releasesRawPath.suffix
                ) as file:
                    downloadPath = Path(file.name)
                    responseHeaders = response.headers
                    # TOTH For loop with iter_content.
                    # https://stackoverflow.com/q/39846671/7657675
                    for content in response.iter_content(1024):
                        file.write(content)
                        logger.info(len(content))

        if downloadPath is None:
            return

        with self._releasesDataLock:
            self._lastFetch = None
            downloadPath.replace(self._releasesRawPath)
            self._releasesIndentedPath.write_text(json.dumps(
                json.loads(self._releasesRawPath.read_bytes()), indent=4))
            self._releasesHeadersPath.write_text(json.dumps(
                dict(responseHeaders), indent=4))
        logger.info(f'lastFetch {self.lastFetch}')
            # Preceding line instantiates a dict because the Requests library
            # uses a custom type, like CaseInsensitiveDictionary, that hasn't
            # implemented JSON encodability.

    def _analyse_releases(self):
        releases = None
        with self._releasesDataLock:
            if self._releasesRawPath.is_file():
                with self._releasesRawPath.open("rb") as file:
                    releases = json.load(file) # Will be an array of objects.
        index = self._index_of_last_published(releases)
        if index is None:
            return
        release = releases[index]
        releaseName = release['name']
        assetName = None
        assetID = None
        assetSize = None
        for asset in release["assets"]:
            name = asset["name"]
            if (
                name.endswith(".exe")
                and name.startswith("-".join((App().name, "Installer")))
            ):
                assetName = name
                assetID = f'{asset["id"]}'
                assetSize = asset['size']
                break

        installerPath = Path(App().updateDirectory, assetName)
        if (not installerPath.is_file()) and assetID is not None:
            url = "/".join((App().releasesAPI, "assets", assetID))
            logger.info(f"Fetching latest installer from {url} ...")
            with requests.get(
                url, stream=True,
                headers={**REQUEST_HEADERS_BINARY, **self._requestAgentHeader}
            ) as response:
                status = response.status_code
                if status < 200 or status >= 300:
                    logger.error(
                        f'Fetch failed {status} "{response.reason}"'
                        f' {response.text}')
                else:
                    # TOTH For loop with iter_content.
                    # https://stackoverflow.com/q/39846671/7657675
                    with installerPath.open('wb') as file:
                        for content in response.iter_content(8 * 1024 * 1024):
                            file.write(content)
                            logger.info(len(content))

        if installerPath.is_file():
            logger.info(f'Launching installer "{installerPath}" ...')
            # TOTH start a process that won't be terminated by termination of
            # the parent.  
            # https://stackoverflow.com/a/39715066/7657675
            popen = subprocess.Popen(
                (installerPath,)
                , creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP
                    | subprocess.DETACHED_PROCESS )
            )
            self._installerPID = popen.pid

    def _index_of_last_published(self, releases):
        if releases is None:
            return None
        
        indexLastPublished = None
        timeLastPublished = None
        for index, release in enumerate(releases):
            publishedStr = release['published_at']
            #
            # Ending with a Z, to indicate zero time zone offset, is valid ISO
            # 8601 format but seems to be rejected by Python 3.10 on Windows.
            if publishedStr[-1] == 'Z':
                publishedStr = publishedStr[:-1] + "+00:00"
            logger.info(publishedStr)
            published = datetime.fromisoformat(publishedStr)
            if indexLastPublished is None:
                logger.info(f'releases[{index}] {published.astimezone()}')
            else:
                logger.info(
                    f'releases[{index}] {published.astimezone()}'
                    f' > {timeLastPublished.astimezone()}'
                    f' {published < timeLastPublished}')
                if published < timeLastPublished:
                    continue
            indexLastPublished = index
            timeLastPublished = published

        # ToDo test with more than one release.

        return indexLastPublished
