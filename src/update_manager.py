# Standard library imports, in alphabetical order.
#
# Date and time module.
# https://docs.python.org/3/library/datetime.html#datetime-objects
# https://docs.python.org/3/library/datetime.html#datetime.datetime.astimezone
from datetime import datetime, timedelta
#
# Email utilities, used to parse the Date header from the releases data API.
# https://docs.python.org/3/library/email.utils.html#email.utils.parsedate_to_datetime
from email.utils import parsedate_to_datetime
#
# Support for enumerated constants.
# https://docs.python.org/3/library/enum.html
from enum import Enum, auto as enum_auto
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
from typing import NamedTuple, Optional
#
# PIP modules, in alphabetic order.
#
# Module for human readable dates, times, and file sizes.  
# https://humanize.readthedocs.io  
# Import aliases are used to conform to Python naming convention.
from humanize import (
    naturalsize as natural_size,
    precisedelta as precise_delta,
    naturaldate as natural_date
)
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
RELEASES_CHUNK_BYTES = 1024
DELTA = {"minimum_unit":"minutes", "format":r"%0.0f"}
NATURAL_SIZE = {"gnu":True}

# Text that appears in the user interface uses these constants. It's a bit
# laborious but should facilitate localisation later.
PRERELEASE = "prerelease"
PUBLISHED = "published"
DEVELOPMENT = "in development"
AGO = "ago"
JUST_NOW = "just now"
SPACE = " "
FULL_STOP = "."
DOTS = "..."
UPDATE_AVAILABILITY_UNKNOWN = "Update availability unknown."
UPDATE_AVAILABILITY_NEVER_CHECKED = "Update availability never checked."
UPDATE_AVAILABILITY_CHECKED = "Update availability checked"
UPDATE_IN_PROGRESS = "Update in progress."
UPDATE_DOWNLOAD_IN_PROGRESS = "Update download in progress."
UPDATE_READY = "Update ready"
RETRIEVING = "Retrieving"
OF = "of"

INSTALLER_ASSET_SUFFIX = ".exe"
INSTALLER_ASSET_MIDDLE = "Installer"

VERSION_NAME_PREFIX = "v"

class RetrievingWhat(Enum):
    NOTHING = enum_auto()
    RELEASES_INFORMATION = enum_auto()
    INSTALLER = enum_auto()

