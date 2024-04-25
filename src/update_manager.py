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
#
# Subprocess management module, used to launch a downloaded installer.
# https://docs.python.org/3/library/subprocess.html
import subprocess
#
# Multi-threading module. Downloading releases information and installers is
# done on a thread.  
# https://docs.python.org/3/library/threading.html
from threading import Thread, Lock
#
# Sleep function, used for diagnostic options that slow down retrieval
# artificically.  
# https://docs.python.org/3/library/time.html#time.sleep
from time import sleep
#
# Type hints module.
# https://docs.python.org/3/library/typing.html#typing.NamedTuple
from typing import NamedTuple
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

        self._startRetrieveLock = Lock()
        with self._startRetrieveLock:
            self._retrieveThread = None
        self._releasesDataLock = Lock()

        self._stateLock = Lock()
        with self._stateLock:
            self._lastFetchDateTime = None
            self._lastFetchMessage = "Releases information unknown."
            self._retrievedAmount = 0
            self._retrievingSize = 0
            self._installerPath = None
        # retrievingSize semantics are as follows.
        # -   Zero if no retrieval is underway.
        # -   Negative if an indeterminate retrieval is underway.
        # -   Positive if a determinate retrieval is underway.

        self._installerPID = None

        self._started = False
    
    @property
    def state(self):
        with self._stateLock:
            return UpdateState(
                self._lastFetchMessage,
                self._lastFetchDateTime,
                self._retrievedAmount,
                self._retrievingSize,
                self._installerPath
            )
    
    def _set_retrieval_progress(
        self, retrievedAmount, retrievingSize=None, installerPath=None
    ):
        with self._stateLock:
            self._retrievedAmount = retrievedAmount
            if retrievingSize is not None:
                self._retrievingSize = retrievingSize
            if installerPath is not None:
                self._installerPath = installerPath

    @property
    def installerPID(self):
        return self._installerPID

    def start(self):
        if not self._started:
            self._started = True
            App().updateDirectory.mkdir(parents=True, exist_ok=True)
            self.update()

    def update(self):
        retrieveReleaseInformation = False
        # Preceding line might need a CLI override option.


        with self._releasesDataLock:
            lastFetch = self._last_fetch_from_releases_files()
        self._set_last_fetch(lastFetch)
        if lastFetch is None:
            retrieveReleaseInformation = True


        # Near here, if retrieveReleaseInformation is False then check how long
        # ago the last fetch was. If it was far enough in the past then set it
        # to true.



        # Clean up any finished thread.
        with self._startRetrieveLock:
            if (
                self._retrieveThread is not None
                and not self._retrieveThread.is_alive()
            ):
                self._retrieveThread.join()
                self._retrieveThread = None

        if retrieveReleaseInformation:
            with self._startRetrieveLock:
                if self._retrieveThread is None:
                    self._retrieveThread = Thread(target=self._fetch)
                    self._retrieveThread.start()
        else:
            asset = self._asset_to_download()
            logger.info(f'Asset to download {asset}.')
            if asset is not None:
                with self._startRetrieveLock:
                    if self._retrieveThread is None:
                        self._retrieveThread = Thread(
                            target=asset.fetch,
                            args=(
                                self._requestAgentHeader,
                                self._set_retrieval_progress)
                        )
                        self._retrieveThread.start()

    def _last_fetch_from_releases_files(self):
        '''Acquire self._releasesDataLock before calling.'''
        if self._releasesHeadersPath.is_file():
            headers = json.loads(self._releasesHeadersPath.read_text())
            try:
                value = headers[DATE_HEADER]
                logger.info(
                    "Last fetch set from stored header"
                    f' "{DATE_HEADER}": "{value}".')
                # TOTH https://stackoverflow.com/a/1472336/7657675
                return parsedate_to_datetime(value).astimezone()
            except ValueError as valueError:
                logger.error(valueError)

        if self._releasesRawPath.exists():
            # Fall back to the modified date of the raw retrieval file, if any.
            logger.info("Last fetch set from modified time.")
            return datetime.fromtimestamp(self._releasesRawPath.stat().st_mtime)
        
        return None

    def _set_last_fetch(self, lastFetch):
        '''Release self._stateLock before calling.'''
        with self._stateLock:
            self._lastFetchDateTime = lastFetch
            message = ""
            if self._lastFetchDateTime is None:
                message = "Releases information has never been retrieved."
            else:
                description = self._lastFetchDateTime.strftime(r"%c")
                # Near here, could use a timedelta to give a more evocative
                # message like "5 minutes ago".
                message = 'Releases information retrieved ' + description + "."
            logger.info(f'Setting last fetch message "{message}"')
            self._lastFetchMessage = message

        # self.lastFetchMessage.set(message)

    def _fetch(self):
        '''Run as a Thread and don't start more than one.'''
        self._fetch_release_information()
        asset = self._asset_to_download()
        logger.info(f'Asset to download {asset}.')
        if asset is not None:
            asset.fetch(self._requestAgentHeader, self._set_retrieval_progress)

    def _fetch_release_information(self):
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
        self._set_retrieval_progress(0, -1)
        with requests.get(
            url, stream=True,
            headers={**REQUEST_HEADERS_JSON, **self._requestAgentHeader}
        ) as response:
            status = response.status_code
            if status < 200 or status >= 300:
                self._set_retrieval_progress(0, 0)
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
                    retrievedAmount = 0
                    delay = App().releaseInformationDelay
                    for content in response.iter_content(1024):
                        file.write(content)
                        retrievedAmount += len(content)
                        self._set_retrieval_progress(retrievedAmount)
                        logger.info(len(content))
                        if delay > 0:
                            sleep(delay)

        if downloadPath is not None:
            with self._releasesDataLock:
                downloadPath.replace(self._releasesRawPath)
                self._releasesIndentedPath.write_text(json.dumps(
                    json.loads(self._releasesRawPath.read_bytes()), indent=4))
                self._releasesHeadersPath.write_text(json.dumps(
                    dict(responseHeaders), indent=4))
                # Preceding line instantiates a dict because the Requests
                # library uses a custom type, like CaseInsensitiveDictionary,
                # that hasn't implemented JSON encodability.
                lastFetch = self._last_fetch_from_releases_files()

            self._set_last_fetch(lastFetch)

        self._set_retrieval_progress(0, 0)

    def _asset_to_download(self):
        '''Release self._releasesDataLock before calling.'''
        releases = None
        with self._releasesDataLock:
            if self._releasesRawPath.is_file():
                with self._releasesRawPath.open("rb") as file:
                    releases = json.load(file) # Will be an array of objects.
        index = self._index_of_last_published(releases)
        if index is None:
            return None
        release = releases[index]
        releaseName = release['name']
        if releaseName.startswith("v"):
            releaseName = releaseName[1:]
        logger.info(
            f'Latest release "{releaseName}". Running "{App().version}"'
            f" {releaseName == App().version}")

        # Near here check if the running software is the latest release. If it
        # is then no need to download, but that can be overridden from the CLI.
        # Also need to support developers running a later version than hasn't
        # been published.


        for asset in release["assets"]:
            name = asset["name"]
            if (
                name.endswith(".exe")
                and name.startswith("-".join((App().name, "Installer")))
            ):
                return Asset(
                    name, str(asset['id']), asset['url'], asset['size'])
        
        return None

        # Near here, manage any installers that were already downloaded.
        #
        # File structure should be like this.
        #
        # update/
        # |
        # +--- assetNNNNN
        # |    |
        # |    +--- FaceCommander-installer...exe
        # |
        # +--- download.json



        # if installerPath.is_file():
        #     logger.info(f'Launching installer "{installerPath}" ...')
        #     # TOTH start a process that won't be terminated by termination of
        #     # the parent.  
        #     # https://stackoverflow.com/a/39715066/7657675
        #     popen = subprocess.Popen(
        #         (installerPath,)
        #         , creationflags=(
        #             subprocess.CREATE_NEW_PROCESS_GROUP
        #             | subprocess.DETACHED_PROCESS )
        #     )
        #     self._installerPID = popen.pid

    def _index_of_last_published(self, releases):
        # Near here have a flag for whether to include preview releases. And
        # have a CLI that says preview releases are in scope.


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

