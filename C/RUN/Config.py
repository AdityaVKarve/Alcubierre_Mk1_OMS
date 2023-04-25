import json
from Logs import logCritical
class Config:
    def __init__(self) -> None:
        self.refresh_config()

    def refresh_config(self):
        try:
            with open('../Config/OMS.json','r') as f:
                config_data = json.load(f)
            # self.LOG_SERVER_ADDRESS = 'http://15.207.12.225:9092/'
            
            # # self.ADS_SERVER_ADDRESS = 'http://15.207.12.225:8080/'
            # self.ADS_SERVER_ADDRESS = 'http://127.0.0.1:8080/'
            # self.OMS_SERVER_ADDRESS = 'http://127.0.0.1:8000/'
            
            # self.SUBSYSTEMS = 'OMS Server'
            # self.SUBSYSTEM = 'OMS Server'
            # self.DEFAULT_API_KEY = 'wd4rw474uonpvn94'
            # self.DEFAULT_API_SECRET = '8bsd661b6i29y064pei4riikj0lr3ede'
            # self.DEFAULT_ID = 'WG5235'
            # self.DEFAULT_PASSWORD = 'Finvant@Research'
            # self.DEFAULT_TOTP = 'TRRLO7QE5K5JYOBPT2C4GDO4KTN6TRKQ'
            # self.EXPIRY_MINUTES = 420
            # self.SECRET_KEY = "3092325@$@(234#24@$(8finvantResearchCapitalSecretKeyApi208u39324935@$#(*3@#(989898"

            self.LOG_SERVER_ADDRESS = config_data['LOG_SERVER_ADDRESS']
            self.ADS_SERVER_ADDRESS = config_data['ADS_SERVER_ADDRESS']
            self.OMS_SERVER_ADDRESS = config_data['OMS_SERVER_ADDRESS']
            self.SUBSYSTEMS = config_data['SUBSYSTEMS']
            self.SUBSYSTEM = config_data['SUBSYSTEM']
            self.DEFAULT_API_KEY = config_data['DEFAULT_API_KEY']
            self.DEFAULT_API_SECRET = config_data['DEFAULT_API_SECRET']
            self.DEFAULT_ID = config_data['DEFAULT_ID']
            self.DEFAULT_PASSWORD = config_data['DEFAULT_PASSWORD']
            self.DEFAULT_TOTP = config_data['DEFAULT_TOTP']
            self.EXPIRY_MINUTES = config_data['EXPIRY_MINUTES']
            self.SECRET_KEY = config_data['SECRET_KEY']
        except: 
            logCritical('Failed to get configs.',exit=True)