from flask import Flask
from app.config import Config


app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# Store active downloads
app.downloads = {}

from app import routes