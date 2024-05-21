# Version number developer guide

This is a developer guide about the version number of the FaceCommander software
package.

All components that require the software's version number use a single source,
the [assets/Version.ini](../assets/Version.ini) file.

The .INI format was selected because it supports comments and has native support
in all the components that require access. See below for a list of those
components.

Note that changes to the Version.ini file trigger the build workflow, see under
Build trigger below.

# Installer component

The installer requires access to the version number. Access is implemented in
the installer setup script, which is read by the Inno Setup Compiler. Inno has
native support for reading .INI files.

See the comments in the [installer.iss](../installer.iss) file for details of
the implementation.

# Build workflow component

The build workflow requires access to the version number. Access for the
workflow is implemented in

- the [build job definition](../.github/workflows/release.yml),
  which is processed by the GitHub Actions service.
- a [Python utility module](../src/utils/readini.py) that also has a command
  line interface called by the build job.

Python has native support for reading .INI files.

## Build trigger

Pushing a change to the Version.ini file triggers the build workflow. The change can be on any branch, not only `main`. The workflow creates a tag for the, builds the executable and installer as release assets, and sets the release to prerelease status. The build steps in the automated workflow are the same as in the [Developer guide](readme.md).

# Application run-time components

The application itself requires access to the version number at run time. All
application components use the [App singleton](../src/app.py) property
`App().version` to access the running software's version number.

The App code itself uses the same Python utility module as the build workflow,
above, but directly and not through the command line interface.
