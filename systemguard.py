from src.config import app
from src import routes
from src.background_task import start_background_tasks
from src.config_loader import configuration_settings
# Start the background tasks
start_background_tasks()

if __name__ == "__main__":
    host = configuration_settings.get('webserver.test', 'HOST')
    port = configuration_settings.getint('webserver.test', 'PORT')
    debug = configuration_settings.getboolean('webserver.test', 'DEBUG', fallback=True)
    app.run(host="0.0.0.0",
            port=port, 
            debug=debug)
