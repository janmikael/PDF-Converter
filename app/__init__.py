from flask import Flask
from app.config import Config


app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# Store active downloads
app.downloads = {}

# Store conversion status per task
app.conversion_status = {}

from app import routes