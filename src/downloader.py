import concurrent.futures
import os
import tempfile
import threading
from dataclasses import dataclass, field

import yt_dlp  # type: ignore
from loguru import logger
from thefuzz import fuzz  # type: ignore
from ytmusicapi import YTMusic  # type: ignore

from src.aliases import Aliases
from src.config import Config
from src.status import DownloadStatus
from src.utils import string_cleaner

config = Config()


@dataclass
class Downloader:
    """
    Downloader class for the application
    """

    aliases: Aliases
    index: int = 0
    _stop_downloading_event: threading.Event = field(default_factory=threading.Event)
    running_flag: bool = False
    futures: list[concurrent.futures.Future] = field(default_factory=list)
    _download_list: list[dict] = field(default_factory=list)
    _status: DownloadStatus = DownloadStatus.UNKNOWN

    def __init__(self, aliases: Aliases):
        super().__init__()
        self.aliases = aliases
        self._stop_downloading_event = threading.Event()
        self._stop_downloading_event.clear()
        self._download_list = []
        self.running_flag = False
        self.futures = []

    def reset(self):
        """
        Reset the downloader
        """
        self._stop_downloading_event.clear()
        self.running_flag = False
        self.futures = []
        self.index = 0
        self._status = DownloadStatus.UNKNOWN

    @property
    def status(self) -> DownloadStatus:
        """
        Get the status

        Returns:
            DownloadStatus: The status
        """
        return self._status

    @status.setter
    def status(self, value: DownloadStatus):
        self._status = value

    @property
    def download_list(self) -> list[dict]:
        """
        Get the download list

        Returns:
            list[dict]: The download list
        """
        return self._download_list

    @download_list.setter
    def download_list(self, value: list[dict]):
        self._download_list = value

    @property
    def stop_downloading_event(self) -> threading.Event:
        """
        Get the stop downloading event

        Returns:
            threading.Event: The stop downloading event
        """
        return self._stop_downloading_event

    @stop_downloading_event.setter
    def stop_downloading_event(self, value: threading.Event):
        self._stop_downloading_event = value

    def find_youtube_link_and_download(self, song):
        """
        Find the YouTube link and download the song

        Args:
            song (dict): The song to download
        """
        try:
            found_link = self._find_youtube_link(song)
            if found_link:
                self._download_song(song, found_link)
            else:
                song["Status"] = DownloadStatus.NO_LINK_FOUND
                logger.warning(f"No Link Found for: {song['Artist']} - {song['Title']}")
        except Exception as e:
            logger.error(f"Error downloading song: {song['Title']}. Error message: {e}")
            song["Status"] = DownloadStatus.SEARCH_FAILED
        finally:
            self.index += 1

    def _find_youtube_link(self, song):
        """
        Find the YouTube link for the song

        Args:
            song (dict): The song to download
        """
        ytmusic = YTMusic()
        artist = song["Artist"]
        title = song["Title"]
        cleaned_artist = self._clean_artist_name(artist)
        cleaned_title = string_cleaner(title).lower()

        search_results = ytmusic.search(
            query=f"{artist} {title}", filter="songs", limit=5
        )
        found_link = self._search_for_link_in_results(
            search_results, cleaned_artist, cleaned_title
        )

        if not found_link:
            found_link = self._search_top_result(ytmusic, cleaned_title, cleaned_artist)

        return found_link

    def _clean_artist_name(self, artist):
        """
        Clean the artist name

        Args:
            artist (str): The artist name

        Returns:
            str: The cleaned artist name
        """
        return string_cleaner(self.aliases.get_name(artist)).lower()

    def _search_for_link_in_results(
        self, search_results, cleaned_artist, cleaned_title
    ):
        """
        Search for a link in the search results

        Args:
            search_results (list): The search results
        """
        for item in search_results:
            cleaned_youtube_title = string_cleaner(item["title"]).lower()
            if cleaned_title in cleaned_youtube_title:
                return f"https://www.youtube.com/watch?v={item['videoId']}"

        for item in search_results:
            if self._is_matching_artist_and_title(item, cleaned_artist, cleaned_title):
                return f"https://www.youtube.com/watch?v={item['videoId']}"

        return None

    def _is_matching_artist_and_title(
        self, item, cleaned_artist, cleaned_title
    ) -> bool:
        """
        Check if the item is a matching artist and title

        Args:
            item (dict): The item to check
            cleaned_artist (str): The cleaned artist name
            cleaned_title (str): The cleaned title

        Returns:
            bool: True if the item is a matching artist and title, False otherwise
        """
        cleaned_youtube_title = string_cleaner(item["title"]).lower()
        cleaned_youtube_artists = ", ".join(
            string_cleaner(x["name"]).lower() for x in item["artists"]
        )
        title_ratio = fuzz.ratio(cleaned_title, cleaned_youtube_title)
        artist_ratio = fuzz.ratio(cleaned_artist, cleaned_youtube_artists)
        return title_ratio >= 90 and artist_ratio >= 90

    def _search_top_result(self, ytmusic, cleaned_title, cleaned_artist):
        """
        Search for the top result

        Args:
            ytmusic (YTMusic): The YouTube music object
            cleaned_title (str): The cleaned title
        """
        top_search_results = ytmusic.search(query=cleaned_title, limit=5)
        if top_search_results:
            return self._evaluate_top_result(
                top_search_results[0], cleaned_artist, cleaned_title
            )
        return None

    def _evaluate_top_result(self, top_result, cleaned_artist, cleaned_title):
        """
        Evaluate the top result

        Args:
            top_result (dict): The top result
            cleaned_artist (str): The cleaned artist name
            cleaned_title (str): The cleaned title

        Returns:
            str: The found link
        """
        cleaned_youtube_title = string_cleaner(top_result["title"]).lower()
        cleaned_youtube_artists = ", ".join(
            string_cleaner(x["name"]).lower() for x in top_result["artists"]
        )
        title_ratio = fuzz.ratio(cleaned_title, cleaned_youtube_title)
        artist_ratio = fuzz.ratio(cleaned_artist, cleaned_youtube_artists)

        if (title_ratio >= 90 and artist_ratio >= 40) or (
            title_ratio >= 40 and artist_ratio >= 90
        ):
            return f"https://www.youtube.com/watch?v={top_result['videoId']}"
        return None

    def _download_song(self, song, found_link):
        """
        Download the song

        Args:
            song (dict): The song to download
            found_link (str): The found link
        """
        folder = song["Folder"]
        cleaned_artist_name = self.aliases.get_name(song["Artist"])
        file_name = os.path.join(
            string_cleaner(folder),
            f"{string_cleaner(song['Title'])} - {string_cleaner(cleaned_artist_name)}",
        )
        download_folder = config.download_folder
        full_file_path = os.path.join(download_folder, f"{file_name}.mp3")

        if os.path.exists(full_file_path):
            song["Status"] = DownloadStatus.FILE_ALREADY_EXISTS
            logger.warning(f"File Already Exists: {song['Artist']} - {song['Title']}")
            return

        self._perform_download(song, found_link, file_name)

    def _perform_download(self, song, found_link, file_name):
        """
        Perform the actual download of the song
        """
        temp_dir = None
        try:
            temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
            ydl_opts = self._get_ydl_options(file_name, temp_dir, song)
            yt_downloader = yt_dlp.YoutubeDL(ydl_opts)
            yt_downloader.download([found_link])
            song["Status"] = DownloadStatus.PROCESSING_COMPLETE
            logger.warning(f"yt_dl Complete: {found_link}")
            self._stop_downloading_event.wait(config.sleep_interval)
        except Exception as e:
            logger.error(f"Error downloading song: {found_link}. Error message: {e}")
            song["Status"] = DownloadStatus.DOWNLOAD_FAILED
        finally:
            if temp_dir is not None:
                temp_dir.cleanup()

    def _get_ydl_options(self, file_name, temp_dir, song):
        """
        Get the ydl options

        Args:
            file_name (str): The file name
            temp_dir (TemporaryDirectory): The temporary directory
            song (dict): The song to download

        Returns:
            dict: The ydl options
        """
        return {
            "logger": logger,
            "ffmpeg_location": config.ffmpeg_path,
            "format": "bestaudio",
            "outtmpl": f"{file_name}.%(ext)s",
            "paths": {
                "home": config.download_folder,
                "temp": temp_dir.name,
            },
            "quiet": False,
            "progress_hooks": [lambda d: self.progress_callback(d, song)],
            "writethumbnail": True,
            "updatetime": False,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "0",
                },
                {"key": "EmbedThumbnail"},
                {"key": "FFmpegMetadata"},
            ],
        }

    def progress_callback(self, d, song):
        """
        Progress callback for the download

        Args:
            d (dict): The download data
            song (dict): The song to download
        """
        if self.stop_downloading_event.is_set():
            raise Exception("Cancelled")
        if d["status"] == "finished":
            logger.warning("Download complete")
        elif d["status"] == "downloading":
            self._log_progress(d, song)

    def _log_progress(self, d, song):
        """
        Log the progress

        Args:
            d (dict): The download data
            song (dict): The song to download
        """
        logger.warning(
            f"Downloaded {d['_percent_str']} of {d['_total_bytes_str']} at {d['_speed_str']}"
        )
        percent_str = d["_percent_str"].replace("%", "").strip()
        song["Status"] = f"{percent_str}% Downloaded"

    def master_queue(self):
        """
        Master queue for the downloader
        """
        try:
            logger.debug("Master Queue Started")
            logger.debug(
                f"Download status: {self.status}, stop downloading event: {self.stop_downloading_event.is_set()}"
            )
            self.running_flag = True
            while not self.stop_downloading_event.is_set() and self.index < len(
                self.download_list
            ):
                self._status = DownloadStatus.RUNNING
                self._process_downloads()
            self.running_flag = False
            self._status = (
                DownloadStatus.COMPLETE
                if not self.stop_downloading_event.is_set()
                else DownloadStatus.STOPPED
            )
            logger.warning(
                "Finished" if not self.stop_downloading_event.is_set() else "Stopped"
            )
        except Exception as e:
            logger.error(f"Error in Master Queue: {str(e)}")
            self._status = DownloadStatus.ERROR
            self.running_flag = False

    def _process_downloads(self):
        """
        Process the downloads
        """
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=config.thread_limit
        ) as executor:
            self.futures = []
            start_position = self.index
            for song in self.download_list[start_position:]:
                if self.stop_downloading_event.is_set():
                    break
                logger.warning(
                    f"Searching for Song: {song['Title']} - {song['Artist']}"
                )
                self.futures.append(
                    executor.submit(self.find_youtube_link_and_download, song)
                )
            concurrent.futures.wait(self.futures)
