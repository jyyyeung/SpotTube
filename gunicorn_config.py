"""Gunicorn config"""

import os

from dotenv import load_dotenv

load_dotenv()

# Gunicorn config
# https://docs.gunicorn.org/en/stable/settings.html

bind = "0.0.0.0:" + os.environ.get("PORT", "5050")
workers = os.environ.get("WORKERS", 1)
threads = os.environ.get("THREADS", 4)
timeout = os.environ.get("TIMEOUT", 120)
worker_class = "geventwebsocket.gunicorn.workers.GeventWebSocketWorker"
