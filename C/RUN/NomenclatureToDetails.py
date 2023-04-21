import json
import time
import traceback
from APIhelper import ADS_Interface, LOG_Interface
import pandas as pd
from Config import Config

class NomeclatureToDetails:
    def __init__(self,url) -> None:
        self.config = Config()
        with open('../Data/spreads.json') as f:
            nom = json.load(f)
        # check 24 Hr refresh period
        if nom['LAST_UPDATE'] + 86400 < time.time():
            ads_interface = ADS_Interface(url)
            self.spreads = ads_interface.get_spreads() # 24H refrefresh period | using a record of spreads
            nom['LAST_UPDATE'] = time.time()
            nom['SPREADS'] = self.spreads
            with open('../Data/spreads.json','w') as f:
                json.dump(nom,f, indent=4)
        else:
            self.spreads = nom['SPREADS']
        self.log = LOG_Interface(self.config.LOG_SERVER_ADDRESS)

    def get_option(self,index:str,deviation:str,dev_amt:int,type:str,expiry_type:str,expiry_dev:int):
        if index == 'NIFTY':
            index_dev = dev_amt//100
        elif index == 'BANKNIFTY':
            index_dev = dev_amt//100
        if deviation == 'L':
            index_dev*=-1
        file_name = index+"_"+expiry_type+"_"+str(expiry_dev)+"_"+type
        # print('../../NTDS/Data/{}.csv'.format(file_name))
        file = pd.read_csv('../../NTDS/Data/{}.csv'.format(file_name))
        with open('../../NTDS/Data/Index.json') as f:
            index = json.load(f)
        option_pos = index[file_name] + index_dev
        option = file.iloc[[option_pos]]
        return {
            "INSTRUMENT_TOKEN":option['instrument_token'].iloc[0],
            "EXCHANGE_TOKEN":option['exchange_token'].iloc[0],
            "TRADINGSYMBOL":option['tradingsymbol'].iloc[0],
            "EXPIRY":option['expiry'].iloc[0],
            "SEGMENT":option['segment'].iloc[0],
            "EXCHANGE":option['exchange'].iloc[0],
            "LOT_SIZE":option['lot_size'].iloc[0]
        }

    def process_order_nomenclature(self,order_nomenclature: str):
        """ 
        To process the order representation and return the instrument details

        eg: N|L|200|CE|M|1 -> A mothly nifty call with strike price 200 less than market price, expiry 1 month from now
        eg: BN|G|100|PE|W|2 -> A weekly banknifty put with strike price 100 greater than market price, expiry 2 weeks from now
        """

        ## TODO: Add error handling
        ## TODO: Add a check to see if the instrument exists in the database
        
        ## Parsing order representation to get instrument details
        #Futures
        if order_nomenclature == 'NIFTY' or order_nomenclature == 'BANKNIFTY':
            with open('../../NTDS/Data/FUTURES.json') as f:
                future = json.load(f)
                # print(future)
                mesg = {
                    order_nomenclature:{
                        "SPREAD":False,
                        "INSTRUMENTS":[
                            future[order_nomenclature]
                        ]
                    }
                }
                # print(mesg)
                return mesg
            
        #SPREAD
        
        if order_nomenclature in self.spreads:
            spread = self.spreads[order_nomenclature]
            instruments = []
            index_peg = spread['INDEX_PEG']
            for options in spread['BUY']:
                option = options.split('|')
                index = option[0]
                deviation = option[1]
                dev_amt = int(option[2])
                type = option[3]
                expiry_type = option[4]
                expiry_dev = int(option[5])
                option_details = self.get_option(index=index,deviation=deviation,dev_amt=dev_amt,type=type,expiry_type=expiry_type,expiry_dev=expiry_dev)
                ratio = int(option[6])
                stoploss = int(option[7])
                target = int(option[8])
                instruments.append({
                    "POSITION":"BUY",
                    "RATIO":ratio,
                    "STOPLOSS":stoploss,
                    "TARGET":target,
                    "INSTRUMENT_TOKEN": int(option_details['INSTRUMENT_TOKEN']),
                    "EXCHANGE_TOKEN": int(option_details['EXCHANGE_TOKEN']),
                    "LOT_SIZE": int(option_details["LOT_SIZE"]),
                    "TRADINGSYMBOL": option_details['TRADINGSYMBOL'],
                    "EXPIRY": option_details['EXPIRY'],
                    "SEGMENT": option_details['SEGMENT'],
                    "EXCHANGE": option_details['EXCHANGE'],
                    "NOMENCLATURE": index+"|"+deviation+"|"+str(dev_amt)+"|"+type+"|"+expiry_type+"|"+str(expiry_dev)
                })
            for options in spread['OPEN SHORT']:
                option = options.split('|')
                
                index = option[0]
                deviation = option[1]
                dev_amt = int(option[2])
                type = option[3]
                expiry_type = option[4]
                expiry_dev = int(option[5])
                option_details = self.get_option(index=index,deviation=deviation,dev_amt=dev_amt,type=type,expiry_type=expiry_type,expiry_dev=expiry_dev)
                ratio = int(option[6])
                stoploss = int(option[7])
                target = int(option[8])
                instruments.append({
                    "POSITION":"OPEN SHORT",
                    "RATIO":ratio,
                    "STOPLOSS":stoploss,
                    "TARGET":target,
                    "INSTRUMENT_TOKEN": int(option_details['INSTRUMENT_TOKEN']),
                    "EXCHANGE_TOKEN": int(option_details['EXCHANGE_TOKEN']),
                    "TRADINGSYMBOL": option_details['TRADINGSYMBOL'],
                    "LOT_SIZE": int(option_details["LOT_SIZE"]),
                    "EXPIRY": option_details['EXPIRY'],
                    "SEGMENT": option_details['SEGMENT'],
                    "EXCHANGE": option_details['EXCHANGE'],
                    "NOMENCLATURE": index+"|"+deviation+"|"+str(dev_amt)+"|"+type+"|"+expiry_type+"|"+str(expiry_dev)
                })
            
            return {
                order_nomenclature:{
                    "SPREAD":True,
                    "INDEX_PEG":index_peg,
                    "INSTRUMENTS":instruments
                }
            }
        #Regular option
        try:
            option = order_nomenclature.split("|")
            index = option[0]
            deviation = option[1]
            dev_amt = int(option[2])
            type = option[3]
            expiry_type = option[4]
            expiry_dev = int(option[5])
            option_details = self.get_option(index=index,deviation=deviation,dev_amt=dev_amt,type=type,expiry_type=expiry_type,expiry_dev=expiry_dev)
            '''
            "INSTRUMENT_TOKEN": 14308610,
            "EXCHANGE_TOKEN": 55893,
            "LOT_SIZE": 50,
            "TRADINGSYMBOL": "NIFTY23JAN17950PE",
            "EXPIRY": "2023-01-25",
            "SEGMENT": "NFO-OPT",
            "EXCHANGE": "NFO"
            '''
            return {
                order_nomenclature:{
                    "SPREAD":False,
                    "INSTRUMENTS":[{
                        "INSTRUMENT_TOKEN": int(option_details['INSTRUMENT_TOKEN']),
                        "EXCHANGE_TOKEN": int(option_details['EXCHANGE_TOKEN']),
                        "LOT_SIZE": option_details['LOT_SIZE'],
                        "TRADINGSYMBOL": option_details['TRADINGSYMBOL'],
                        "EXPIRY": option_details['EXPIRY'],
                        "SEGMENT": option_details['SEGMENT'],
                        "EXCHANGE":option_details['EXCHANGE'],
                        "NOMENCLATURE":order_nomenclature
                    }]
                }
            }
        except Exception as e:
            print(e)
            traceback.print_exc()
            return "Invalid instrument!"




# print(process_order_representation('N|L|200|CE|M|1'))
# print(process_order_representation('BN|G|1000|PE|W|4'))
# ADS_URL = 'http://15.207.12.225:8080/'
# n = NomeclatureToDetails(ADS_URL)
# f1 = n.process_order_nomenclature("NIFTY|L|200|CE|MONTH|1")
# print(f1)