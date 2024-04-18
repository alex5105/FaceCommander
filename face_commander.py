# Standard library imports, in alphabetic order.
#
# Logging module.
# https://docs.python.org/3/library/logging.html
import logging
#
# Object oriented path handling.
# https://docs.python.org/3/library/pathlib.html
from pathlib import Path
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
# https://platformdirs.readthedocs.io/en/latest/api.html
from platformdirs import user_data_dir
#
# Local imports.
#
from src.gui import MainGui
from src.pipeline import Pipeline
from src.task_killer import TaskKiller

def app_data_root():
    path = Path(user_data_dir(appname="FaceCommander", appauthor="AceCentre"))
    try:
        path.mkdir(parents=True, exist_ok=True)
    except FileExistsError as exception:
        # For details of why this exception is raised see the reference
        # documentation here.
        # https://docs.python.org/3/library/pathlib.html#pathlib.Path.mkdir
        raise RuntimeError(
            "Non-directory found where application data directory is expected."
            f' {path}'
        ) from exception
    
    return path

def configure_logging(appDataRoot):
    logging.basicConfig(
        format=r"%(asctime)s %(levelname)s %(name)s: %(funcName)s: %(message)s",
        level=logging.INFO,
        handlers=(
            logging.FileHandler(appDataRoot / 'log.txt', mode="w"),
            logging.StreamHandler(stdout)
        )
    )

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


if __name__ == "__main__":
    configure_logging(app_data_root())

    tk_root = customtkinter.CTk()

    logging.info("Starting main app.")
    TaskKiller().start()
    main_app = MainApp(tk_root)
    main_app.tk_root.mainloop()

    main_app = None
