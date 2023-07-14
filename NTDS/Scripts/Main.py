from datetime import datetime,timedelta
from Config import Config
from AutoLoginDual import auto_login
from Log_Server_Interface import Log_Server_Interface
from kiteconnect import KiteTicker, KiteConnect
from PreProcessing import PreProcessing
import threading
from time import sleep
import Logs as logs
from UpdateIndices import UpdateIndices

# start = (datetime.combine(datetime.today(), datetime.now().time()) + timedelta(minutes=0)).time()
# end = (datetime.combine(datetime.today(), datetime.now().time()) + timedelta(minutes=45)).time()

class Main:
    def __init__(self) -> None:
        self.START_TIME = datetime.strptime("09:10:00",'%H:%M:%S').time()
        # self.START_TIME = (datetime.combine(datetime.today(), datetime.now().time()) + timedelta(minutes = 55)).time()
        self.SLEEP_TIME = datetime.strptime("15:30:00",'%H:%M:%S').time()
        # self.RUNNING = False
        self.run()
        
    def run(self):
        # while True:
            # if ((datetime.now().time() >= self.START_TIME and datetime.now().time() <= self.SLEEP_TIME) or (datetime.now().time() >= start and datetime.now().time() < end)) and not self.RUNNING:
            # if (datetime.now().time() >= self.START_TIME and datetime.now().time() < self.SLEEP_TIME):
        print(self.START_TIME,self.SLEEP_TIME)
        self.config_object = Config()
        self.log_server_object = Log_Server_Interface(self.config_object)
        self.log_server_object.postLog("INFO",'Starting NTDS',1,'')
        try:
            self.kite,self.kws = auto_login(self.config_object)
            # tmp_dict = {}
            # self.kite,tmp_dict = auto_login(self.config_object)
            
            # print(tmp_dict)
            
            # if (datetime.now().time() >= start and datetime.now().time() < end):
            #     print("changing access_token")
            #     tmp_dict['access_token'] = tmp_dict['access_token'][:-1] + 'X'
                
            
            # self.kws = KiteTicker(tmp_dict['key'], tmp_dict['access_token'])
            
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
            # t1 = threading.Thread(target = u.fetchData, args=[self.kws,end,self.START_TIME])
            t1 = threading.Thread(target = u.fetchData, args=[self.kws])
            t1.start()
            t1.join()
            
            return
        except:
            self.log_server_object.postLog("CRITICAL",'Failed to start update thread: {}'.format(e),1,'')
            return
            
                
            # self.RUNNING = True
        
        # elif (datetime.now().time() > end and datetime.now().time() < self.START_TIME) and self.RUNNING:
        # elif datetime.now().time() > self.SLEEP_TIME and self.RUNNING:
        
        #     print("making self.running false")
        #     self.RUNNING = False
        
        # else:
        #     print("sleeping for 100 seconds")
        #     sleep(100)
    
m = Main()
