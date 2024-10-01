# Developer guide

This guide has information for developer contributors to Face Commander.

- Getting started.
- Build instructions.
- Tips for Git on Windows.

There are separate guides for the following.

- [Update manager developer guide](UpdateManagerDeveloperGuide.md).
- [Version number developer guide](VersionNumberDeveloperGuide.md).
- [Release and sign developer guide](ReleaseAndSignDeveloperGuide.md).

Paths in this file have forward slash separators, not backslash. Forward slash
is compatible with PowerShell and with bash, which is an alternative shell that
comes with Git for Windows, see below. Backslash is only compatible with
PowerShell.


# Build instructions

A Windows executable and installer can be built for this application. This type
of executable is sometimes referred to as a _frozen_ Python application.

To build the executable and installer you will need these tools.

- [Nutika](https://nutika.ent/) for the executable.  
  It will already have been installed into the venv, see above, because it is
  listed in the [pyrproject.toml](pyrproject.toml) file.

- [Inno Setup](https://jrsoftware.org/isinfo.php) for the installer.  
  It can be obtained from their
  [downloads page](https://jrsoftware.org/isdl.php#stable). Look for
  `innosetup-X.X.X.exe` where X.X.X is at least the 6.2.2 version. The
  download will install the Inno Setup Compiler application, which is an
  installer builder.

Proceed as follows.

1.  Build the executable.

    Run commands like this

        cd /path/where/you/cloned/FaceCommander
        ./build_executable.bat

    That creates a `build/` and a `dist/` sub-directory.

2.  Test the executable.

    The executable will be here.
    `/path/where/you/cloned/FaceCommander/dist/facecommander/facecommander.exe`

    Run it at least once to test it, for example by double-clicking. Note that
    the directory and .exe file names have no underscore, unlike the .py file
    name.

3.  Build the installer.

    Open the `installer.iss` file in the Inno Setup Compiler application that
    you installed. You might be able to do that by double clicking the file,
    depending on the options you chose when you installed Inno Setup. Otherwise
    you can start the Inno Setup Compiler and open the `installer.iss` file by
    hand.

    In the compiler select Build, Compile to build the installer, or press
    Ctrl-F9 as a shortcut. That will create an `Output/` sub-directory, with a
    `FaceCommander-Installer-vX.X.X.exe` file in it.

Run the installer .exe you just generated at least once to test it, for example
by double-clicking.

That concludes building the executable and installer.

# Tips for Git on Windows

Git for Windows can be installed with winget as described here.  
[git-scm.com/download/win](https://git-scm.com/download/win)

You can activate OpenSSH in Windows 10 as described here.  
[stackoverflow.com/a/40720527/7657675](https://stackoverflow.com/a/40720527/7657675)

You can then set up a private key for GitHub authentication and configure SSH in
the usual way, by creating a `.ssh` sub-directory under your `users` directory,
for example `C:/Users/Jim/.ssh`. For example, you could create a `config` file
there with these settings.

    Host github.com
        IdentityFile ~/.ssh/<file you created with ssh-keygen here>
        User <Your GitHub username here>

    Host *
        AddKeysToAgent yes

That will cause the SSH identity you use for GitHub to be loaded in the agent so
you don't have to retype the private key passcode every time.

You can discover the OpenSSH executable path by running a Powershell command
like this.

    gcm ssh

The output could be like this (spaces have been compressed).

    CommandType     Name         Version    Source
    -----------     ----         -------    ------
    Application     ssh-add.exe  8.1.0.1    C:\Windows\System32\OpenSSH\ssh.exe

You can configure Git to use OpenSSH in the current Powershell session by
setting an environment variable, like this.

    $env:GIT_SSH = "C:\Windows\System32\OpenSSH\ssh.exe"

You can configure Git to use OpenSSH in all your future Powershell sessions by
configuring a permanent environment variable, like this.

    [Environment]::SetEnvironmentVariable(
        "GIT_SSH", "C:\Windows\System32\OpenSSH\ssh.exe", "User")

TOTH [stackoverflow.com/a/55389713/7657675](https://stackoverflow.com/a/55389713/7657675)  
Looks like you have to exit the Powershell session in which you ran that
command for it to take effect.

You can check the value has been set by printing all environment variables. To
do that run a command like this.

    get-childitem env:

Git for Windows comes with a command line shell, `bash`, which you may prefer to
use instead of PowerShell. Here are some tips for bash for Windows.

- To open a directory in Windows file explorer from bash, you can use the
  `start` command. For example this command will open the current working
  directory.

      start .

- You can select to set bash as the default shell in VSCode and VSCodium, see
  this StackOverflow answer.  
  [stackoverflow.com/a/50527994/7657675](https://stackoverflow.com/a/50527994/7657675)
