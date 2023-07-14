from kiteconnect import KiteTicker,KiteConnect
from AutoLoginDual import automate_login
import re
from datetime import datetime
import time as t
import Logs as logs
import json


class UpdateIndices:
    def __init__(self) -> None:
        with open('../Data/Index.json') as f:
            self.index = json.load(f)

    def round_closest(self,x, base):
        return base * round(x/base)

    def save_json(self):
        with open('../Data/Index.json','w') as f:
            json.dump(self.index, f,indent=2)

    # def fetchData(self, kws_object: KiteTicker,start,end):
    def fetchData(self, kws_object: KiteTicker):
        
        '''
        Call this as a runnable thread only, or you will freeze up your code!
        Saves output to a csv
        '''

        logs.logInfo('inside fetch data function')
        
        self.running = 1   
        self.should_close = 0     
        
        self.kws = kws_object
        self.kws.on_ticks = self.on_ticks
        self.kws.on_connect = self.on_connect
        self.kws.on_close = self.on_close
        self.kws.connect(threaded=True)
        self.create_candle_time = None
        self.nifty_ltp = None
        self.banknifty_ltp = None
        count = 0
        
        print("Fetching data")
        while True:
            count += 1
            # print(count)
            if count%2 == 0:
                t.sleep(0.5)
    
            if datetime.now().time() > datetime.strptime('15:30:00','%H:%M:%S').time():
                print("closing websocket and stopping the reactor")
                self.kws.stop()
                return
            # if datetime.now().time() >= start and datetime.now().time() < end:             
            

    def on_ticks(self,ws, ticks):
        now = datetime.now()
        
        #NIFTY 256265
        for tick in ticks:
            if tick['instrument_token'] == 256265:
                nifty_ltp = tick['last_price']
                nifty_strike = self.round_closest(nifty_ltp,100)
                print(nifty_strike)
                if nifty_strike != self.index['CURRENT_NIFTY_STRIKE']:
                    dif = (nifty_strike - self.index['CURRENT_NIFTY_STRIKE'])//100
                    print("DIF: {}".format(dif))
                    for i in self.index.keys():
                        if i != 'CURRENT_NIFTY_STRIKE' and i != 'CURRENT_BANKNIFTY_STRIKE' and 'NIFTY' in i and 'BANKNIFTY' not in i:
                            self.index[i] += dif
                    self.index['CURRENT_NIFTY_STRIKE'] = nifty_strike
                    self.save_json()
            
            if tick['instrument_token'] == 260105:
                banknifty_ltp = tick['last_price']
                banknifty_strike = self.round_closest(banknifty_ltp,100)
                if banknifty_strike != self.index['CURRENT_BANKNIFTY_STRIKE']:
                    dif = (banknifty_strike - self.index['CURRENT_BANKNIFTY_STRIKE'])//100
                    for i in self.index.keys():
                        if i != 'CURRENT_NIFTY_STRIKE' and i != 'CURRENT_BANKNIFTY_STRIKE' and 'BANKNIFTY' in i:
                            self.index[i] += dif
                    self.index['CURRENT_BANKNIFTY_STRIKE'] = banknifty_strike
                    self.save_json()

        #BANKNIFTY 260105

    def on_connect(self,ws, response):
        print(self.kws.on_close)
        with open('../Data/Misc/instrument_tokens.json') as f:
            js = json.load(f)
        ws.subscribe(js["instrument_tokens"])

        # Set RELIANCE to tick in `full` mode.
        ws.set_mode(ws.MODE_LTP, js["instrument_tokens"])

    def on_close(self,ws,code,reason):
        # On connection close stop the event loop.
        # Reconnection will not happen after executing `ws.stop()`
        print("In on_close function")
        logs.logCritical(f"{code} , {reason}")
        
        pass