class UpdateState(NamedTuple):
    lastFetchMessage: str
    lastFetchDateTime: datetime
    retrievedAmount: int
    retrievingSize: int
    installerPath: Path

    def __eq__(self, other):
        return (
            self.lastFetchMessage == other.lastFetchMessage
            and self.lastFetchDateTime == other.lastFetchDateTime
            and self.retrievedAmount == other.retrievedAmount
            and self.retrievingSize == other.retrievingSize
            and self.installerPath == other.installerPath
        )

class Asset(NamedTuple):
    filename: str
    identifier: str
    url: str
    sizeBytes: int

    def fetch(self, agentHeader, progress_callback):
        directory = Path(App().updateDirectory, "asset" + self.identifier)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / self.filename
        if path.is_file() and path.stat().st_size == self.sizeBytes:
            logger.info(f"Asset already fetched {path} {self.sizeBytes}.")
            progress_callback(0, 0, path)
            return None

        logger.info(f"Fetching asset {self.url} ...")
        progress_callback(0, self.sizeBytes)
        with requests.get(
            self.url, stream=True,
            headers={**REQUEST_HEADERS_BINARY, **agentHeader}
        ) as response:
            status = response.status_code
            if status < 200 or status >= 300:
                progress_callback(0, 0)
                logger.error(
                    f'Asset fetch failed {status} "{response.reason}"'
                    f' {response.text}')
                return False

            # TOTH For loop with iter_content.
            # https://stackoverflow.com/q/39846671/7657675
            retrievedAmount = 0
            with path.open('wb') as file:
                for content in response.iter_content(8 * 1024 * 1024):
                    file.write(content)
                    retrievedAmount += len(content)
                    progress_callback(retrievedAmount)
            progress_callback(0, 0, path)
            logger.info(f"Asset fetched {path} {self.sizeBytes}.")
            return True
