# Release and Sign

We use Github Releases to track the releases which is then tied to our updater. [Read the update manager docs here.](UpdateManagerDeveloperGuide.md)

# Signing

The application must be signed in order for the 'UI Access' flag to be properly applied to our application. The executable and the installer must be signed separately.

We (Ace Centre) have an EV Code Signing Certificate which we sign applications with. However, it is tied to a physical USB Private Key. To use automation to sign out files we have setup a machine in our office with the key plugged in and set it up as a 'Github Runner', which can be access in Github Actions using the `runs-on: self-hosted` option. We only sign on this machine, other build steps happen on Github runners.

The key has to be manually 'unlocked' before any github flow can access the key. Details of how to do this process will be shared internally, for this reason the release process can only be completed by Ace Centre staff.

# Release

[You can see the full release Github Workflow here.](../.github/workflows/release.yml). It follows these steps:

1. Build executable
2. Sign executable
3. Build installer
4. Sign installer
5. Release installer

# Developing

You will not have access to signed executables during development, this means you will likely run into issues around permissions. You can solve all these issues by running as admin.
