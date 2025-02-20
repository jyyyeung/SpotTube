import logging
import spotipy  # type: ignore

from spotipy.oauth2 import SpotifyClientCredentials  # type: ignore
from spotipy_anon import SpotifyAnon  # type: ignore

from src.config import Config


class SpotifyHandler:
    """
    Handles the Spotify API
    """

    def __init__(self):
        self.config = Config()
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=self.config.spotify_client_id,
                client_secret=self.config.spotify_client_secret,
            )
        )
        self.sp_anon = spotipy.Spotify(auth_manager=SpotifyAnon())
        self.artist_track_selection = "top"
        self.logger = logging.getLogger(__name__)
        self.unique_tracks = set()

    def spotify_extractor(self, link):
        """
        Extracts the data from the Spotify link
        """
        if "artist" in link:
            return self._extract_tracks_from_artist(link)

        if "track" in link:
            return self._extract_tracks_from_track(link)

        if "album" in link:
            return self._extract_tracks_from_album(link)

        return self._extract_tracks_from_playlist(link)

    def append_if_unique(self, track_info) -> bool:
        """
        Appends the track info to the track list if it is unique
        """
        if (
            track_info["Artist"],
            track_info["Title"],
        ) not in self.unique_tracks:
            self.unique_tracks.add((track_info["Artist"], track_info["Title"]))
            return True
        return False

    def _extract_tracks_from_artist(self, link):
        """
        Extracts the tracks from the artist
        """
        artist_albums = []
        track_list = []
        offset = 0
        limit = 50

        artist_info = self.sp.artist(link)
        artist_name = artist_info.get("name", "Unknown Artist")

        if self.artist_track_selection == "top":
            try:
                top_tracks = self.sp.artist_top_tracks(link)
                for item in top_tracks["tracks"]:
                    track_title = item["name"]
                    artists = [artist["name"] for artist in item["artists"]]
                    artists_str = ", ".join(artists)
                    release_date = item.get("album", {}).get(
                        "release_date", "Unknown Date"
                    )
                    track_info = {
                        "Artist": artists_str,
                        "Title": track_title,
                        "Status": "Queued",
                        "Folder": artist_name,
                        "ReleaseDate": release_date,
                    }
                    if self.append_if_unique(track_info):
                        track_list.append(track_info)
                sorted_tracks = sorted(track_list, key=lambda x: x["ReleaseDate"])
                return sorted_tracks

            except Exception as e:
                self.logger.error("Error fetching artist's top tracks: %s", str(e))
                return []

        while True:
            try:
                response = self.sp.artist_albums(
                    link, include_groups="album,single", limit=limit, offset=offset
                )
                if response is None:
                    break
                albums = response.get("items", [])
                artist_albums.extend(albums)
                if response.get("next") is None:
                    break
                offset += limit

            except Exception as e:
                self.logger.error("Error fetching artist's albums: %s", str(e))
                break

        for album in artist_albums:
            album_id = album["id"]
            self.extract_tracks_from_artist_albums(album_id, artist_name)

        sorted_tracks = sorted(track_list, key=lambda x: x["ReleaseDate"])
        return sorted_tracks

    def extract_tracks_from_artist_albums(self, album_id, artist_name):
        """
        Extracts the tracks from the artist's albums
        """
        track_list = []
        album_name = ""
        try:
            album_info = self.sp.album(album_id)
            album_name = album_info["name"]
            release_date = album_info["release_date"]

            album_tracks = self.sp.album_tracks(album_id)
            for item in album_tracks["items"]:
                track_title = item["name"]
                artists = [artist["name"] for artist in item["artists"]]
                artists_str = ", ".join(artists)
                track_info = {
                    "Artist": artists_str,
                    "Title": track_title,
                    "Status": "Queued",
                    "Folder": artist_name,
                    "ReleaseDate": release_date,
                }
                if self.append_if_unique(track_info):
                    track_list.append(track_info)
                else:
                    pass

        except Exception as e:
            self.logger.error(
                "Error parsing track from album %s: %s", album_name, str(e)
            )
        return track_list

    def _extract_tracks_from_track(self, link):
        """
        Extracts the tracks from the track
        """
        track_list = []
        track_info = self.sp.track(link)
        album_name = track_info["album"]["name"]
        track_title = track_info["name"]
        artists = [artist["name"] for artist in track_info["artists"]]
        artists_str = ", ".join(artists)
        track_list.append(
            {
                "Artist": artists_str,
                "Title": track_title,
                "Status": "Queued",
                "Folder": "",
            }
        )
        return track_list

    def _extract_tracks_from_album(self, link):
        """
        Extracts the tracks from the album
        """
        album_info = self.sp.album(link)
        track_list = []
        album_name = album_info["name"]
        album = self.sp.album_tracks(link)
        for item in album["items"]:
            try:
                track_title = item["name"]
                artists = [artist["name"] for artist in item["artists"]]
                artists_str = ", ".join(artists)
                track_list.append(
                    {
                        "Artist": artists_str,
                        "Title": track_title,
                        "Status": "Queued",
                        "Folder": album_name,
                    }
                )

            except Exception as e:
                self.logger.error(
                    "Error Parsing Item in Album: %s - %s", str(item), str(e)
                )

        return track_list

    def _extract_tracks_from_playlist(self, link):
        """
        Extracts the tracks from the playlist
        """
        track_list = []
        try:
            playlist = self.sp.playlist(link)

        except Exception as e:
            self.logger.error(
                "Error using authenticated account to get playlist: %s.", str(e)
            )
            self.logger.info("Attempting to use anonymous authentication...")
            playlist = self.sp_anon.playlist(link)

        playlist_name = playlist["name"]
        number_of_tracks = playlist["tracks"]["total"]
        fields = "items(track(name,artists(name)),added_at)"

        offset = 0
        limit = 100
        all_items = []
        while offset < number_of_tracks:

            try:
                results = self.sp.playlist_items(
                    link, fields=fields, limit=limit, offset=offset
                )

            except Exception as e:
                self.logger.error(
                    "Error using authenticated account to get playlist: %s.", str(e)
                )
                self.logger.info("Attempting to use anonymous authentication...")
                results = self.sp_anon.playlist_items(
                    link, fields=fields, limit=limit, offset=offset
                )

            all_items.extend(results["items"])
            offset += limit

        all_items_sorted = sorted(all_items, key=lambda x: x["added_at"], reverse=False)
        for item in all_items_sorted:
            try:
                track = item["track"]
                track_title = track["name"]
                artists = [artist["name"] for artist in track["artists"]]
                artists_str = ", ".join(artists)
                track_list.append(
                    {
                        "Artist": artists_str,
                        "Title": track_title,
                        "Status": "Queued",
                        "Folder": playlist_name,
                    }
                )

            except Exception as e:
                self.logger.error(
                    "Error Parsing Item in Playlist: %s - %s", str(item), str(e)
                )

        return track_list
