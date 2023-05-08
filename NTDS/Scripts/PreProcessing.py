from kiteconnect import KiteConnect
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import json

class PreProcessing:
    '''
    This class will be called at 8:55 to create the initial dictionary
    This module stores monthly options at nearest expiry, +1 and +2, and weekly options at current, +1 and +2
    '''
    def __init__(self, kite: KiteConnect):
        self.kite = kite
        self.instrument_token_list = []

    def get_spot_ltp(self,kite:KiteConnect):
        '''
        Returns NIFTY LTP and BANKNIFTY LTP index as a list. 

        Arguments:
        self {self}
        kite {KiteConnect} -- kite object

        Keyword Arguments:
        None

        Returns:
        LTP {list} - [NIFTY and BANNKNIFTY LTP]
        '''
        NIFTY_LTP = kite.ltp(['NSE:NIFTY 50'])['NSE:NIFTY 50']['last_price']
        BANKNIFTY_LTP = kite.ltp(['NSE:NIFTY BANK'])['NSE:NIFTY BANK']['last_price']
        return [NIFTY_LTP,BANKNIFTY_LTP]
    
    def round_closest(self,x:float, base:int):
        '''
        Rounds to closest value to base (eg:17124 rounded to base 50 will return 17100). 

        Arguments:
        self {self}
        x {float} -- Number to be rounded
        base {float} -- Base to be rounded to

        Keyword Arguments:
        None

        Returns:
        rounded number {int} -- the rounded number
        '''
        return int(base * round(x/100))

    def get_trading_days_between(self,start: datetime,end: datetime):
        '''
        Returns trading days between 2 given dates 

        Arguments:
        self {self}
        start {datetime} -- The date from 
        end {datetime} -- The date to

        Keyword Arguments:
        None

        Returns:
        days between {int} -- the days between the 2 dates
        '''
        trading_holidays = pd.read_csv('../Config/trading_holidays.csv')
        dates = trading_holidays['Date'].tolist()
        ctr = 0
        while start < end:
            if start.strftime('%d-%b-%y') not in dates:
                if start.weekday() != 5 or start.weekday() != 6:
                    ctr += 1
            start += timedelta(days = 1)
        return ctr

    def get_months(self):
        '''
        Returns a list of months and years in the format [[month, year],[next month, year of next month]...] 
        Returns next 4 months 

        Arguments:
        self {self}

        Keyword Arguments:
        None

        Returns:
        months {list} -- the list of months and associated years
        '''
        now = datetime.now()
        current_month = now.month
        current_year = now.year
        next_month = current_month + 1
        next_year = current_year
        next_next_year = current_year
        next_next_next_year = current_year
        if next_month > 12:
            next_month -= 12
            next_year += 1
        next_next_month = current_month + 2
        if next_next_month > 12:
            next_next_month -= 12
            next_next_year += 1
        
        next_next_next_month = current_month + 3
        if next_next_next_month > 12:
            next_next_next_month -= 12
            next_next_next_year += 1
        
        return [[current_month,current_year], [next_month,next_year], [next_next_month,next_next_year], [next_next_next_month,next_next_next_year]]
    
    def get_monthly_expiries(self,expiries:list):
        '''
        Returns expiry for 3 months (current, next and next to next)

        Arguments:
        self {self}
        expiries {list} -- a list of all expiries obtained from kite.instruments()

        Keyword Arguments:
        None

        Returns:
        expiries {list} -- the list of expiries for this month, next month and next to next month
        '''
        months = self.get_months()
        current_month_expiry = None
        next_month_expiry = None
        next_next_month_expiry = None
        next_next_next_month_expiry = None
        for e in expiries:
            if (current_month_expiry == None or (current_month_expiry < e)) and (e.month == months[0][0] and e.year == months[0][1]):
                current_month_expiry = e

        if current_month_expiry == None:    #This happens when we are past expiry for the month
            for e in expiries:
                if (current_month_expiry == None or (current_month_expiry < e)) and (e.month == months[1][0] and e.year == months[1][1]):
                    current_month_expiry = e
            for e in expiries:
                if (next_month_expiry == None or (next_month_expiry < e)) and (e.month == months[2][0] and e.year == months[2][1]):
                    next_month_expiry = e
            
            for e in expiries:
                if (next_next_month_expiry == None or (next_next_month_expiry < e)) and (e.month == months[3][0] and e.year == months[3][1]):
                    next_next_month_expiry = e
            
            
        for e in expiries:
            if (next_month_expiry == None or (next_month_expiry < e)) and (e.month == months[1][0] and e.year == months[1][1]):
                next_month_expiry = e
        
        for e in expiries:
            if (next_next_month_expiry == None or (next_next_month_expiry < e)) and (e.month == months[2][0] and e.year == months[2][1]):
                next_next_month_expiry = e
        
        for e in expiries:
            if (next_next_next_month_expiry == None or (next_next_next_month_expiry < e)) and (e.month == months[3][0] and e.year == months[3][1]):
                next_next_next_month_expiry = e
        if self.get_trading_days_between(datetime.now(),current_month_expiry.to_pydatetime()) <= 30:
            return [next_month_expiry, next_next_month_expiry, next_next_next_month_expiry,current_month_expiry]
        
        return [current_month_expiry, next_month_expiry, next_next_month_expiry]
        
    def get_weekly_expiries(self, expiries:list):
        '''
        Returns expiry for 4 weeks (current, next and next to next...)

        Arguments:
        self {self}
        expiries {list} -- a list of all expiries obtained from kite.instruments()

        Keyword Arguments:
        None

        Returns:
        expiries {list} -- the list of expiries for the next 4 weeks.
        '''
        week_1 = None
        week_2 = None
        week_3 = None
        week_4 = None
        for e in expiries:
            if week_1 == None or e < week_1:
                week_1 = e
            
        for e in expiries:
            if (week_2 == None or (e < week_2)) and e > week_1:
                week_2 = e
            
        for e in expiries:
            if (week_3 == None or (e < week_3)) and e > week_2:
                week_3 = e
            
        for e in expiries:
            if (week_4 == None or (e < week_4)) and e > week_3:
                week_4 = e
        return [week_1,week_2,week_3,week_4]
    
    def get_futures(self, monthly_expiries:list, instruments:pd.DataFrame):
        '''
        Returns nifty and banknifty futures for the current month. Saves futures to a json.

        Arguments:
        self {self}
        monthly_expiries {list} -- a list of monthly expiries.
        instruments {DataFrame} -- A list of all instruments obtained through kite.instruments()
        Keyword Arguments:
        None

        Returns:
        None
        '''

        futures = instruments.loc[instruments['segment'] == 'NFO-FUT']
        nifty_current_month = futures.loc[instruments['name'] == 'NIFTY'].loc[instruments['expiry'] == monthly_expiries[0].to_pydatetime().date()].iloc[0]
        banknifty_current_month = futures.loc[instruments['name'] == 'BANKNIFTY'].loc[instruments['expiry'] == monthly_expiries[0].to_pydatetime().date()].iloc[0]

        if len(monthly_expiries) > 3:
            nifty_expired_month = futures.loc[instruments['name'] == 'NIFTY'].loc[instruments['expiry'] == monthly_expiries[-1].to_pydatetime().date()].iloc[0]
            banknifty_expired_month = futures.loc[instruments['name'] == 'BANKNIFTY'].loc[instruments['expiry'] == monthly_expiries[-1].to_pydatetime().date()].iloc[0]
            self.instrument_token_list.append(nifty_expired_month['instrument_token'])
            self.instrument_token_list.append(banknifty_expired_month['instrument_token'])

        futures = {
            "NIFTY":{
                "INSTRUMENT_TOKEN":int(nifty_current_month['instrument_token']),
                "EXCHANGE_TOKEN": int(nifty_current_month['exchange_token']),
                "TRADINGSYMBOL": nifty_current_month['tradingsymbol'],
                "LOT_SIZE": int(nifty_current_month['lot_size']),
                "EXPIRY": nifty_current_month['expiry'].strftime('%Y-%m-%d'),
                "SEGMENT": nifty_current_month['segment'],
                "EXCHANGE": nifty_current_month['exchange'],
                "NOMENCLATURE": "NIFTY"
            },
            "BANKNIFTY":{
                "INSTRUMENT_TOKEN":int(banknifty_current_month['instrument_token']),
                "EXCHANGE_TOKEN": int(banknifty_current_month['exchange_token']),
                "TRADINGSYMBOL": banknifty_current_month['tradingsymbol'],
                "LOT_SIZE": int(banknifty_current_month['lot_size']),
                "EXPIRY": banknifty_current_month['expiry'].strftime('%Y-%m-%d'),
                "SEGMENT": banknifty_current_month['segment'],
                "EXCHANGE": banknifty_current_month['exchange'],
                "NOMENCLATURE": "BANKNIFTY"
            }
        }
        self.NIFTY_INSTRUMENT_TOKEN = int(nifty_current_month['instrument_token'])
        self.BANKNIFTY_INSTRUMENT_TOKEN = int(banknifty_current_month['instrument_token'])
        with open('../Data/FUTURES.json','w') as f:
            json.dump(futures,f,indent=2)

        

    def start(self):
        '''
        Call this method from main to carry out the pre-processing.

        Arguments:
        Keyword Arguments:
        None

        Returns:
        None
        '''
        instruments = pd.DataFrame(self.kite.instruments())
        instruments.to_csv('../Data/Misc/instruments.csv')
        all_nifty_options = instruments.loc[instruments['segment'] == 'NFO-OPT'].loc[instruments['name'] == 'NIFTY']
        all_banknifty_options = instruments.loc[instruments['segment'] == 'NFO-OPT'].loc[instruments['name'] == 'BANKNIFTY']
        all_nifty_options['expiry'] = pd.to_datetime(all_nifty_options['expiry'], format='%Y-%m-%d')
        all_banknifty_options['expiry'] = pd.to_datetime(all_banknifty_options['expiry'], format='%Y-%m-%d')

        
        expiry_date_list = all_nifty_options['expiry'].drop_duplicates().tolist()

        expiry_monthly = self.get_monthly_expiries(expiry_date_list)
        expiry_weekly = self.get_weekly_expiries(expiry_date_list)

        self.get_futures(monthly_expiries = expiry_monthly, instruments = instruments)

        nifty_ltp, banknifty_ltp = self.get_spot_ltp(self.kite)
        nifty_strike = self.round_closest(nifty_ltp,100)
        banknifty_strike = self.round_closest(banknifty_ltp,100)
        range_min_nifty = nifty_ltp*0.9 #We will only store values within this range
        range_max_nifty = nifty_ltp*1.1
        range_min_banknifty = banknifty_ltp*0.9
        range_max_banknifty = banknifty_ltp*1.1
        
        self.instrument_token_list.append(self.NIFTY_INSTRUMENT_TOKEN)
        self.instrument_token_list.append(self.BANKNIFTY_INSTRUMENT_TOKEN)
        self.instrument_token_list.append(256265)
        self.instrument_token_list.append(260105)
        ####MONTHLY OPTIONS START####
        
        #Expired monthly options
        if len(expiry_monthly) > 3:
            nifty_expired_month_options = all_nifty_options.loc[all_nifty_options['expiry'] == expiry_monthly[-1]]
            nifty_expired_month_call = nifty_expired_month_options.loc[nifty_expired_month_options['instrument_type'] == 'CE'].loc[nifty_expired_month_options['strike'] > range_min_nifty].loc[nifty_expired_month_options['strike'] < range_max_nifty].sort_values(by=['strike']).reset_index(drop=True)
            nifty_expired_month_put = nifty_expired_month_options.loc[nifty_expired_month_options['instrument_type'] == 'PE'].loc[nifty_expired_month_options['strike'] > range_min_nifty].loc[nifty_expired_month_options['strike'] < range_max_nifty].sort_values(by=['strike']).reset_index(drop=True)
            self.instrument_token_list += nifty_expired_month_call['instrument_token'].tolist()
            self.instrument_token_list += nifty_expired_month_put['instrument_token'].tolist()

            banknifty_expired_month_options = all_banknifty_options.loc[all_banknifty_options['expiry'] == expiry_monthly[-1]]
            banknifty_expired_month_call = banknifty_expired_month_options.loc[banknifty_expired_month_options['instrument_type'] == 'CE'].loc[banknifty_expired_month_options['strike'] > range_min_banknifty].loc[banknifty_expired_month_options['strike'] < range_max_banknifty].sort_values(by=['strike']).reset_index(drop=True)
            banknifty_expired_month_put = banknifty_expired_month_options.loc[banknifty_expired_month_options['instrument_type'] == 'PE'].loc[banknifty_expired_month_options['strike'] > range_min_banknifty].loc[banknifty_expired_month_options['strike'] < range_max_banknifty].sort_values(by=['strike']).reset_index(drop=True)
            self.instrument_token_list += banknifty_expired_month_call['instrument_token'].tolist()
            self.instrument_token_list += banknifty_expired_month_put['instrument_token'].tolist()

        #NIFTY
        nifty_current_month_options = all_nifty_options.loc[all_nifty_options['expiry'] == expiry_monthly[0]]
        nifty_current_month_call = nifty_current_month_options.loc[nifty_current_month_options['instrument_type'] == 'CE'].loc[nifty_current_month_options['strike'] > range_min_nifty].loc[nifty_current_month_options['strike'] < range_max_nifty].loc[nifty_current_month_options['strike']%100==0].sort_values(by=['strike']).reset_index(drop=True)
        nifty_current_month_put = nifty_current_month_options.loc[nifty_current_month_options['instrument_type'] == 'PE'].loc[nifty_current_month_options['strike'] > range_min_nifty].loc[nifty_current_month_options['strike'] < range_max_nifty].loc[nifty_current_month_options['strike']%100==0].sort_values(by=['strike']).reset_index(drop=True)
        self.instrument_token_list += nifty_current_month_call['instrument_token'].tolist()
        self.instrument_token_list += nifty_current_month_put['instrument_token'].tolist()
        

        nifty_next_month_options = all_nifty_options.loc[all_nifty_options['expiry'] == expiry_monthly[1]]
        nifty_next_month_call = nifty_next_month_options.loc[nifty_next_month_options['instrument_type'] == 'CE'].loc[nifty_next_month_options['strike'] > range_min_nifty].loc[nifty_next_month_options['strike'] < range_max_nifty].loc[nifty_next_month_options['strike']%100==0].sort_values(by=['strike']).reset_index(drop=True)
        nifty_next_month_put = nifty_next_month_options.loc[nifty_next_month_options['instrument_type'] == 'PE'].loc[nifty_next_month_options['strike'] > range_min_nifty].loc[nifty_next_month_options['strike'] < range_max_nifty].loc[nifty_next_month_options['strike']%100==0].sort_values(by=['strike']).reset_index(drop=True)
        self.instrument_token_list += nifty_next_month_call['instrument_token'].tolist()
        self.instrument_token_list += nifty_next_month_put['instrument_token'].tolist()

        nifty_next_next_month_options = all_nifty_options.loc[all_nifty_options['expiry'] == expiry_monthly[2]]
        nifty_next_next_month_call = nifty_next_next_month_options.loc[nifty_next_next_month_options['instrument_type'] == 'CE'].loc[nifty_next_next_month_options['strike'] > range_min_nifty].loc[nifty_next_next_month_options['strike'] < range_max_nifty].loc[nifty_next_next_month_options['strike']%100==0].sort_values(by=['strike']).reset_index(drop=True)
        nifty_next_next_month_put = nifty_next_next_month_options.loc[nifty_next_next_month_options['instrument_type'] == 'PE'].loc[nifty_next_next_month_options['strike'] > range_min_nifty].loc[nifty_next_next_month_options['strike'] < range_max_nifty].loc[nifty_next_next_month_options['strike']%100==0].sort_values(by=['strike']).reset_index(drop=True)
        self.instrument_token_list += nifty_next_next_month_call['instrument_token'].tolist()
        self.instrument_token_list += nifty_next_next_month_put['instrument_token'].tolist()

        #BANKNIFTY
        banknifty_current_month_options = all_banknifty_options.loc[all_banknifty_options['expiry'] == expiry_monthly[0]]
        banknifty_current_month_call = banknifty_current_month_options.loc[banknifty_current_month_options['instrument_type'] == 'CE'].loc[banknifty_current_month_options['strike'] > range_min_banknifty].loc[banknifty_current_month_options['strike'] < range_max_banknifty].sort_values(by=['strike']).reset_index(drop=True)
        banknifty_current_month_put = banknifty_current_month_options.loc[banknifty_current_month_options['instrument_type'] == 'PE'].loc[banknifty_current_month_options['strike'] > range_min_banknifty].loc[banknifty_current_month_options['strike'] < range_max_banknifty].sort_values(by=['strike']).reset_index(drop=True)
        self.instrument_token_list += banknifty_current_month_call['instrument_token'].tolist()
        self.instrument_token_list += banknifty_current_month_put['instrument_token'].tolist()
        
        banknifty_next_month_options = all_banknifty_options.loc[all_banknifty_options['expiry'] == expiry_monthly[1]]
        banknifty_next_month_call = banknifty_next_month_options.loc[banknifty_next_month_options['instrument_type'] == 'CE'].loc[banknifty_next_month_options['strike'] > range_min_banknifty].loc[banknifty_next_month_options['strike'] < range_max_banknifty].sort_values(by=['strike']).reset_index(drop=True)
        banknifty_next_month_put = banknifty_next_month_options.loc[banknifty_next_month_options['instrument_type'] == 'PE'].loc[banknifty_next_month_options['strike'] > range_min_banknifty].loc[banknifty_next_month_options['strike'] < range_max_banknifty].sort_values(by=['strike']).reset_index(drop=True)
        self.instrument_token_list += banknifty_next_month_call['instrument_token'].tolist()
        self.instrument_token_list += banknifty_next_month_put['instrument_token'].tolist()

        banknifty_next_next_month_options = all_banknifty_options.loc[all_banknifty_options['expiry'] == expiry_monthly[2]]
        banknifty_next_next_month_call = banknifty_next_next_month_options.loc[banknifty_next_next_month_options['instrument_type'] == 'CE'].loc[banknifty_next_next_month_options['strike'] > range_min_banknifty].loc[banknifty_next_next_month_options['strike'] < range_max_banknifty].sort_values(by=['strike']).reset_index(drop=True)
        banknifty_next_next_month_put = banknifty_next_next_month_options.loc[banknifty_next_next_month_options['instrument_type'] == 'PE'].loc[banknifty_next_next_month_options['strike'] > range_min_banknifty].loc[banknifty_next_next_month_options['strike'] < range_max_banknifty].sort_values(by=['strike']).reset_index(drop=True)
        self.instrument_token_list += banknifty_next_next_month_call['instrument_token'].tolist()
        self.instrument_token_list += banknifty_next_next_month_put['instrument_token'].tolist()
        ####MONTHLY OPTIONS END####
        

        #WEEKLY OPTIONS

        #NIFTY
        nifty_current_week_options = all_nifty_options.loc[all_nifty_options['expiry'] == expiry_weekly[0]]
        nifty_current_week_call = nifty_current_week_options.loc[nifty_current_week_options['instrument_type'] == 'CE'].loc[nifty_current_week_options['strike'] > range_min_nifty].loc[nifty_current_week_options['strike'] < range_max_nifty].loc[nifty_current_week_options['strike']%100==0].sort_values(by=['strike']).reset_index(drop=True)
        nifty_current_week_put = nifty_current_week_options.loc[nifty_current_week_options['instrument_type'] == 'PE'].loc[nifty_current_week_options['strike'] > range_min_nifty].loc[nifty_current_week_options['strike'] < range_max_nifty].loc[nifty_current_week_options['strike']%100==0].sort_values(by=['strike']).reset_index(drop=True)
        self.instrument_token_list += nifty_current_week_call['instrument_token'].tolist()
        self.instrument_token_list += nifty_current_week_put['instrument_token'].tolist()

        nifty_next_week_options = all_nifty_options.loc[all_nifty_options['expiry'] == expiry_weekly[1]]
        nifty_next_week_call = nifty_next_week_options.loc[nifty_next_week_options['instrument_type'] == 'CE'].loc[nifty_next_week_options['strike'] > range_min_nifty].loc[nifty_next_week_options['strike'] < range_max_nifty].loc[nifty_next_week_options['strike']%100==0].sort_values(by=['strike']).reset_index(drop=True)
        nifty_next_week_put = nifty_next_week_options.loc[nifty_next_week_options['instrument_type'] == 'PE'].loc[nifty_next_week_options['strike'] > range_min_nifty].loc[nifty_next_week_options['strike'] < range_max_nifty].loc[nifty_next_week_options['strike']%100==0].sort_values(by=['strike']).reset_index(drop=True)
        self.instrument_token_list += nifty_next_week_call['instrument_token'].tolist()
        self.instrument_token_list += nifty_next_week_put['instrument_token'].tolist()

        nifty_next_next_week_options = all_nifty_options.loc[all_nifty_options['expiry'] == expiry_weekly[2]]
        nifty_next_next_week_call = nifty_next_next_week_options.loc[nifty_next_next_week_options['instrument_type'] == 'CE'].loc[nifty_next_next_week_options['strike'] > range_min_nifty].loc[nifty_next_next_week_options['strike'] < range_max_nifty].loc[nifty_next_next_week_options['strike']%100==0].sort_values(by=['strike']).reset_index(drop=True)
        nifty_next_next_week_put = nifty_next_next_week_options.loc[nifty_next_next_week_options['instrument_type'] == 'PE'].loc[nifty_next_next_week_options['strike'] > range_min_nifty].loc[nifty_next_next_week_options['strike'] < range_max_nifty].loc[nifty_next_next_week_options['strike']%100==0].sort_values(by=['strike']).reset_index(drop=True)
        self.instrument_token_list += nifty_next_next_week_call['instrument_token'].tolist()
        self.instrument_token_list += nifty_next_next_week_put['instrument_token'].tolist()


        nifty_next_next_next_week_options = all_nifty_options.loc[all_nifty_options['expiry'] == expiry_weekly[3]]
        nifty_next_next_next_week_call = nifty_next_next_next_week_options.loc[nifty_next_next_next_week_options['instrument_type'] == 'CE'].loc[nifty_next_next_next_week_options['strike'] > range_min_nifty].loc[nifty_next_next_next_week_options['strike'] < range_max_nifty].loc[nifty_next_next_next_week_options['strike']%100==0].sort_values(by=['strike']).reset_index(drop=True)
        nifty_next_next_next_week_put = nifty_next_next_next_week_options.loc[nifty_next_next_next_week_options['instrument_type'] == 'PE'].loc[nifty_next_next_next_week_options['strike'] > range_min_nifty].loc[nifty_next_next_next_week_options['strike'] < range_max_nifty].loc[nifty_next_next_next_week_options['strike']%100==0].sort_values(by=['strike']).reset_index(drop=True)
        self.instrument_token_list += nifty_next_next_next_week_call['instrument_token'].tolist()
        self.instrument_token_list += nifty_next_next_next_week_put['instrument_token'].tolist()

        #BANKNIFTY
        banknifty_current_week_options = all_banknifty_options.loc[all_banknifty_options['expiry'] == expiry_weekly[0]]
        banknifty_current_week_call = banknifty_current_week_options.loc[banknifty_current_week_options['instrument_type'] == 'CE'].loc[banknifty_current_week_options['strike'] > range_min_banknifty].loc[banknifty_current_week_options['strike'] < range_max_banknifty].sort_values(by=['strike']).reset_index(drop=True)
        banknifty_current_week_put = banknifty_current_week_options.loc[banknifty_current_week_options['instrument_type'] == 'PE'].loc[banknifty_current_week_options['strike'] > range_min_banknifty].loc[banknifty_current_week_options['strike'] < range_max_banknifty].sort_values(by=['strike']).reset_index(drop=True)
        self.instrument_token_list += banknifty_current_week_call['instrument_token'].tolist()
        self.instrument_token_list += banknifty_current_week_put['instrument_token'].tolist()

        banknifty_next_week_options = all_banknifty_options.loc[all_banknifty_options['expiry'] == expiry_weekly[1]]
        banknifty_next_week_call = banknifty_next_week_options.loc[banknifty_next_week_options['instrument_type'] == 'CE'].loc[banknifty_next_week_options['strike'] > range_min_banknifty].loc[banknifty_next_week_options['strike'] < range_max_banknifty].sort_values(by=['strike']).reset_index(drop=True)
        banknifty_next_week_put = banknifty_next_week_options.loc[banknifty_next_week_options['instrument_type'] == 'PE'].loc[banknifty_next_week_options['strike'] > range_min_banknifty].loc[banknifty_next_week_options['strike'] < range_max_banknifty].sort_values(by=['strike']).reset_index(drop=True)
        self.instrument_token_list += banknifty_next_week_call['instrument_token'].tolist()
        self.instrument_token_list += banknifty_next_week_put['instrument_token'].tolist()

        banknifty_next_next_week_options = all_banknifty_options.loc[all_banknifty_options['expiry'] == expiry_weekly[2]]
        banknifty_next_next_week_call = banknifty_next_next_week_options.loc[banknifty_next_next_week_options['instrument_type'] == 'CE'].loc[banknifty_next_next_week_options['strike'] > range_min_banknifty].loc[banknifty_next_next_week_options['strike'] < range_max_banknifty].sort_values(by=['strike']).reset_index(drop=True)
        banknifty_next_next_week_put = banknifty_next_next_week_options.loc[banknifty_next_next_week_options['instrument_type'] == 'PE'].loc[banknifty_next_next_week_options['strike'] > range_min_banknifty].loc[banknifty_next_next_week_options['strike'] < range_max_banknifty].sort_values(by=['strike']).reset_index(drop=True)
        self.instrument_token_list += banknifty_next_next_week_call['instrument_token'].tolist()
        self.instrument_token_list += banknifty_next_next_week_put['instrument_token'].tolist()


        banknifty_next_next_next_week_options = all_banknifty_options.loc[all_banknifty_options['expiry'] == expiry_weekly[2]]
        banknifty_next_next_next_week_call = banknifty_next_next_next_week_options.loc[banknifty_next_next_next_week_options['instrument_type'] == 'CE'].loc[banknifty_next_next_next_week_options['strike'] > range_min_banknifty].loc[banknifty_next_next_next_week_options['strike'] < range_max_banknifty].sort_values(by=['strike']).reset_index(drop=True)
        banknifty_next_next_next_week_put = banknifty_next_next_next_week_options.loc[banknifty_next_next_next_week_options['instrument_type'] == 'PE'].loc[banknifty_next_next_next_week_options['strike'] > range_min_banknifty].loc[banknifty_next_next_next_week_options['strike'] < range_max_banknifty].sort_values(by=['strike']).reset_index(drop=True)
        self.instrument_token_list += banknifty_next_next_next_week_call['instrument_token'].tolist()
        self.instrument_token_list += banknifty_next_next_next_week_put['instrument_token'].tolist()

        #Save to folder
        #Current month
        pd.DataFrame(nifty_current_month_call).to_csv("../Data/NIFTY_MONTH_0_CE.csv")
        pd.DataFrame(nifty_current_month_put).to_csv("../Data/NIFTY_MONTH_0_PE.csv")
        pd.DataFrame(banknifty_current_month_call).to_csv("../Data/BANKNIFTY_MONTH_0_CE.csv")
        pd.DataFrame(banknifty_current_month_put).to_csv("../Data/BANKNIFTY_MONTH_0_PE.csv")

        #Month + 1
        pd.DataFrame(nifty_next_month_call).to_csv("../Data/NIFTY_MONTH_1_CE.csv")
        pd.DataFrame(nifty_next_month_put).to_csv("../Data/NIFTY_MONTH_1_PE.csv")
        pd.DataFrame(banknifty_next_month_call).to_csv("../Data/BANKNIFTY_MONTH_1_CE.csv")
        pd.DataFrame(banknifty_next_month_put).to_csv("../Data/BANKNIFTY_MONTH_1_PE.csv")

        #Month + 2
        #pd.DataFrame(nifty_next_next_month_call).to_csv("../Data/NIFTY_MONTH_2_CE.csv")
        #pd.DataFrame(nifty_next_next_month_put).to_csv("../Data/NIFTY_MONTH_2_PE.csv")
        #pd.DataFrame(banknifty_next_next_month_call).to_csv("../Data/BANKNIFTY_MONTH_2_CE.csv")
        #pd.DataFrame(banknifty_next_next_month_put).to_csv("../Data/BANKNIFTY_MONTH_2_PE.csv")

        #Current week
        pd.DataFrame(nifty_current_week_call).to_csv("../Data/NIFTY_WEEK_0_CE.csv")
        pd.DataFrame(nifty_current_week_put).to_csv("../Data/NIFTY_WEEK_0_PE.csv")
        pd.DataFrame(banknifty_current_week_call).to_csv("../Data/BANKNIFTY_WEEK_0_CE.csv")
        pd.DataFrame(banknifty_current_week_put).to_csv("../Data/BANKNIFTY_WEEK_0_PE.csv")

        #Week + 1
        pd.DataFrame(nifty_next_week_call).to_csv("../Data/NIFTY_WEEK_1_CE.csv")
        pd.DataFrame(nifty_next_week_put).to_csv("../Data/NIFTY_WEEK_1_PE.csv")
        pd.DataFrame(banknifty_next_week_call).to_csv("../Data/BANKNIFTY_WEEK_1_CE.csv")
        pd.DataFrame(banknifty_next_week_put).to_csv("../Data/BANKNIFTY_WEEK_1_PE.csv")

        #Week + 2
        pd.DataFrame(nifty_next_next_week_call).to_csv("../Data/NIFTY_WEEK_2_CE.csv")
        pd.DataFrame(nifty_next_next_week_put).to_csv("../Data/NIFTY_WEEK_2_PE.csv")
        pd.DataFrame(banknifty_next_next_week_call).to_csv("../Data/BANKNIFTY_WEEK_2_CE.csv")
        pd.DataFrame(banknifty_next_next_week_put).to_csv("../Data/BANKNIFTY_WEEK_2_PE.csv")

        #Week + 3
        pd.DataFrame(nifty_next_next_next_week_call).to_csv("../Data/NIFTY_WEEK_3_CE.csv")
        pd.DataFrame(nifty_next_next_next_week_put).to_csv("../Data/NIFTY_WEEK_3_PE.csv")
        pd.DataFrame(banknifty_next_next_next_week_call).to_csv("../Data/BANKNIFTY_WEEK_3_CE.csv")
        pd.DataFrame(banknifty_next_next_next_week_put).to_csv("../Data/BANKNIFTY_WEEK_3_PE.csv")
        print(banknifty_strike)
        print(nifty_next_next_month_call)
        indices = {
            "CURRENT_NIFTY_STRIKE": nifty_strike,
            "CURRENT_BANKNIFTY_STRIKE": banknifty_strike,
            "NIFTY_MONTH_0_CE": nifty_current_month_call.index[nifty_current_month_call['strike'] == nifty_strike].tolist()[0],
            "NIFTY_MONTH_0_PE": nifty_current_month_put.index[nifty_current_month_put['strike'] == nifty_strike].tolist()[0],
            "BANKNIFTY_MONTH_0_CE": banknifty_current_month_call.index[banknifty_current_month_call['strike'] == banknifty_strike].tolist()[0],
            "BANKNIFTY_MONTH_0_PE": banknifty_current_month_put.index[banknifty_current_month_put['strike'] == banknifty_strike].tolist()[0],

            "NIFTY_MONTH_1_CE": nifty_next_month_call.index[nifty_next_month_call['strike'] == nifty_strike].tolist()[0],
            "NIFTY_MONTH_1_PE": nifty_next_month_put.index[nifty_next_month_put['strike'] == nifty_strike].tolist()[0],
            "BANKNIFTY_MONTH_1_CE": banknifty_next_month_call.index[banknifty_next_month_call['strike'] == banknifty_strike].tolist()[0],
            "BANKNIFTY_MONTH_1_PE":banknifty_next_month_put.index[banknifty_next_month_put['strike'] == banknifty_strike].tolist()[0],
            
            #"NIFTY_MONTH_2_CE": nifty_next_next_month_call.index[nifty_next_next_month_call['strike'] == nifty_strike].tolist()[0],
            #"NIFTY_MONTH_2_PE":nifty_next_next_month_put.index[nifty_next_next_month_put['strike'] == nifty_strike].tolist()[0],
            #"BANKNIFTY_MONTH_2_CE": banknifty_next_next_month_call.index[banknifty_next_next_month_call['strike'] == banknifty_strike].tolist()[0],
            #"BANKNIFTY_MONTH_2_PE":banknifty_next_next_month_put.index[banknifty_next_next_month_put['strike'] == banknifty_strike].tolist()[0],

            
            "NIFTY_WEEK_0_CE": nifty_current_week_call.index[nifty_current_week_call['strike'] == nifty_strike].tolist()[0],
            "NIFTY_WEEK_0_PE":nifty_current_week_put.index[nifty_current_week_put['strike'] == nifty_strike].tolist()[0],
            "BANKNIFTY_WEEK_0_CE": banknifty_current_week_call.index[banknifty_current_week_call['strike'] == banknifty_strike].tolist()[0],
            "BANKNIFTY_WEEK_0_PE":banknifty_current_week_put.index[banknifty_current_week_put['strike'] == banknifty_strike].tolist()[0],

            "NIFTY_WEEK_1_CE": nifty_next_week_call.index[nifty_next_week_call['strike'] == nifty_strike].tolist()[0],
            "NIFTY_WEEK_1_PE": nifty_next_week_put.index[nifty_next_week_put['strike'] == nifty_strike].tolist()[0],
            "BANKNIFTY_WEEK_1_CE": banknifty_next_week_call.index[banknifty_next_week_call['strike'] == banknifty_strike].tolist()[0],
            "BANKNIFTY_WEEK_1_PE":banknifty_next_week_put.index[banknifty_next_week_put['strike'] == banknifty_strike].tolist()[0],

            "NIFTY_WEEK_2_CE": nifty_next_next_week_call.index[nifty_next_next_week_call['strike'] == nifty_strike].tolist()[0],
            "NIFTY_WEEK_2_PE":nifty_next_next_week_put.index[nifty_next_next_week_put['strike'] == nifty_strike].tolist()[0],
            "BANKNIFTY_WEEK_2_CE":banknifty_next_next_week_call.index[banknifty_next_next_week_call['strike'] == banknifty_strike].tolist()[0],
            "BANKNIFTY_WEEK_2_PE":banknifty_next_next_week_put.index[banknifty_next_next_week_put['strike'] == banknifty_strike].tolist()[0],

            "NIFTY_WEEK_3_CE": nifty_next_next_next_week_call.index[nifty_next_next_next_week_call['strike'] == nifty_strike].tolist()[0],
            "NIFTY_WEEK_3_PE":nifty_next_next_next_week_put.index[nifty_next_next_next_week_put['strike'] == nifty_strike].tolist()[0],
            "BANKNIFTY_WEEK_3_CE": banknifty_next_next_next_week_call.index[banknifty_next_next_next_week_call['strike'] == banknifty_strike].tolist()[0],
            "BANKNIFTY_WEEK_3_PE": banknifty_next_next_next_week_put.index[banknifty_next_next_next_week_put['strike'] == banknifty_strike].tolist()[0],
        }
        with open('../Data/Index.json','w') as f:
            json.dump(indices,f,indent=2)
        self.instrument_token_list = [*set(self.instrument_token_list)]
        with open('../Data/Misc/instrument_tokens.json','w') as f:
            for i in range(len(self.instrument_token_list)):
                self.instrument_token_list[i] = int(self.instrument_token_list[i])
        
            json.dump({'instrument_tokens':self.instrument_token_list},f,indent=2)

        
