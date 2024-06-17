# Standard library imports, in alphabetical order.
#
# Logging module.
# https://docs.python.org/3/library/logging.html
import logging
import signal
#
# PIP modules, in alphabetic order.
#
# Cross-platform processes module.
# https://psutil.readthedocs.io/en/latest/
from psutil import Process, NoSuchProcess
#
# Local imports.
#
import src.utils as utils
from src.singleton_meta import Singleton
from src.update_manager import UpdateManager

logger = logging.getLogger("TaskKiller")


class TaskKiller(metaclass=Singleton):
    """Singleton class for softly killing the process and freeing the memory
    """

    def __init__(self):
        logger.info("Initialize TaskKiller singleton")
        self.is_started = False

    def start(self):
        if not self.is_started:
            logging.info("Installing google fonts.")
            utils.install_fonts("assets/fonts")

            # Start singletons
            from src.update_manager import UpdateManager
            UpdateManager().start()

            from src.config_manager import ConfigManager
            ConfigManager().start()

            from src.camera_manager import CameraManager
            CameraManager().start()

            from src.controllers import Keybinder
            Keybinder().start()

            from src.detectors import FaceMesh
            FaceMesh().start()

            self.is_started = True

    def exit(self):
        logger.info("Exit program")

        from src.camera_manager import CameraManager
        from src.controllers import Keybinder
        from src.detectors import FaceMesh

        CameraManager().destroy()
        Keybinder().destroy()
        FaceMesh().destroy()

        utils.remove_fonts("assets/fonts")

        self._terminate_tree(
            Process(), tuple(pid for pid in self._exempt_PID()))
        exit()

    def _exempt_PID(self):
        pid = UpdateManager().state.installerPID
        if pid is not None:
            yield pid

    def _terminate_tree(self, process, exempt):
        logger.info(f'{process=} {exempt=}')
        if process.pid in exempt:
            logger.info(f"Exempt {process.pid=}")
            return
        for child in process.children():
            logger.info(f'Parent {process} {child=}')
            self._terminate_tree(child, exempt)
        logger.info(f'SIGTERM {process.pid=}')
        try:
            process.send_signal(signal.SIGTERM)
        except NoSuchProcess:
            logger.info(f'No such process {process.pid=}')

