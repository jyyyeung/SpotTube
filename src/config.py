import logging
import os
from dataclasses import dataclass, field


@dataclass
class Config:
    """
    Config class for the application
    """

    credentials: dict[str, str]
    paths: dict[str, str]
    _sleep_interval: int = 0
    thread_limit: int = 1
    artist_track_selection: str = "all"
    ignored_keywords: list[str] = field(default_factory=list)
    logger: logging.Logger = logging.getLogger(__name__)

    def __init__(self):
        self._sleep_interval = os.environ.get("SLEEP_INTERVAL", 0)
        self.thread_limit = os.environ.get("THREAD_LIMIT", 1)
        self.artist_track_selection = os.environ.get("ARTIST_TRACK_SELECTION", "all")
        self.logger = logging.getLogger(__name__)
        self.credentials = {
            "spotify_client_id": os.environ.get("SPOTIFY_CLIENT_ID"),
            "spotify_client_secret": os.environ.get("SPOTIFY_CLIENT_SECRET"),
        }
        self.paths = {
            "download_folder": os.environ.get("DOWNLOAD_FOLDER", "downloads"),
            "config_folder": os.environ.get("CONFIG_FOLDER", "config"),
            "cookies_path": os.environ.get("COOKIES_PATH", "cookies.txt"),
            "ffmpeg_path": os.environ.get("FFMPEG_PATH", "/usr/bin/ffmpeg"),
        }

        self.ignored_keywords = []
        if os.environ.get("IGNORED_KEYWORDS"):
            self.ignored_keywords = os.environ.get("IGNORED_KEYWORDS", "").split(",")

    def __post_init__(self):
        if not os.path.exists(self.download_folder):
            os.makedirs(self.download_folder)
        if not os.path.exists(self.config_folder):
            os.makedirs(self.config_folder)

    @property
    def download_folder(self) -> str:
        """
        Returns the download folder
        """
        return self.paths["download_folder"]

    @download_folder.setter
    def download_folder(self, value: str):
        self.paths["download_folder"] = value

    @property
    def config_folder(self) -> str:
        """
        Returns the config folder
        """
        return self.paths["config_folder"]

    @config_folder.setter
    def config_folder(self, value: str):
        self.paths["config_folder"] = value

    @property
    def cookies_path(self) -> str:
        """
        Returns the cookies path
        """
        return self.paths["cookies_path"]

    @cookies_path.setter
    def cookies_path(self, value: str):
        self.paths["cookies_path"] = value

    @property
    def ffmpeg_path(self) -> str:
        """
        Returns the ffmpeg path
        """
        return self.paths["ffmpeg_path"]

    @ffmpeg_path.setter
    def ffmpeg_path(self, value: str):
        self.paths["ffmpeg_path"] = value

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
