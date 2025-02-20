from dotenv import load_dotenv
import os

load_dotenv()

bind = "0.0.0.0:" + os.environ.get("PORT", "5000")
workers = 1
threads = 4
timeout = 120
worker_class = "geventwebsocket.gunicorn.workers.GeventWebSocketWorker"
