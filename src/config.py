from dataclasses import dataclass
import logging
import os


@dataclass
class Config:
    """
    Config class for the application
    """

    credentials: dict
    ffmpeg_path: str = "/usr/bin/ffmpeg"
    cookies_path: str = "cookies.txt"
    download_folder: str = "downloads"
    config_folder: str = "config"
    sleep_interval: int = 0
    thread_limit: int = 1
    artist_track_selection: str = "all"
    logger: logging.Logger = logging.getLogger(__name__)

    def __init__(self):
        self.ffmpeg_path = os.environ.get("FFMPEG_PATH", "/usr/bin/ffmpeg")
        self.cookies_path = os.environ.get("COOKIES_PATH", "cookies.txt")
        self.download_folder = os.environ.get("DOWNLOAD_FOLDER", "downloads")
        self.sleep_interval = os.environ.get("SLEEP_INTERVAL", 0)
        self.thread_limit = os.environ.get("THREAD_LIMIT", 1)
        self.artist_track_selection = os.environ.get("ARTIST_TRACK_SELECTION", "all")
        self.config_folder = os.environ.get("CONFIG_FOLDER", "config")
        self.logger = logging.getLogger(__name__)
        self.credentials = {
            "spotify_client_id": os.environ.get("SPOTIFY_CLIENT_ID"),
            "spotify_client_secret": os.environ.get("SPOTIFY_CLIENT_SECRET"),
        }

    @property
    def spotify_client_id(self) -> str:
        """
        Returns the Spotify client ID
        """
        return self.credentials["spotify_client_id"]

    @property
    def spotify_client_secret(self) -> str:
        """
        Returns the Spotify client secret
        """
        return self.credentials["spotify_client_secret"]
