import os
import pathlib
import sys
import threading

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_socketio import SocketIO  # type: ignore
from loguru import logger

from src import db
from src.aliases import Aliases
from src.config import Config
from src.data import DataHandler
from src.downloader import Downloader
from src.spotify import SpotifyHandler
from src.status import DownloadStatus

app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(
    SECRET_KEY=os.environ.get(
        "SECRET_KEY", "dev"
    ),  # Should be a random string when in production
    DATABASE=os.path.join(app.instance_path, "spottube.sqlite"),
)

socketio = SocketIO(app)

try:
    os.makedirs(app.instance_path)
except OSError:
    pass

# Initialize everything within app context
with app.app_context():
    db.init_app(app)
    db.init_db()
    aliases = Aliases()
    aliases.import_from_file(pathlib.Path("config/aliases.yaml"))
    print(aliases.aliases)

    spotify_handler = SpotifyHandler()
    downloader = Downloader(aliases)
    data_handler = DataHandler(downloader)
    config = Config()


@app.route("/")
def home():
    """
    Renders the base.html template
    """
    return render_template("base.html")


@socketio.on("download")
def download(data):
    """
    Downloads the data from the Spotify link
    """
    try:
        logger.warning(f"Download Request: {data}")
        downloader.stop_downloading_event.clear()
        if not data_handler.monitor_active_flag:
            logger.debug(f"Monitor Active Flag: {data_handler.monitor_active_flag}")
            data_handler.stop_monitoring_event.clear()
            thread = threading.Thread(target=data_handler.monitor, args=(socketio,))
            thread.daemon = True
            thread.start()
            data_handler.monitor_active_flag = True

        link = data["Link"]
        ret = spotify_handler.spotify_extractor(link)
        if downloader.status == DownloadStatus.COMPLETE:
            downloader.download_list = []
        downloader.download_list.extend(ret)
        logger.debug(f"Download List: {downloader.download_list}")
        logger.debug(f"Status: {downloader.status}")

        if downloader.status != DownloadStatus.RUNNING:
            logger.debug("Resetting Downloader")
            downloader.index = 0
            downloader.status = DownloadStatus.RUNNING
            thread = threading.Thread(target=downloader.master_queue)
            thread.daemon = True
            thread.start()

        ret = {"Status": "Success"}

    except Exception as e:
        logger.error(f"Error Handling Download Request from UI: {str(e)}")
        ret = {"Status": "Error", "Data": str(e)}

    finally:
        socketio.emit("download", ret)


@socketio.on("remove_track")
def remove_track(index: int):
    """
    Remove a track from the download list
    """
    logger.warning(f"Remove Track Request: {index}")
    downloader.download_list.pop(index)
    ret = {"Status": "Success"}
    socketio.emit("remove_track", ret)


@socketio.on("connect")
def connection():
    """
    Connects the client to the server
    """
    with app.app_context():
        if not data_handler.monitor_active_flag:
            data_handler.stop_monitoring_event.clear()
            thread = threading.Thread(target=data_handler.monitor, args=(socketio,))
            thread.daemon = True
            thread.start()
            data_handler.monitor_active_flag = True


@socketio.on("loadSettings")
def load_settings():
    """
    Loads the settings for the data handler
    """
    data = {
        "spotify_client_id": config.spotify_client_id,
        "spotify_client_secret": config.spotify_client_secret,
        "sleep_interval": config.sleep_interval,
        "ignored_keywords": config.ignored_keywords,
    }
    socketio.emit("settingsLoaded", data)


@socketio.on("updateSettings")
def update_settings(data):
    """
    Updates the settings for the data handler
    """
    config.spotify_client_id = data["spotify_client_id"]
    config.spotify_client_secret = data["spotify_client_secret"]
    config.sleep_interval = int(data["sleep_interval"])
    config.ignored_keywords = data["ignored_keywords"]
    logger.debug(f"Updated Settings: {config.__dict__}")


@socketio.on("disconnect")
def disconnect():
    """
    Disconnects the client from the server
    """
    data_handler.stop_monitoring_event.set()
    data_handler.monitor_active_flag = False


@socketio.on("clear")
def clear():
    """
    Clears the download list and cancels all futures
    """
    logger.warning("Clear List Request")
    downloader.stop_downloading_event.set()
    for future in downloader.futures:
        if not future.done():
            future.cancel()
    if not downloader.running_flag:
        downloader.download_list = []
        downloader.futures = []


def is_debug():
    """
    Returns True if the application is running in debug mode
    """
    return os.environ.get("DEBUG", "False").lower() == "true"


def setup_logging():
    """
    Sets up the logging for the application
    """
    if is_debug():
        level = "DEBUG"
    else:
        level = os.environ.get("LOG_LEVEL", "INFO")

    print(f"Setting up logging with level: {level}")

    logger.add(
        sys.stdout,
        colorize=True,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S",
        level=level,
    )


if __name__ == "__main__":
    load_dotenv()
    port = int(os.environ.get("PORT", 5050))
    setup_logging()
    debug = is_debug()
    socketio.run(app, host="0.0.0.0", port=port, debug=debug)
