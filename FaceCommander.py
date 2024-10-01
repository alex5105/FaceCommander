"""\
Face Commander.
Control and move the pointer using head movements and facial gestures.
"""
# Standard library imports, in alphabetic order.
#
# Command line arguments module. Command line arguments are used for diagnostic
# options.  
# https://docs.python.org/3/library/argparse.html
import argparse
#
# Logging module.
# https://docs.python.org/3/library/logging.html
import logging
#
# Object oriented path handling.
# https://docs.python.org/3/library/pathlib.html
from pathlib import Path
#
# Operating system module, used to get the command line and standard output.
# https://docs.python.org/3/library/sys.html
from sys import argv, stdout, executable as sys_executable
#
# Module for text dedentation. Only used for --help description.
# https://docs.python.org/3/library/textwrap.html
import textwrap
#
# PIP modules, in alphabetic order.
#
# https://customtkinter.tomschimansky.com/documentation/
import customtkinter
#
# Local imports.
#
from src.app import App
from src.gui import MainGui
from src.pipeline import Pipeline
from src.task_killer import TaskKiller

LOG_FORMAT = r"%(asctime)s %(levelname)s %(name)s: %(funcName)s: %(message)s"
LOG_LEVEL = logging.INFO

logger = logging.getLogger(__name__)

class MainApp(MainGui, Pipeline):
    def __init__(self, tk_root):
        super().__init__(tk_root)
        # Wait for window drawing.
        self.tk_root.wm_protocol("WM_DELETE_WINDOW", self.close_all)

        self.is_active = True

        # Enter loop
        self.tk_root.after(1, self.anim_loop)

    def anim_loop(self):
        try:
            if self.is_active:
                self.poll_update_state()

                # Run detectors and controllers.
                self.pipeline_tick()
                self.tk_root.after(1, self.anim_loop)
        except Exception as e:
            logging.critical(e, exc_info=e)

    def close_all(self):
        logging.info("Close all")
        self.is_active = False
        # Completely close this process
        TaskKiller().exit()

def create_app_data_root():
    try:
        App().dataRoot.mkdir(parents=True, exist_ok=True)
    except FileExistsError as exception:
        # For details of why this exception is raised see the reference
        # documentation here.
        # https://docs.python.org/3/library/pathlib.html#pathlib.Path.mkdir
        raise RuntimeError(
            "Non-directory found where application data directory is expected."
            f' {App().dataRoot}'
        ) from exception

def start_logging():
    logging.basicConfig(
        format=LOG_FORMAT, level=LOG_LEVEL, handlers=(
            logging.FileHandler(App().logPath, mode="w"),
            logging.StreamHandler(stdout)
        )
    )
    logger.info(
        f'Installation root "{App().installationRoot}".'
        f' Application data root "{App().dataRoot}".')

if __name__ == "__main__":
    cli={
        'description': textwrap.dedent(__doc__),
        'formatter_class': argparse.RawDescriptionHelpFormatter,
        'allow_abbrev': False
    }
    progPath = Path(__file__)
    for index, arg in enumerate(argv):
        try:
            if progPath.samefile(arg):
                # TOTH https://stackoverflow.com/a/54443527/7657675
                try:
                    executable = Path(sys_executable).relative_to(Path.cwd())
                except ValueError:
                    executable = Path(sys_executable)  # Use absolute path if not relative.
                cli['prog'] = " ".join([str(executable),] + argv[0:index + 1])
                break
        except FileNotFoundError:
            pass
    argumentParser = argparse.ArgumentParser(**cli)
    argumentParser.add_argument(
        '--no-user-agent', dest='userAgentHeader', action='store_false', help=
        "Don't send a user agent header when fetching release details, which"
        " causes fetch to fail with HTTP 403.")
    argumentParser.add_argument(
        '--release-information-delay', dest='releaseInformationDelay'
        , metavar="SECONDS", type=int, help=
        "Wait for a number of seconds after retrieving each 1kb of release"
        " information. This makes it easy to see retrieval progress on the"
        " About page.")
    argumentParser.add_argument(
        '--include-prereleases', dest='includePrereleases'
        , action='store_true', help=
        "Include prereleases in the update check and installer download.")
    argumentParser.parse_args(argv[1:], App())

    create_app_data_root()
    start_logging()

    tk_root = customtkinter.CTk()

    logger.info("Starting main app.")
    TaskKiller().start()
    main_app = MainApp(tk_root)
    main_app.tk_root.mainloop()

    main_app = None
