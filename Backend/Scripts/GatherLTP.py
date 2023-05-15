from kiteconnect import KiteTicker
from time import sleep
from datetime import datetime
import json
import threading 
import DBManager
from Log_Server_Interface import Log_Server_Interface
import OMS_API_Interface
from Config import Config
import time

def measure_performance(func):
  def wrapper(*args, **kwargs):
    start_time = time.perf_counter()
    result = func(*args, **kwargs)
    end_time = time.perf_counter()
    print(f"{func.__name__} took {end_time - start_time:.6f} seconds to complete")
    return result
  return wrapper


class GatherLTP:
    def __init__(self,kws: KiteTicker, log_interface: Log_Server_Interface, config: Config):
        try:
            self.log_interface = log_interface
            self.config = config
            self.log_interface.postLog("INFO","Initialising LTP gather thread.",1,"")
            self.kws = kws
            self.checked_rollovers = False
            self.SLEEP_TIME = datetime.strptime("15:31:00",'%H:%M:%S').time()
            self.ROLLOVER_TIME = datetime.strptime(config.ROLLOVER_TIME,'%H:%M:%S').time()
            self.OMS_interface = OMS_API_Interface.OMS_Interface(Config().OMS_SERVER_ADDRESS)
            self.START_TIME = datetime.now()
            self.tick_ctr = 0

            try:
                with open('../../NTDS/Data/Misc/instrument_tokens.json') as f:
                    instrument_token_json = json.load(f)
                
                with open('../../C/Data/lookup_table.json') as f:
                    self.lookup_table = json.load(f)

                with open('../Data/LTP_table.json','w') as f:
                    json.dump({},f,indent=2)
                
                with open('../Data/LTP_table.json') as f:
                    self.LTP_table = json.load(f)
            except:
                self.log_interface.postLog("CRITICAL","Failed to load vital jsons for LTP gathering.",1,"")

            self.instrument_token_list = instrument_token_json["instrument_tokens"]
        except:
            self.log_interface.postLog(severity="CRITICAL",message='Failed to initialise LTP gather module.',publish = 1, tag = 'OMSB_GLTP_1')
    
    def save_LTP_table(self):
        with open('../Data/LTP_table.json','w') as f:
            json.dump(self.LTP_table,f,indent=2)

    def start_LTP_thread(self):
        try:

            LTP_thread = threading.Thread(target = self.start, args = [])
            LTP_thread.start()
        except:
            self.log_interface.postLog(severity="CRITICAL",message='Failed to start LTP thread.',publish = 1, tag = 'OMSB_GLTP_2')

    def refresh_lookup_table(self):
        try:
            with open('../../C/Data/lookup_table.json') as f:
                self.lookup_table = json.load(f)
        except:
            self.log_interface.postLog(severity="CRITICAL",message='Failed to refresh lookup table.',publish = 1, tag = 'OMSB_GLTP_3')

    
    def start(self):
        try:
            self.kws.on_ticks = self.on_ticks
            self.kws.on_connect = self.on_connect
            self.kws.on_close = self.on_close
            self.kws.connect(threaded = True)
            count = 0
        except:
            self.log_interface.postLog(severity="CRITICAL",message='Failed to start KWS thread.',publish = 1, tag = 'OMSB_GLTP_4')

        while True:  
            count += 1
            if count%2 == 0:
                sleep(0.5)
                DBManager.update_net_position_values(self.log_interface)
            if datetime.now().time() > self.SLEEP_TIME:
                DBManager.clearOrderBuffer()
                return
    
    def update_ltp(self,ticks: list):
        try:
            for tick in ticks:
                instrument_token = tick['instrument_token']
                last_price = tick['last_price']
                self.refresh_lookup_table()
                self.LTP_table[instrument_token] = last_price
                self.save_LTP_table()
                if str(instrument_token) == '256265' or str(instrument_token) == '260105':
                    if str(instrument_token) == '256265':
                        self.tick_ctr += 1
                        DBManager.update_LTP_peg('NIFTY',last_price)
                    else:
                        DBManager.update_LTP_peg('BANKNIFTY',last_price)
                if str(instrument_token) in self.lookup_table:
                    DBManager.update_LTP(instrument_token=instrument_token,LTP=last_price)
                
            
        except:
            self.log_interface.postLog(severity="CRITICAL",message='Failed to update LTPs.',publish = 1, tag = 'OMSB_GLTP_5')
        
    def on_ticks(self,ws, ticks):
        # print("Gathering ticks")
        now = datetime.now()
        self.update_ltp(ticks)

    def on_connect(self,ws, response):

        ws.subscribe(self.instrument_token_list)

        # Set RELIANCE to tick in `full` mode.
        ws.set_mode(ws.MODE_LTP, self.instrument_token_list)

    def on_close(self,ws, code, reason):
        # On connection close stop the event loop.
        # Reconnection will not happen after executing `ws.stop()`
        pass
