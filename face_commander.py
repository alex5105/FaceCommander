# Standard library imports, in alphabetic order.
#
# Logging module.
# https://docs.python.org/3/library/logging.html
import logging
#
# Operating system module, used to get standard output.
# https://docs.python.org/3/library/sys.html
from sys import stdout
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
    create_app_data_root()
    start_logging()

    tk_root = customtkinter.CTk()

    logger.info("Starting main app.")
    TaskKiller().start()
    main_app = MainApp(tk_root)
    main_app.tk_root.mainloop()

    main_app = None
