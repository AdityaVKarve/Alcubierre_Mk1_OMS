import json
from Logs import logCritical
class Config:
    def __init__(self) -> None:
        self.refresh_config()

    def refresh_config(self):
        """ Refreshes the config data from the config file. """
        try:
            with open('../Config/OMS_Backend_Config.json','r') as f:
                config_data = json.load(f)

            self.LOG_SERVER_ADDRESS = config_data['LOG_SERVER_ADDRESS']
            self.ADS_SERVER_ADDRESS = config_data['ADS_SERVER_ADDRESS']
            self.OMS_SERVER_ADDRESS = config_data['OMS_SERVER_ADDRESS']
            self.SUBSYSTEMS = config_data['SUBSYSTEMS']
            self.DEFAULT_API_KEY = config_data['DEFAULT_API_KEY']
            self.DEFAULT_API_SECRET = config_data['DEFAULT_API_SECRET']
            self.DEFAULT_ID = config_data['DEFAULT_ID']
            self.DEFAULT_PASSWORD = config_data['DEFAULT_PASSWORD']
            self.DEFAULT_TOTP = config_data['DEFAULT_TOTP']
            self.ROLLOVER_TIME = config_data['ROLLOVER_TIME']
        except: 
            logCritical('Failed to get configs.',exit=True)
