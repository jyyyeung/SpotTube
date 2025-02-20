from enum import Enum
import logging
import threading
import concurrent.futures
from dataclasses import dataclass, field

from ytmusicapi import YTMusic  # type: ignore
import os
import tempfile
import yt_dlp  # type: ignore
from thefuzz import fuzz  # type: ignore

from src.config import Config
from src.utils import string_cleaner
from src.status import DownloadStatus


logger = logging.getLogger(__name__)
config = Config()


@dataclass
class Downloader:
    """
    Downloader class for the application
    """

    ytmusic: YTMusic
    index: int
    _stop_downloading_event: threading.Event
    running_flag: bool
    futures: list[concurrent.futures.Future] = field(default_factory=list)
    _download_list: list[dict] = field(default_factory=list)
    _status: DownloadStatus = DownloadStatus.UNKNOWN

    def __init__(self):
        super().__init__()
        self.ytmusic = YTMusic()
        self.index = 0
        self._download_list = []
        self._stop_downloading_event = threading.Event()

    @property
    def status(self) -> DownloadStatus:
        """
        Get the status of the download
        """
        return self._status

    @status.setter
    def status(self, value: DownloadStatus):
        self._status = value

    @property
    def download_list(self) -> list[dict]:
        """
        Get the download list
        """
        return self._download_list

    @property
    def stop_downloading_event(self) -> threading.Event:
        """
        Get the stop downloading event
        """
        return self._stop_downloading_event

    @stop_downloading_event.setter
    def stop_downloading_event(self, value: threading.Event):
        self._stop_downloading_event = value

    def find_youtube_link_and_download(self, song):
        """
        Finds the YouTube link and downloads the song
        """
        try:
            artist = song["Artist"]
            title = song["Title"]
            cleaned_artist = string_cleaner(artist).lower()
            cleaned_title = string_cleaner(title).lower()
            folder = song["Folder"]

            found_link = None
            search_results = self.ytmusic.search(
                query=artist + " " + title, filter="songs", limit=5
            )

            for item in search_results:
                cleaned_youtube_title = string_cleaner(item["title"]).lower()
                if cleaned_title in cleaned_youtube_title:
                    found_link = "https://www.youtube.com/watch?v=" + item["videoId"]
                    break
            else:
                # Try again but check for a partial match
                for item in search_results:
                    cleaned_youtube_title = string_cleaner(item["title"]).lower()
                    cleaned_youtube_artists = ", ".join(
                        string_cleaner(x["name"]).lower() for x in item["artists"]
                    )

                    title_ratio = (
                        100
                        if all(
                            word in cleaned_title
                            for word in cleaned_youtube_title.split()
                        )
                        else fuzz.ratio(cleaned_title, cleaned_youtube_title)
                    )
                    artist_ratio = (
                        100
                        if cleaned_artist in cleaned_youtube_artists
                        else fuzz.ratio(cleaned_artist, cleaned_youtube_artists)
                    )

                    if title_ratio >= 90 and artist_ratio >= 90:
                        found_link = (
                            "https://www.youtube.com/watch?v=" + item["videoId"]
                        )
                        break
                else:
                    # Default to first result if Top result is not found
                    found_link = (
                        "https://www.youtube.com/watch?v="
                        + search_results[0]["videoId"]
                    )

                    # Search for Top result specifically
                    top_search_results = self.ytmusic.search(
                        query=cleaned_title, limit=5
                    )
                    cleaned_youtube_title = string_cleaner(
                        top_search_results[0]["title"]
                    ).lower()
                    if (
                        "Top result" in top_search_results[0]["category"]
                        and top_search_results[0]["resultType"] == "song"
                        or top_search_results[0]["resultType"] == "video"
                    ):
                        cleaned_youtube_artists = ", ".join(
                            string_cleaner(x["name"]).lower()
                            for x in top_search_results[0]["artists"]
                        )
                        title_ratio = (
                            100
                            if cleaned_title in cleaned_youtube_title
                            else fuzz.ratio(cleaned_title, cleaned_youtube_title)
                        )
                        artist_ratio = (
                            100
                            if cleaned_artist in cleaned_youtube_artists
                            else fuzz.ratio(cleaned_artist, cleaned_youtube_artists)
                        )
                        if (title_ratio >= 90 and artist_ratio >= 40) or (
                            title_ratio >= 40 and artist_ratio >= 90
                        ):
                            found_link = (
                                "https://www.youtube.com/watch?v="
                                + top_search_results[0]["videoId"]
                            )

        except Exception as e:
            logger.error("Error downloading song: %s. Error message: %s", title, e)
            song["Status"] = "Search Failed"

        else:
            if found_link:
                song["Status"] = "Link Found"
                file_name = os.path.join(
                    string_cleaner(folder),
                    string_cleaner(title) + " - " + string_cleaner(artist),
                )
                download_folder = config.download_folder
                full_file_path = os.path.join(download_folder, f"{file_name}.mp3")

                if os.path.exists(full_file_path):
                    song["Status"] = "File Already Exists"
                    logger.warning("File Already Exists: " + artist + " " + title)
                else:
                    try:
                        temp_dir = tempfile.TemporaryDirectory(
                            ignore_cleanup_errors=True
                        )
                        ydl_opts = {
                            "logger": logger,
                            "ffmpeg_location": config.ffmpeg_path,
                            "format": "bestaudio",
                            "outtmpl": f"{file_name}.%(ext)s",
                            "paths": {
                                "home": download_folder,
                                "temp": temp_dir.name,
                            },
                            "quiet": False,
                            "progress_hooks": [
                                lambda d: self.progress_callback(d, song)
                            ],
                            "writethumbnail": True,
                            "updatetime": False,
                            "postprocessors": [
                                {
                                    "key": "FFmpegExtractAudio",
                                    "preferredcodec": "mp3",
                                    "preferredquality": "0",
                                },
                                {
                                    "key": "EmbedThumbnail",
                                },
                                {
                                    "key": "FFmpegMetadata",
                                },
                            ],
                        }
                        if config.cookies_path:
                            ydl_opts["cookiefile"] = config.cookies_path
                        yt_downloader = yt_dlp.YoutubeDL(ydl_opts)
                        yt_downloader.download([found_link])
                        logger.warning("yt_dl Complete : %s", found_link)
                        song["Status"] = "Processing Complete"

                        self._stop_downloading_event.wait(config.sleep_interval)

                    except Exception as e:
                        logger.error(
                            "Error downloading song: %s. Error message: %s",
                            found_link,
                            e,
                        )
                        song["Status"] = "Download Failed"

                    finally:
                        temp_dir.cleanup()

            else:
                song["Status"] = "No Link Found"
                logger.warning("No Link Found for: " + artist + " " + title)

        finally:
            self.index += 1

    def progress_callback(self, d, song):
        """
        Callback function for the progress of the download
        """
        if self._stop_downloading_event.is_set():
            raise Exception("Cancelled")
        if d["status"] == "finished":
            logger.warning("Download complete")

        elif d["status"] == "downloading":
            logger.warning(
                "Downloaded %s of %s at %s",
                d["_percent_str"],
                d["_total_bytes_str"],
                d["_speed_str"],
            )
            percent_str = d["_percent_str"].replace("%", "").strip()
            percent_complete = percent_str if percent_str else 0
            song["Status"] = f"{percent_complete}% Downloaded"

    def master_queue(self):
        """
        Master queue for the download
        """
        try:
            self.running_flag = True
            while not self._stop_downloading_event.is_set() and self.index < len(
                self.download_list
            ):
                self._status = DownloadStatus.RUNNING
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=config.thread_limit
                ) as executor:
                    self.futures = []
                    start_position = self.index
                    for song in self.download_list[start_position:]:
                        if self._stop_downloading_event.is_set():
                            break
                        logger.warning(
                            "Searching for Song: "
                            + song["Title"]
                            + " - "
                            + song["Artist"]
                        )
                        self.futures.append(
                            executor.submit(self.find_youtube_link_and_download, song)
                        )
                    concurrent.futures.wait(self.futures)

            self.running_flag = False
            if not self._stop_downloading_event.is_set():
                self._status = DownloadStatus.COMPLETE
                logger.warning("Finished")

            else:
                self._status = DownloadStatus.STOPPED
                logger.warning("Stopped")
                self.download_list = []

        except Exception as e:
            logger.error("Error in Master Queue: %s", str(e))
            self._status = DownloadStatus.ERROR
            logger.warning("Stopped")
            self.running_flag = False
