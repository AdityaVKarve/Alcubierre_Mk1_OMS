from datetime import datetime
from Config import Config
from AutoLoginDual import auto_login
from Log_Server_Interface import Log_Server_Interface
from kiteconnect import KiteTicker, KiteConnect
from PreProcessing import PreProcessing
import threading
from time import sleep
from UpdateIndices import UpdateIndices

class Main:
    def __init__(self) -> None:
        self.START_TIME = datetime.strptime("09:10:00",'%H:%M:%S').time()
        self.SLEEP_TIME = datetime.strptime("15:30:00",'%H:%M:%S').time()
        self.RUNNING = False
        self.run()
        
    def run(self):
        while True:
            if datetime.now().time() >= self.START_TIME and datetime.now().time() <= self.SLEEP_TIME and not self.RUNNING:
                self.config_object = Config()
                self.log_server_object = Log_Server_Interface(self.config_object)
                self.log_server_object.postLog("INFO",'Starting NTDS',1,'')
                try:
                    self.kite,self.kws = auto_login(self.config_object)
                except Exception as e:
                    self.log_server_object.postLog("CRITICAL",'Failed to log into kite accounts: {}'.format(e),1,'')
                    return
                
                try:
                    pre_processing_object = PreProcessing(kite=self.kite)
                    pre_processing_object.start()
                except Exception as e:
                    self.log_server_object.postLog("CRITICAL",'NTDS pre processing failed: {}'.format(e),1,'')
                    return
                
                try:
                    u = UpdateIndices()
                    t1 = threading.Thread(target = u.fetchData, args=[self.kws])
                    t1.start()
                except:
                    self.log_server_object.postLog("CRITICAL",'Failed to start update thread: {}'.format(e),1,'')
                    return
                self.RUNNING = True
            
            elif datetime.now().time() > self.SLEEP_TIME and self.RUNNING:
                self.RUNNING = False
            
            else:
                sleep(100)
    


m = Main()
