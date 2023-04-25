import json

class Config:
    def __init__(self) -> None:
        #TODO: Describe configs
        with open('../Config/Config.json') as f:
            self.config = json.load(f)
        self.KITE_API_KEY = self.config['BACKEND_KITE_API_KEY']
        self.KITE_API_SECRET = self.config['BACKEND_KITE_API_SECRET']
        self.KITE_ID = self.config['BACKEND_KITE_ID']
        self.KITE_PASSWORD = self.config['BACKEND_KITE_PASSWORD']
        self.KITE_TOTP = self.config['BACKEND_KITE_TOTP_PIN']
        self.LOG_SERVER_ADRESS = "15.207.12.225:9092/"
        self.SUBSYSTEMS = "NTDS"