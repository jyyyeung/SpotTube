import os
import threading
from dataclasses import dataclass

from flask_socketio import SocketIO  # type: ignore
from loguru import logger

from src.config import Config
from src.downloader import Downloader
from src.status import DownloadStatus


@dataclass
class DataHandler:
    """
    Data handler for the download
    """

    _stop_monitoring_event: threading.Event
    monitor_active_flag: bool
    downloader: Downloader

    def __init__(self, downloader: Downloader):
        super().__init__()
        self.downloader = downloader

        app_name_text = os.environ.get("APP_NAME", "SpotTube")
        release_version = os.environ.get("RELEASE_VERSION", "unknown")

        print(f"{'*' * 50}\n")
        print(f"{app_name_text} Version: {release_version}")
        print("*" * 50)

        self._stop_monitoring_event = threading.Event()
        self._stop_monitoring_event.clear()

        config = Config()

        full_cookies_path = os.path.join(config.config_folder, "cookies.txt")
        self.cookies_path = (
            full_cookies_path if os.path.exists(full_cookies_path) else None
        )
        self.reset()

    @property
    def stop_monitoring_event(self) -> threading.Event:
        """
        Get the stop monitoring event
        """
        return self._stop_monitoring_event

    @stop_monitoring_event.setter
    def stop_monitoring_event(self, value: threading.Event):
        self._stop_monitoring_event = value

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
        self.downloader.stop_downloading_event.clear()
        self.stop_monitoring_event.clear()
        self.monitor_active_flag = False
        self.downloader.reset()

    def monitor(self, socketio: SocketIO):
        """
        Monitors the progress of the download

        Args:
            socketio (SocketIO): The socketio object
        """

        while not self.stop_monitoring_event.is_set():
            index = self.index
            status = self.status
            download_list = self.downloader.download_list
            percent_completion = (
                100 * (index / len(download_list)) if download_list else 0
            )
            download_list_dump = [track.model_dump() for track in download_list]
            custom_data = {
                "data": download_list_dump,
                "status": status.value,
                "percent_completion": percent_completion,
            }
            logger.debug(f"Emitted update progress status: {custom_data}")
            socketio.emit("progress_status", custom_data)
            self.stop_monitoring_event.wait(1)
