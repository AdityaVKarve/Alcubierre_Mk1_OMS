from datetime import datetime
from Config import Config
from AutoLoginDual import auto_login
from Log_Server_Interface import Log_Server_Interface
from kiteconnect import KiteTicker, KiteConnect
from PreProcessing import PreProcessing
import threading
from UpdateIndices import UpdateIndices

class Main:
    def __init__(self) -> None:
        self.run()

    def run(self):
        print("Starting")
        self.config_object = Config()
        self.kite,self.kws = auto_login(self.config_object)
        #self.log_server = Log_Server_Interface(self.config_object)
        #self.log_server.postLog(severity="INFO",message="Started NTDS",publish=1)
        pre_processing_object = PreProcessing(kite=self.kite)
        pre_processing_object.start()
        u = UpdateIndices()
        t1 = threading.Thread(target = u.fetchData, args=[self.kws])
        t1.start()
        print("Thread started")
    


m = Main()