class UpdateManager(metaclass=Singleton):

    def __init__(self):
        self._releasesRawPath = Path(
            App().updateDirectory, RELEASES_RAW_FILENAME)
        self._releasesIndentedPath = Path(
            App().updateDirectory, RELEASES_INDENTED_FILENAME)
        self._releasesHeadersPath = Path(
            App().updateDirectory, RELEASES_HEADERS_FILENAME)

        self._requestAgentHeader = (
            {USER_AGENT_HEADER: App().name + USER_AGENT_SUFFIX}
            if App().userAgentHeader else {}
        )

        # Thread synchronisation locks.
        #
        # Start Retrieve lock, must be acquired before either of these actions.
        #
        # -   Starting a retrieval thread.
        # -   Checking if a retrieval thread is already running.
        #
        # There is up to one retrieval thread at a time. Release the lock after
        # starting the thread.
        self._startRetrieveLock = Lock()
        with self._startRetrieveLock:
            self._retrieveThread = None
        #
        # Releases Data lock, must be acquired before reading or writing the
        # releases files.
        self._releasesDataLock = Lock()

        self._state = LockedState()

        self._started = False
    
    @property
    def state(self):
        return self._state.get()

    def start(self):
        if not self._started:
            self._started = True
            # Don't check for updates at launch if the diagnostic delay option
            # is active.
            self.manage(False if App().releaseInformationDelay > 0 else None)

    def manage(self, checkNow:Optional[bool] = None):
        App().updateDirectory.mkdir(parents=True, exist_ok=True)
        with self._releasesDataLock:
            releasesChecked = self._last_fetch_from_releases_files()
        self._state.set(releasesChecked=releasesChecked)
        if releasesChecked is None and checkNow is None:
            # If checkNow is unspecified, and releases have never been checked,
            # check now. If checkNow:False was specified, don't check now.
            checkNow = True

        # ToDo near here, if checkNow is False then calculate how long ago the
        # last fetch was. If it was far enough in the past then set it to true.

        # Clean up any finished thread.
        with self._startRetrieveLock:
            if (
                self._retrieveThread is not None
                and not self._retrieveThread.is_alive()
            ):
                self._retrieveThread.join()
                self._retrieveThread = None

        if checkNow:
            with self._startRetrieveLock:
                if self._retrieveThread is None:
                    # The _fetch method will retrieve releases data and download
                    # an installer asset if an update is available.
                    self._retrieveThread = Thread(target=self._fetch)
                    self._retrieveThread.start()
        else:
            # Don't retrieve releases information, but still download an
            # installer asset if an update is available based on the stored
            # releases information.
            asset = self._process_release_information()
            if asset is not None:
                logger.info(f'Starting thread to download {asset=}.')
                with self._startRetrieveLock:
                    if self._retrieveThread is None:
                        self._retrieveThread = Thread(
                            target=asset.fetch,
                            args=(self._requestAgentHeader, self._state)
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

    def _fetch(self):
        '''Run as a Thread and don't start more than one.'''
        self._fetch_release_information()
        asset = self._process_release_information()
        if asset is not None:
            logger.info(f'Downloading in thread {asset=}.')
            asset.fetch(self._requestAgentHeader, self._state)
    
    def _fetch_release_information(self):
        # References for the request.
        #
        # https://docs.github.com/en/rest/releases/releases?apiVersion=2022-11-28#list-releases-for-a-repository
        #
        # This code uses the API without authentication. That means it retrieves
        # only public data, which doesn't include draft releases.
        #
        # "All API requests must include a valid User-Agent header."
        # https://docs.github.com/en/rest/using-the-rest-api/getting-started-with-the-rest-api?apiVersion=2022-11-28#user-agent

        # "https://api.github.com/repos/AceCentre/FaceCommander/releases"
        # /repos/{owner}/{repo}/releases
        
        url = App().releasesAPI
        logger.info(f"Fetching release data from {url} ...")

        downloadPath = None
        responseHeaders = None
        self._state.set(
            retrievedAmount=0, retrievingSize=-1
            , retrievingWhat=RetrievingWhat.RELEASES_INFORMATION)
        with requests.get(
            url, stream=True,
            headers={**REQUEST_HEADERS_JSON, **self._requestAgentHeader}
        ) as response:
            status = response.status_code
            if status < 200 or status >= 300:
                self._state.zero()
                logger.error(
                    f'Fetch failed {status} "{response.reason}"'
                    f' {response.text}')
            else:
                # Download release information to a temporary file in the update
                # directory. Rename the temporary file to the final name when
                # the download finishes. Note that there's no need to acquire
                # the Releases Data lock until the download has finished.
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
                    delay = App().releaseInformationDelay # Diagnostic option.
                    for content in response.iter_content(RELEASES_CHUNK_BYTES):
                        file.write(content)
                        retrievedAmount += len(content)
                        self._state.set(retrievedAmount=retrievedAmount)
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
                releasesChecked = self._last_fetch_from_releases_files()

            self._state.set(releasesChecked=releasesChecked)

        self._state.zero()
    
    def _process_release_information(self):
        '''Release self._releasesDataLock before calling.'''
        releases = None
        with self._releasesDataLock:
            if self._releasesRawPath.is_file():
                with self._releasesRawPath.open("rb") as file:
                    releases = json.load(file) # Will be an array of objects.

        if releases is None or len(releases) == 0:
            logger.error(f"No information {releases=}")
            return None
        
        includePrereleases = App().includePrereleases # Diagnostic option.
        logger.info(f'{includePrereleases=}')
        
        latestIndex = None
        latestPublished = None
        runningIndex = None
        prereleases = 0
        for index, release in enumerate(releases):
            published, publishedStr = self._published(release)
            running, prerelease, name = self._running(release)
            logger.info(
                f'releases[{index}] {name=} {running=} {prerelease=}'
                f' {publishedStr=} {published}')

            if running:
                runningIndex = index
                self._state.set(runningPublished=("".join((
                    SPACE, *((PRERELEASE, SPACE) if prerelease else ())
                    , PUBLISHED, SPACE, natural_date(published), FULL_STOP
                ))))

            if prerelease:
                prereleases += 1
                if not includePrereleases:
                    continue

            if latestIndex is None or published > latestPublished:
                if latestIndex is not None:
                    logger.info(f'{published} > {latestPublished}')
                latestIndex = index
                latestPublished = published

        if runningIndex is None:
            logger.info(
                "Running an unpublished developer version."
                " No installer asset download.")
            self._state.set(runningPublished="".join((
                SPACE, DEVELOPMENT, FULL_STOP)))
            return None
        
        if latestIndex is None:
            logger.info(
                f'{latestIndex=}.'
                f' Total release count {len(releases)}.'
                f' Of which, prerelease count {prereleases}.')
            return None

        if latestIndex == runningIndex:
            # Running software is the latest published, so no need to download
            # an installer asset.
            logger.info("Running latest release. No installer asset download.")
            return None

        # ToDo near here, manage any installers that were already downloaded.

        assets = releases[latestIndex]['assets']
        for asset in assets:
            name = asset['name']
            if (
                name.endswith(INSTALLER_ASSET_SUFFIX)
                and name.startswith("-".join((
                    App().name, INSTALLER_ASSET_MIDDLE)))
            ):
                return Asset(
                    name, str(asset['id']), asset['url'], asset['size'])

        logger.error(f"No installer identified for download {assets=}")
        return None

    def _published(self, release):
        publishedStr = release['published_at']
        #
        # Ending with a Z, to indicate zero time zone offset, is valid ISO
        # 8601 format but seems to be rejected by Python 3.10 on Windows.
        if publishedStr[-1] == 'Z':
            publishedStr = publishedStr[:-1] + "+00:00"
        return datetime.fromisoformat(publishedStr).astimezone(), publishedStr

    def _running(self, release):
        name = release['name']
        if name.startswith(VERSION_NAME_PREFIX):
            name = name[len(VERSION_NAME_PREFIX):]
        return (name == App().version), release['prerelease'], name

    def launch_installer(self):
        installerPath = self._state.get().installerPath
        if installerPath is None:
            logger.error("Installer path is None.")
            return False

        if not installerPath.is_file():
            logger.error("Installer path isn't a file." f' "{installerPath}"')
            return False

        logger.info(f'Launching installer "{installerPath}"')
        # TOTH start a process that won't be terminated by termination of
        # the parent.  
        # https://stackoverflow.com/a/39715066/7657675
        self._state.set(installerPopen=subprocess.Popen(
            (installerPath,), creationflags=(
                subprocess.CREATE_NEW_PROCESS_GROUP
                | subprocess.DETACHED_PROCESS
            )
        ))
        return True

class LockedState:
    def __init__(self):
        self._lock = Lock()
        with self._lock:
            self._releasesChecked = None
            self._retrievedAmount = None
            self._retrievingSize = None
            self._retrievingWhat = None
            self._installerPath = None
            self._setEver = False
            self._installerPopen = None
            self._runningPublished = ""
    
    def set(
        self,
        releasesChecked: Optional[datetime] = None,
        retrievedAmount: Optional[int] = None,
        retrievingSize: Optional[int] = None,
        retrievingWhat: Optional[RetrievingWhat] = None,
        installerPath: Optional[str] = None,
        installerPopen: Optional[subprocess.Popen] = None,
        runningPublished: Optional[str] = None
    ):
        with self._lock:
            self._setEver = True
            if releasesChecked is not None:
                self._releasesChecked = releasesChecked
            if retrievedAmount is not None:
                self._retrievedAmount = retrievedAmount
            if retrievingSize is not None:
                self._retrievingSize = retrievingSize
            if installerPath is not None:
                self._installerPath = installerPath
            if retrievingWhat is None:
                if retrievedAmount == 0 and retrievingSize == 0:
                    self._retrievingWhat = RetrievingWhat.NOTHING
            else:
                self._retrievingWhat = retrievingWhat
            if installerPopen is not None:
                self._installerPopen = installerPopen
            if runningPublished is not None:
                self._runningPublished = runningPublished
    
    def zero(self, **kwargs):
        return self.set(retrievedAmount=0, retrievingSize=0, **kwargs)

    def get(self):
        with self._lock:
            installerPID = None
            if self._installerPopen is not None:
                if self._installerPopen.poll() is None:
                    # Process is still running.
                    installerPID = self._installerPopen.pid
            return UpdateState(
                "".join(
                    summary for summary in
                    self._releases_summaries(installerPID)),
                "".join(
                    summary for summary in
                    self._installer_summaries(installerPID)),
                "".join(
                    prompt for prompt in
                    self._installer_prompts(installerPID)),
                self._releasesChecked,
                self._retrievedAmount,
                self._retrievingSize,
                self._retrievingWhat,
                self._installerPath,
                installerPID,
                self._runningPublished
            )
    
    def _releases_summaries(self, installerPID):
        if installerPID is not None:
            return
        if not self._setEver:
            yield UPDATE_AVAILABILITY_UNKNOWN
            return

        if self._releasesChecked is None:
            yield UPDATE_AVAILABILITY_NEVER_CHECKED
        else:
            yield UPDATE_AVAILABILITY_CHECKED
            yield SPACE
            # 1.  If the check was more than an hour ago, use the natural_date()
            #     description, which will be today, yesterday, or a date.
            # 2.  If the check was between one hour and five minutes ago, use a
            #     precise_delta() description, in minutes.
            # 3.  If the check was less than five minutes ago, describe it as
            #     just now.
            now = datetime.now().astimezone()
            agoMinutes = (now + timedelta(minutes=-5)).astimezone()
            agoDate = (now + timedelta(hours=-1)).astimezone()
            if self._releasesChecked < agoDate:
                yield natural_date(self._releasesChecked)
            elif self._releasesChecked < agoMinutes:
                yield precise_delta(
                    now - self._releasesChecked, **DELTA)
                yield SPACE
                yield AGO
            else:
                yield JUST_NOW
            yield FULL_STOP
        if self._retrievingWhat is RetrievingWhat.RELEASES_INFORMATION:
            yield from self._progress()

    def _installer_summaries(self, installerPID):
        if installerPID is not None:
            yield UPDATE_IN_PROGRESS
            return
        if self._retrievingWhat is RetrievingWhat.INSTALLER:
            yield UPDATE_DOWNLOAD_IN_PROGRESS
            yield from self._progress()
    
    def _installer_prompts(self, installerPID):
        if installerPID is None and self._installerPath is not None:
            yield UPDATE_READY
            yield SPACE
            yield self._installerPath.name

    def _progress(self):
        if self._retrievingSize == 0:
            return
        yield SPACE
        yield RETRIEVING
        yield SPACE
        if self._retrievingSize < 0:
            yield natural_size(self._retrievedAmount, **NATURAL_SIZE)
        elif self._retrievingSize > 0:
            percentage = 100.0 * (
                float(self._retrievedAmount) / float(self._retrievingSize))
            yield f"{percentage:.0f}%"
            yield SPACE
            yield natural_size(self._retrievedAmount, **NATURAL_SIZE)
            yield SPACE
            yield OF
            yield SPACE
            yield natural_size(self._retrievingSize, **NATURAL_SIZE)
        yield SPACE
        yield DOTS

class UpdateState(NamedTuple):
    releasesSummary: str
    installerSummary: str
    installerPrompt: str
    releasesChecked: datetime
    retrievedAmount: int
    retrievingSize: int
    # retrievingSize semantics are as follows.
    # -   Zero if no retrieval is underway.
    # -   Negative if an indeterminate retrieval is underway.
    # -   Positive if a determinate retrieval is underway.
    retrievingWhat: RetrievingWhat
    installerPath: Path
    installerPID: Optional[int]
    runningPublished: str

    def __eq__(self, other):
        for field in self._fields:
            if getattr(self, field) != getattr(other, field):
                return False
        return True

class Asset(NamedTuple):
    filename: str
    identifier: str
    url: str
    sizeBytes: int

    def fetch(self, agentHeader:dict, lockedState:LockedState):
        directory = Path(App().updateDirectory, "asset" + self.identifier)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / self.filename
        if path.is_file() and path.stat().st_size == self.sizeBytes:
            logger.info(f"Asset already fetched {path} {self.sizeBytes}.")
            lockedState.zero(installerPath=path)
            return None

        logger.info(f"Fetching asset {self.url} ...")
        lockedState.set(
            retrievedAmount=0, retrievingSize=self.sizeBytes
            , retrievingWhat=RetrievingWhat.INSTALLER
        )
        with requests.get(
            self.url, stream=True,
            headers={**REQUEST_HEADERS_BINARY, **agentHeader}
        ) as response:
            status = response.status_code
            if status < 200 or status >= 300:
                lockedState.zero()
                logger.error(
                    f'Asset fetch failed {status} "{response.reason}"'
                    f' {response.text}')
                return False

            # TOTH For loop with iter_content.
            # https://stackoverflow.com/q/39846671/7657675
            retrievedAmount = 0
            retrieveChunk = int(self.sizeBytes / 20)
            with path.open('wb') as file:
                for content in response.iter_content(retrieveChunk):
                    file.write(content)
                    retrievedAmount += len(content)
                    lockedState.set(retrievedAmount=retrievedAmount)
            lockedState.zero(installerPath=path)
            logger.info(f"Asset fetched {path} {self.sizeBytes}.")
            return True
