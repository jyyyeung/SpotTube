import logging
import os
from dataclasses import dataclass


@dataclass
class Config:
    """
    Config class for the application
    """

    credentials: dict[str, str]
    ffmpeg_path: str = "/usr/bin/ffmpeg"
    cookies_path: str = "cookies.txt"
    download_folder: str = "downloads"
    config_folder: str = "config"
    _sleep_interval: int = 0
    thread_limit: int = 1
    artist_track_selection: str = "all"
    logger: logging.Logger = logging.getLogger(__name__)

    def __init__(self):
        self.ffmpeg_path = os.environ.get("FFMPEG_PATH", "/usr/bin/ffmpeg")
        self.cookies_path = os.environ.get("COOKIES_PATH", "cookies.txt")
        self.download_folder = os.environ.get("DOWNLOAD_FOLDER", "downloads")
        self._sleep_interval = os.environ.get("SLEEP_INTERVAL", 0)
        self.thread_limit = os.environ.get("THREAD_LIMIT", 1)
        self.artist_track_selection = os.environ.get("ARTIST_TRACK_SELECTION", "all")
        self.config_folder = os.environ.get("CONFIG_FOLDER", "config")
        self.logger = logging.getLogger(__name__)
        self.credentials = {
            "spotify_client_id": os.environ.get("SPOTIFY_CLIENT_ID"),
            "spotify_client_secret": os.environ.get("SPOTIFY_CLIENT_SECRET"),
        }

    def __post_init__(self):
        if not os.path.exists(self.download_folder):
            os.makedirs(self.download_folder)
        if not os.path.exists(self.config_folder):
            os.makedirs(self.config_folder)

    @property
    def sleep_interval(self) -> int:
        """
        Returns the sleep interval
        """
        return self._sleep_interval

    @sleep_interval.setter
    def sleep_interval(self, value: int):
        self._sleep_interval = value

    @property
    def spotify_client_id(self) -> str:
        """
        Returns the Spotify client ID
        """
        return self.credentials["spotify_client_id"]

    @spotify_client_id.setter
    def spotify_client_id(self, value: str):
        self.credentials["spotify_client_id"] = value

    @property
    def spotify_client_secret(self) -> str:
        """
        Returns the Spotify client secret
        """
        return self.credentials["spotify_client_secret"]

    @spotify_client_secret.setter
    def spotify_client_secret(self, value: str):
        self.credentials["spotify_client_secret"] = value
