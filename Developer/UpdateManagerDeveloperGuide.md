# Update manager developer guide
The update manager is a component of the FaceCommander software package. Its
functions are to

-   retrieve publication and status information about the running version of the
    software.
-   check for updates to the software.
-   download an update installer if available.
-   launch the downloaded installer.

This is a guide to the component for developers.

# Overview
The update manager is a singleton class. Its code is in the
[src/update_manager.py](../src/update_manager.py) file.

The update manager component doesn't have any tkinter code and doesn't as such
show any user interface (UI). However, it does generate descriptions that may be
shown in the UI. At time of writing, update manager descriptions are shown on
the About page. See under Update manager state descriptions, below, for details.

The update manager calls a server application programming interface (API) to get
releases information for the software. The API

-   uses secure Hypertext Transfer Protocol (HTTP) for communication.
-   is provided by the host of the released software, GitHub.
-   provides information in JavaScript Object Notation (JSON) format.
-   provides addresses from which installer files, referred to as assets, can be
    downloaded.

For API reference documentation see the GitHub website, for example
here.  
[docs.github.com/en/rest/releases/...list-releases-for-a-repository](https://docs.github.com/en/rest/releases/releases?apiVersion=2022-11-28#list-releases-for-a-repository)

The update manager caches information retrieved from the API in the application
data directory. See under Update manager files, below, for details.

The update manager will attempt to retrieve and cache releases information from
the API when the

-   application is launched for the first time.
-   application is launched and cached information isn't present.
-   user selects to check for an update.

After retrieval and caching, the update manager processes the releases
information and may initiate retrieval of an update installer. See under
Releases information data structure, and under Releases information usage, both
below, for details.

After downloading the installer, the update manager can launch it. At time of
writing an installer will always launch in full-screen and warn the user that
the program can make changes to their system. If the main application is
terminated by the user while the installer is running, the installer isn't
terminated automatically.

# Update manager files
The update manager maintains and utilises these files.

-   *Releases information raw file*, which is a copy of the latest retrieval
    from the API. The format is JSON.
-   *Releases information indented file*, which has the same JSON as the raw
    file but indented and with line breaks for easier human readability.
-   *Releases headers file*, which a JSON representation of the HTTP headers
    from the latest retrieval.
-   *Asset files*, which are copies of installers downloaded from the API. Each
    asset file is kept in a separate directory.

The releases information files are relatively small, typically under 30 kb in
total. Asset files are relatively large, typically approaching 100 mb each.

In principle there need be only one of each releases information file and up to
one asset file at a time.

The update manager stores its files in the application data directory. The
structure is illustrated in this diagram.

    User home directory/AppData/Local/AceCentre/FaceCommander/
    |
    +---configs/
    |   |
    |   + Profiles and settings.
    |     This directory is shown for context, not documented here.
    |
    +---log.txt
    |
    +---update/
        |
        +--- assetNNNNN/
        |    |
        |    +--- FaceCommander-installer...exe
        |
        +--- releases_headers.json
        |
        +--- releases_indented.json
        |
        +--- releases_raw.json

# Releases information data structure
The update manager uses the following data from the releases information files.

-   From the headers file, the value of the `Date` header is taken as the time
    of the last check for updates.
    
    It appears that the API doesn't always return a Date header. For example,
    that seems to happen in the case that the request doesn't include a User
    Agent header.

-   The modification time of the raw file is taken as the time of the last check
    for updates in case the Date header isn't available.

-   If the Date header isn't available, and there isn't a raw file, then it is
    assumed that there has never been a check for updates.

The update manager generates and maintains a description of the time of the last
check. And see under Update manager state descriptions, below.

The data structure of the raw and indented files is an array of release
information records, each relating to one release. These fields are used in each
record.

-   `published_at`, the time that release was published.

-   `name`, the version number of the release.

    The value can be matched to the version number of the running software, to
    which the update manager has access as an application run-time component.
    See the [Version number developer guide](VersionNumberDeveloperGuide.md) for
    details.

-   `prerelease`, a Boolean for whether the release is flagged as prerelease
    software.

-   `assets`, an array of records about release assets, such as installer
    files that can be downloaded. Within each asset record, these fields are
    used.

    -   `name`, the file name of the asset. The value is pattern-matched to
        an expected naming convention to identify which asset to download.
    -   `id`, a unique numeric identifier used in the directory name for the
        asset file if it gets downloaded.
    -   `url`, the address from which the asset can be downloaded.
    -   `size`, used to calculate the progress of a download.

The indented file contains the same fields as the raw file but isn't read by the
update manager.

# Releases information usage
Releases information retrieved by the update manager is used for these purposes.

The retrieved releases information is used to determine the publication date and
status of the current running software. The version number is matched against
the version numbers in the releases information and the following rules applied.

-   If there isn't a match then the running software is assumed to be have
    *in-development status* and *no publication date*.
-   If there is a match then the release's `published_at` value is its
    *publication date*.
-   If there is a match and the release's `prerelease` flag is set then the
    running software has *prerelease status*. Otherwise, it has
    *production status*. But note that production status isn't explicitly
    flagged in the user interface.

The retrieved releases information is also used to determine which is the
*latest release*, as follows.

-   Releases flagged as prerelease aren't in scope. That can be overridden with
    a diagnostic command line switch, see the Appendix: Developer support,
    below.

-   The release with the latest published_at value is the latest release.

Note that there mightn't be a latest release, for example if all current hosted
releases are flagged as prerelease.

A download action may be taken depending on the following rules.

-   If the running software is in development then no action is taken.

-   Otherwise, if the latest release was published after the running software
    was published then an installer asset is downloaded. The asset to download
    is chosen from its `name`, see under Releases information data structure,
    above.

# Update manager state descriptions
The update manager generates descriptive messages for these aspects of its
current state.

-   `runningPublished` is a message about when the running software was
    published, if known, and its status as prerelease or in-development. See
    under Releases information usage, above, for details.

-   `releasesSummary` is a message about the when the last update check was
    made, and about any update check that is currently in progress.
    
    For the purposes of this message the update check finishes when the releases
    information has been retrieved. Specifically, installer download isn't part
    of the update check.

    In principle, if an update check is now underway then the message expresses
    progress in terms of number of bytes retrieved from the API. In practise
    retrieval completes in about one second so that part of the message won't be
    noticed by end users. But see the Appendix: Developer support, below.

-   `installerSummary` is a message for either of these cases.

    -   An installer download is underway.
    
        The message will describe current progress of the download. Progress is
        expressed in terms of bytes downloaded, bytes total, and a percentage.

    -   A downloaded installer has been launched and is running now.
    
        This case is identified by tracking the process identifier (PID) of the
        installer. The PID is known because the application launches the
        installer in a separate process. If the user cancels the installation
        then PID tracking will show that it terminated and this case no longer
        applies.

    This message isn't presented as actionable in the user interface.

-   `installerPrompt` is a message about the downloaded installer, if any. The
    message includes the name of the .exe file, which will include its version
    number.

    This message is presented as actionable in the user interface. The action
    taken when the user selects it is to launch the installer.

If there is an installer prompt then there won't be an installer summary. In
other words, if installerPrompt isn't blank then installerSummary will be blank.
If no update installer is available, for example if the running software is
already the latest, then the installer prompt and the installer summary will
both be blank.

The update manager's state is polled by one class in the UI code, `MainGui`.
That UI code in turn reflects the messages into tkinter string variables. Those
variables can be observed by other parts of the UI code in order to display the
update state to the end user.

# Update manager synchronisation and threading
All update manager data retrievals take place on a separate processing thread.
These locks are used for synchronisation.

-   The *start retrieve* lock is acquired to launch a retrieval thread or to
    check if a retrieval thread is already running. The lock is released after
    the launch or check. The update manager runs no more than one retrieval
    thread at a time.

-   The *releases data* lock is acquired to read or write the releases
    information files, see above. The lock is released after the files have been
    written, or read into memory for processing.

-   The *state* lock is acquired to read or update the descriptions of the
    current update manager state. The lock is released after the read or update
    is complete.

# Appendix: Developer support
The software has some facilities that can be used to support development of the
update manager.

## Force retrieval and download
You can force the application to retrieve releases information at launch by
deleting the headers and raw releases files.

You can force the application to repeat download of the latest update installer
by deleting the installer .exe file, or by deleing the asset directory that
contains it.

You can also delete the whole update/ directory to force both retrieval and
download at launch.

## Test harness for releases information
If you are working on the update manager code you may want to simulate various
responses from the releases information API. These are some examples of
simulations you might want in a test harness.

-   Change the time of the last update check.
-   Change the publication time of a release to make it newer or older than the
    running software.
-   Change the publication time of the running software.
-   Change the prerelease status of a particular release.

This can be done as follows.

1.  Start the application and check for updates once.
2.  Terminate the application.
3.  Edit the releases information files to represent the response you require.

    -   To change the time of the last update check, edit the headers file.
    -   To change any other value, edit the indented releases information file
        and save it over the raw file.

4.  Start the application again.

The software will read the modified files and hence the response will be
simulated.

## Diagnostic command line switches
The software has a command line interface (CLI) with diagnostic switches. The
CLI can be accessed when the application is run from its source. The CLI isn't
available in the built executable nor in the application as installed.

You can print all the command line switches by running the application like
this.

    cd /path/where/you/cloned/FaceCommander
    ./venv/Scripts/python.exe face_commander.py --help

Output will be like this. Some space has been removed for layout here.

    usage: venv\Scripts\python.exe face_commander.py [-h] [--no-user-agent]
              [--release-information-delay SECONDS] [--include-prereleases]

    Face Commander.
    Control and move the pointer using head movements and facial gestures.

    options:
    -h, --help           show this help message and exit
    --no-user-agent
            Don't send a user agent header when fetching release details, which
            causes fetch to fail with HTTP 403.
    --release-information-delay SECONDS
            Wait for a number of seconds after retrieving each 1kb of release
            information. This makes it easy to see retrieval progress on the
            About page.
    --include-prereleases
            Include prereleases in the update check and installer download.
