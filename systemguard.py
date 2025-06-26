from src.core.config.app_config import app
from src.infrastructure.http.initialize_clients import register_all_clients

register_all_clients()

from src import routes
from src import middleware
from src.tasks import start_background_tasks
from src.core.config.config_loader import configuration_settings

# Start the background tasks
start_background_tasks()



if __name__ == "__main__":
    host = configuration_settings.get('webserver.test', 'HOST')
    port = configuration_settings.getint('webserver.test', 'PORT')
    debug = configuration_settings.getboolean('webserver.test', 'DEBUG', fallback=True)
    app.run(host=host,
            port=port, 
            debug=debug)
