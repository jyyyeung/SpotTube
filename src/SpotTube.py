import logging
import os
import pathlib
import sys
import threading

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_socketio import SocketIO  # type: ignore

from src import db
from src.aliases import Aliases
from src.config import Config
from src.data import DataHandler
from src.downloader import Downloader
from src.spotify import SpotifyHandler

app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(
    SECRET_KEY="dev",  # Should be a random string when in production
    DATABASE=os.path.join(app.instance_path, "spottube.sqlite"),
)

# ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

socketio = SocketIO(app)

# Initialize everything within app context
with app.app_context():
    db.init_app(app)
    aliases = Aliases()
    aliases.import_from_file(pathlib.Path("files/aliases.yaml"))
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
        downloader.stop_downloading_event.clear()
        if not data_handler.monitor_active_flag:
            data_handler.stop_monitoring_event.clear()
            thread = threading.Thread(target=data_handler.monitor, args=(socketio,))
            thread.daemon = True
            thread.start()
            data_handler.monitor_active_flag = True

        link = data["Link"]
        ret = spotify_handler.spotify_extractor(link)
        if data_handler.status == "Complete":
            downloader.download_list = []
        downloader.download_list.extend(ret)

        if data_handler.status != "Running":
            data_handler.index = 0
            data_handler.status = "Running"
            thread = threading.Thread(target=downloader.master_queue)
            thread.daemon = True
            thread.start()

        ret = {"Status": "Success"}

    except Exception as e:
        data_handler.logger.error("Error Handling Download Request from UI: %s", str(e))
        ret = {"Status": "Error", "Data": str(e)}

    finally:
        socketio.emit("download", ret)


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
    data_handler.logger.warning("Clear List Request")
    downloader.stop_downloading_event.set()
    for future in downloader.futures:
        if not future.done():
            future.cancel()
    if not downloader.running_flag:
        downloader.download_list = []
        downloader.futures = []


def setup_logging():
    """
    Sets up the logging for the application
    """
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


if __name__ == "__main__":
    setup_logging()
    load_dotenv()
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
