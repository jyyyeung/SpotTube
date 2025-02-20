import os
import logging
from dataclasses import dataclass
import threading
import concurrent.futures
from flask_socketio import SocketIO  # type: ignore
from src.downloader import Downloader
from src.config import Config
from src.status import DownloadStatus


@dataclass
class DataHandler:
    """
    Data handler for the download
    """

    logger: logging.Logger
    percent_completion: int | float
    futures: list[concurrent.futures.Future]
    stop_downloading_event: threading.Event
    stop_monitoring_event: threading.Event
    monitor_active_flag: bool
    running_flag: bool
    downloader: Downloader

    def __init__(self, downloader: Downloader):
        self.logger = logging.getLogger()
        self.downloader = downloader

        app_name_text = os.path.basename(__file__).replace(".py", "")
        release_version = os.environ.get("RELEASE_VERSION", "unknown")

        self.logger.warning("%s\n", "*" * 50)
        self.logger.warning("%s Version: %s", app_name_text, release_version)
        self.logger.warning("*" * 50)

        self.percent_completion = 0

        config = Config()

        if not os.path.exists(config.download_folder):
            os.makedirs(config.download_folder)
        if not os.path.exists(config.config_folder):
            os.makedirs(config.config_folder)

        full_cookies_path = os.path.join(config.config_folder, "cookies.txt")
        self.cookies_path = (
            full_cookies_path if os.path.exists(full_cookies_path) else None
        )
        self.reset()

    @property
    def download_list(self) -> list[dict]:
        """
        Get the download list
        """
        return self.downloader.download_list

    @property
    def index(self) -> int:
        """
        Get the index of the download
        """
        return self.downloader.index

    @index.setter
    def index(self, value: int):
        self.downloader.index = value

    @property
    def status(self) -> DownloadStatus:
        """
        Get the status of the download
        """
        return self.downloader.status

    @status.setter
    def status(self, value: DownloadStatus):
        self.downloader.status = value

    def reset(self):
        """
        Resets the data handler
        """
        self.futures = []
        self.stop_downloading_event = threading.Event()
        self.stop_monitoring_event = threading.Event()
        self.monitor_active_flag = False
        self.percent_completion = 0
        self.running_flag = False

    def monitor(self, socketio: SocketIO):
        """
        Monitors the progress of the download
        """
        download_list = self.download_list
        index = self.index
        status = self.status
        while not self.stop_monitoring_event.is_set():
            self.percent_completion = (
                100 * (index / len(download_list)) if download_list else 0
            )
            custom_data = {
                "Data": download_list,
                "Status": status.value,
                "Percent_Completion": self.percent_completion,
            }
            socketio.emit("progress_status", custom_data)
            self.stop_monitoring_event.wait(1)
