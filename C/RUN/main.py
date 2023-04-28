""" MODULES IMPORT """
import asyncio
from datetime import timedelta, datetime
import datetime
import json
import time
import traceback
from typing import Optional

import sqlite3
import jwt

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.hash import bcrypt
from tortoise.contrib.fastapi import register_tortoise
from tortoise.exceptions import DoesNotExist
from fastapi.middleware.cors import CORSMiddleware

from Config import Config
from NomenclatureToDetails import NomeclatureToDetails
from encryption_hybrid import EncryptionHybrid
from APIhelper import ADS_Interface
from models import (
    User,
    User_Pydantic,
    UserIn_Pydantic,
)
from Log_Server_Interface import Log_Server_Interface



####### API SETUP #######
############# Start APP #############
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app = FastAPI()
config = Config()

#################### """ APP CONFIG """ ###############################
# Add additional origins here if required. Addresses must be in the format: "http://localhost:8000" -> for applications accessing the API from this address.
origins = [
    "http://localhost",
    "http://localhost:8000"
    "http://localhost:8080",
    "http://localhost:3000",
    "http://15.207.12.225:9021",
    "http://13.126.93.66:9021"

]
# Purpose: To allow cross origin requests from the above origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#################### """ APP CONFIG """ ###############################
con = sqlite3.connect('../Data/OrderData.db')
cur = con.cursor()
log = Log_Server_Interface(config=config)
log.postLog(severity='INFO', message='OMS Server turned on.', publish=1)
################### """ HELPER FUNCTIONS """ ###################


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    '''
    FastAPI helper function. Returns access token.
    
    Arguments:
    data {dict} -- User details
    expires_delta {timedelta} -- timedelta until token expiry

    Keyword Arguments:
    None

    Returns:
    encoded_jwt {str} - The access token.
    '''
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.datetime.utcnow() + expires_delta
        else:
            expire = datetime.datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm="HS256")
        return encoded_jwt
    except Exception as e:
        log.postLog(severity='ERROR', message='Error in create_access_token : ' + str(e), publish=1, tag='OMS_Main_1')


async def authenticate_user(username: str, password: str):
    '''
    FastAPI helper function. Returns user model if valid.
    
    Arguments:
    username {str} -- logged in username
    password {str} -- logged in password

    Keyword Arguments:
    None

    Returns:
    user {Tortoise model} -- The user if valid.
    False {boolean} -- Invalid login
    '''
    try:
        user = await User.get(username=username)
        if user is None:
            return False
        if not user.verify_password(password):
            return False
        return user
    except Exception as e:
        print({"config.SUBSYSTEM": config.SUBSYSTEM,"Severity": "ERROR","Message": str(e),"Publish": True,"Tags": "OMS_Main_2"})
        log.postLog(severity='ERROR', message='Error in authenticate_user : ' + str(e), publish=1, tag='OMS_Main_2')


async def get_current_user(token: str = Depends(oauth2_scheme)):
    '''
    FastAPI helper function. Checks current user login.
    
    Arguments:
    token {str} -- access token

    Keyword Arguments:
    None

    Returns:
    user {Tortoise model} -- The usermodel if valid.
    credentials_exception {HTTPException} -- Invalid login
    '''
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])
        user = await User.get(id=payload.get("id"))
        if user is None:
            raise credentials_exception

    except Exception as e:
        print({"config.SUBSYSTEM": config.SUBSYSTEM,"Severity": "ERROR","Message": str(e),"Publish": True,"Tags": "OMS_Main_3"})
        log.postLog(severity='ERROR', message='Error in get_current_user : ' + str(e), publish=1, tag='OMS_Main_3')
        raise credentials_exception
    return await User_Pydantic.from_tortoise_orm(user)
        

async def checkOrderValidity(user, strategy, instrument_nomenclature, position):
    '''
    Checks if a given order can be placed.
    
    Arguments:
    user {str} -- The username of the account on which the order goes
    strategy {str} -- The strategy placing the order
    instrument_nomenclature {str} -- The instrument nomenclature of the instrument to be traded
    position {str} -- BUY/SELL/OPEN SHORT/CLOSE SHORT

    Keyword Arguments:
    None

    Returns:
    order validity {bool} - True if order can be placed, else false.
    '''
    
    print('Checking for ' + position + ' order validity' + ' for ' + user + ' ' + strategy + ' ' + instrument_nomenclature)
    try:
        if position == 'BUY' or position == 'OPEN SHORT':
            cur.execute("SELECT * FROM orderbook WHERE username={} and strategy_name={} and instrument_nomenclature={} and position={};".format(gSF(user),gSF(strategy),gSF(instrument_nomenclature),gSF(position)))
            res = cur.fetchall()
            if len(res) == 0:
                # print('Order validity check passed')
                return True
            return False
        
        if position == 'SELL':
            cur.execute("SELECT * FROM orderbook WHERE username={} and strategy_name={} and instrument_nomenclature={} and position={};".format(gSF(user),gSF(strategy),gSF(instrument_nomenclature),gSF('BUY')))
            res = cur.fetchall()
            # print(res)
            if len(res) == 0:
                return False
            data = list(res)[0]
            if data[0] == 'PLACED':
                print('Order validity check passed')
                return True
            return False
                
        if position == 'CLOSE SHORT':
            cur.execute("SELECT * FROM orderbook WHERE username={} and strategy_name={} and instrument_nomenclature={} and position={};".format(gSF(user),gSF(strategy),gSF(instrument_nomenclature),gSF('OPEN SHORT')))
            res = cur.fetchall()
            if len(res) == 0:
                return False
            data = list(res)[0]
            if data[0] == 'PLACED':
                # print('Order validity check passed')
                return True
            return False
    except Exception as e:
        print({"config.SUBSYSTEM": config.SUBSYSTEM,"Severity": "ERROR","Message": str(e),"Publish": True,"Tags": "OMS_Main_4"})
        log.postLog(severity='ERROR', message='Error in checkOrderValidity : ' + str(e), publish=1, tag='OMS_Main_4')

def gSF(stringToConvert: str):
    '''
    Converts string to a format acceptable by sqlite3 for text type entries.
    
    Arguments:
    stringToConvert {str} -- The string to convert

    Keyword Arguments:
    None

    Returns:
    converted string {str} - The string converted to the needed format.
    '''
    if type(stringToConvert) != type("string"):
        log.postLog(severity='ERROR', message='Invalid input type! : OMS_Main', publish=1, tag='gSF_1')
        return "Invalid input type!"
    return "\'"+stringToConvert+"\'"


def check_expiry(expiry_date, instrument_nomenclature):
    """ 
    Checks if the instrument is expired or not.

    Arguments:
    expiry_date {str} -- The expiry date of the instrument
    instrument_nomenclature {str} -- The instrument nomenclature of the instrument to be traded

    Keyword Arguments:
    None

    Returns:
    expiry validity {bool} - True if instrument is not expired, else false.
    """
    expiry_date = datetime.strptime(expiry_date,'%Y-%m-%d')
    current_date = datetime.now()
    trade_holidays = pd.read_csv('../Data/trading_holidays.csv')
    ctr = 0
    while current_date < expiry_date:
        if current_date.weekday()!= 5 and current_date.weekday() != 6 and current_date.strftime('%Y-%m-%d') not in trade_holidays['Date'].tolist():
            ctr += 1
    if 'WEEK' in instrument_nomenclature:
        if ctr <= 1:
            return True
        else:
            return False
    if ctr <= 2:
        return True
    return False

def addToOrderHistory(cur,order_id, brokerage_id, user_type,  username, strategy_name, tradingsymbol, position, instrument_nomenclature, order_price, order_qty, lot_size, order_time, order_status=None):
    """ 
    Adds the order to the order history table.

    Arguments:
    cur {cursor} -- The cursor to the database
    order_id {str} -- The order id of the order
    brokerage_id {str} -- The brokerage id of the order
    user_type {str} -- The type of user placing the order
    username {str} -- The username of the account on which the order goes
    strategy_name {str} -- The strategy placing the order
    tradingsymbol {str} -- The tradingsymbol of the instrument to be traded
    position {str} -- BUY/SELL/OPEN SHORT/CLOSE SHORT
    instrument_nomenclature {str} -- The instrument nomenclature of the instrument to be traded
    order_price {float} -- The price at which the order is placed
    order_qty {int} -- The quantity of the order
    lot_size {int} -- The lot size of the instrument
    order_time {str} -- The time at which the order is placed

    Keyword Arguments:
    order_status {str} -- The status of the order (default: {None})

    Returns:
    None
    """
    cur.execute("INSERT INTO order_history (order_id, brokerage,brokerage_id,  username, strategy_name, tradingsymbol, position, instrument_nomenclature, order_status, order_price, order_qty, order_time) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(order_id,brokerage_id, user_type ,username, strategy_name, tradingsymbol, position, instrument_nomenclature, 'COMPLETE', order_price, order_qty*lot_size, order_time))


def rollOverOrder():
    '''
    Rolls over the order to the next expiry.

    Arguments:
    None

    Keyword Arguments:
    None

    Returns:
    None
    '''
    try:
        checked_instruments = {}
        cur.execute('SELECT instrument_nomenclature, tradingsymbol,instrument_token, order_id, position_stoploss_percent, position_target_percent, position_entry_price, lot_size, exchange_token, quantity, exchange, segment, order_id FROM order_reference WHERE position_status = {};'.format(gSF('PLACED')))
        orders = cur.fetchall()

        ########################################
        # Get LTP table
        # Posssible issues : LTP table not updated, LTP table not found
        while True:
            try:
                with open('../../Backend/Data/LTP_table.json') as f:
                    ltp_table = json.load(f)
                break
            except:
                print('Waiting for LTP table to be updated')
                time.sleep(0.5)
                continue
        ########################################
            
        for o in orders:

            """ 
            Working of the following code:
            1st, go to order reference, and find positions to be rolled over.
            This will be done by checking if current tradingsymbol is not the same as held tradingsymbol
            Save new instrument nom to lookup table

            Get the LTP of new and old instrument
            Set placed price = old placed price - diff in LTPs of new and old LTP
            Adjust target and stoploss accordingly

            Add old position close to orderbuffer
            Add new position open to orderbuffer
            Update orderbook
              
            """
            print(list(o))
            instrument_nomenclature = list(o)[0]
            held_tradingsymbol = list(o)[1]
            held_instrument_token = str(list(o)[2])
            order_id = list(o)[3]
            position_stoploss_perc = list(o)[4]
            position_target_perc = list(o)[5]
            position_entry_price = list(o)[6]
            lot_size = list(o)[7]
            held_exchange_token = list(o)[8]
            quantity = list(o)[9]
            exchange = list(o)[10]
            segment = list(o)[11]
            order_id = list(o)[12]
            cur.execute('SELECT instrument_nomenclature FROM orderbook WHERE order_id = {};'.format(order_id))
            instrument_nomenclature_ob = cur.fetchall()[0][0]
            cur.execute('SELECT username, net_stoploss_perc, net_target_perc, strategy_name, position, strategy_name from orderbook where order_id = {};'.format(order_id))
            position = cur.fetchall()
            username = list(position)[0][0]
            strategy_name = list(position)[0][3]
            strategy_name = list(position)[0][5]

            cur.execute('SELECT position_type from ORDER_REFERENCE WHERE order_id = {} and tradingsymbol = {};'.format(order_id, gSF(held_tradingsymbol)))
            position_type_or = cur.fetchall()[0][0]
            # print(held_tradingsymbol)

            if instrument_nomenclature not in checked_instruments:
                n = NomeclatureToDetails(config.ADS_SERVER_ADDRESS)
                instrument_data = n.process_order_nomenclature(instrument_nomenclature)[instrument_nomenclature]['INSTRUMENTS'][0]
                print(' NTDS : ',instrument_data)
                checked_instruments[instrument_nomenclature] = instrument_data

            instrument_data = checked_instruments[instrument_nomenclature]
            latest_tradingsymbol = instrument_data['TRADINGSYMBOL']
            print(latest_tradingsymbol)
            latest_instrument_token = str(instrument_data['INSTRUMENT_TOKEN'])
            latest_expiry = instrument_data['EXPIRY']
            latest_exchange_token = instrument_data['EXCHANGE_TOKEN']
            if held_tradingsymbol != latest_tradingsymbol:
                #Rollover existing position
                ltp_old = ltp_table[held_instrument_token]
                ltp_new = ltp_table[latest_instrument_token]
                diff = ltp_new - ltp_old

                new_position_stoploss = (position_entry_price + diff)*(position_stoploss_perc/100)
                new_position_target = (position_entry_price + diff)*(position_target_perc/100)
                cur.execute("UPDATE order_reference SET expiry_date = {}, exchange_token = {}, tradingsymbol = {}, instrument_token = {}, position_stoploss = {}, position_target = {}, position_entry_price = {} WHERE instrument_nomenclature = {} AND order_id = {};".format(gSF(latest_expiry),latest_exchange_token,gSF(latest_tradingsymbol),gSF(latest_instrument_token),new_position_stoploss,new_position_target,position_entry_price+diff, gSF(instrument_nomenclature), order_id))
                

                ######################################## TO BE UPDATED
                # lookup_table = open('../Data/lookup_table.json')
                # lookup_table = json.load(lookup_table)
                # # Update lookup table
                # if str(instrument_token) in lookup_table:
                #     lookup_table[str(instrument_token)]['ctr'] = lookup_table[str(instrument_token)]['ctr'] + 1
                # else:
                #     lookup_table[instrument_token] = {
                #         "ctr": 1
                #     }
                ########################################
                
                
                # Print order details
                log.postLog('INFO', "Rollover order placed for {} with order id {}".format(held_tradingsymbol, order_id), publish=False, tag='Rollover')

                # Add old position close to orderbuffer -> to CLOSE the position
                addOrderToOrderBuffer(username=username, tradingsymbol=held_tradingsymbol, lot_size=lot_size, exchange_token=held_exchange_token, quantity=(quantity*-1),strategy_name=strategy_name, instrument_nomenclature=instrument_nomenclature_ob,position=position_type_or, exchange=exchange,segment=segment,instrument_token=held_instrument_token,rollover='Y')
                # Add new position open to orderbuffer -> to OPEN the position
                addOrderToOrderBuffer(username=username, tradingsymbol=latest_tradingsymbol, lot_size=lot_size, exchange_token=latest_exchange_token, quantity=quantity,strategy_name=strategy_name, instrument_nomenclature=instrument_nomenclature_ob,position=position_type_or, exchange=exchange,segment=segment,instrument_token=latest_instrument_token,rollover='Y')
                
        # Release the db lock
        con.commit()

        # log the order
        log.postLog(username, 'Order rollover successful', 'INFO')
        return {'status': 'success'}
    except Exception as e:
        print(e)
        traceback.print_exc()
        return {'status': 'error - {}'.format(e)}
    
     

def placeOrder(username,strategy_name,instrument_nomenclature,position,quantity,net_stoploss_perc,net_target_perc, nomenclature_to_details):
    '''This method places inputted order by
    1. Adding it to the orderbook
    2. Adding it to the order reference table
    3. Adding it to the order buffer table
    4. Adding it to the position reference table
    
    Arguments:
    username {str} -- The username of the account on which the order goes
    strategy_name {str} -- The strategy placing the order
    instrument_nomenclature {str} -- The instrument nomenclature of the instrument to be traded
    position {str} -- BUY/SELL/OPEN SHORT/CLOSE SHORT
    quantity {int} -- The number of lots to be placed
    net_stoploss_perc {real} -- The stoploss of the overall position as a percentage
    net_target_perc {real} -- The target of the overall position as a percentage

    Keyword Arguments:
    None

    Returns:
    Order status 

    
    '''
    # print('Placing order')

    if position == 'BUY' or position == 'OPEN SHORT':
        order_id = str(hash(datetime.datetime.now())) 
        print('Order ID: ',order_id) 
        if position == 'BUY':
            try:
                cur.execute('INSERT INTO orderbook VALUES ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {},{}, {}, {})'.format(gSF('Placing'),gSF(username),gSF(strategy_name),gSF(instrument_nomenclature),gSF(position),quantity,0,net_stoploss_perc,net_target_perc,0,0,0,gSF(order_id), gSF('N')))
            except sqlite3.Error as e:
                print(e)
                print('DATABASE ERROR: Order already exists in orderbook table')
                return False
        if position == 'OPEN SHORT':
            try:
                quantity = quantity*-1
                cur.execute('INSERT INTO orderbook VALUES ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {},{}, {}, {})'.format(gSF('Placing'),gSF(username),gSF(strategy_name),gSF(instrument_nomenclature),gSF(position),(quantity),0,net_stoploss_perc,net_target_perc,0,0,0,gSF(order_id), gSF('N')))
            except sqlite3.Error as e:
                print(e)
                print('DATABASE ERROR: Order already exists in orderbook table')
                return False
        #^ Add order to orderbook table
    elif position == 'SELL':
        try:
            cur.execute("SELECT * FROM orderbook WHERE username = {} and strategy_name = {} and instrument_nomenclature = {} and position = {}".format(gSF(username),gSF(strategy_name),gSF(instrument_nomenclature),gSF("BUY")))
            d = list(cur.fetchall())[0]
            order_id = d[12]
            cur.execute('UPDATE orderbook SET order_status={} where username={} and strategy_name={} and instrument_nomenclature={} and position={}'.format(gSF('CLOSING'),gSF(username),gSF(strategy_name),gSF(instrument_nomenclature),gSF('BUY')))
        except sqlite3.Error as e:
            print(e)
            print('DATABASE ERROR: Order already exists in orderbook table')
            return False
    elif position == 'CLOSE SHORT':
        try:
            print("HIT")
            cur.execute("SELECT * FROM orderbook WHERE username = {} and strategy_name = {} and instrument_nomenclature = {} and position = {}".format(gSF(username),gSF(strategy_name),gSF(instrument_nomenclature),gSF("OPEN SHORT")))
            d = list(cur.fetchall())[0]
            order_id = d[12]
            cur.execute('UPDATE orderbook SET order_status={} where username={} and strategy_name={} and instrument_nomenclature={} and position={}'.format(gSF('CLOSING'),gSF(username),gSF(strategy_name),gSF(instrument_nomenclature),gSF('OPEN SHORT')))
        except sqlite3.Error as e:
            print(e)
            print('DATABASE ERROR: Order already exists in orderbook table')
            return False
    ret = addOrderToOrderReference(order_id = order_id, username=username, instrument_nomenclature = instrument_nomenclature, quantity = quantity, position = position, strategy=strategy_name, nomenclature_to_details=nomenclature_to_details)

    if ret:
        log.postLog('post/log', "Order placed for {} {} {} {} {} {} {}".format(username,strategy_name,instrument_nomenclature,position,quantity,net_stoploss_perc,net_target_perc), publish=False)
    print("Order placed")
    return ret

def refresh_lookup_table(instrument_token, position):
    """
    This function refreshes the lookup table

    Arguments:
    instrument_token {int} -- The instrument token of the instrument to be refreshed
    position {str} -- The position to be refreshed

    Keyword Arguments:
    None

    Returns:
    None
    """
    lookup_table = open('../Data/lookup_table.json')
    lookup_table = json.load(lookup_table)
    # Check if instrument token exists in lookup table
    if position == 'BUY' or position == 'OPEN SHORT':
        if str(instrument_token) in lookup_table:
            lookup_table[str(instrument_token)]['ctr'] = lookup_table[str(instrument_token)]['ctr'] + 1
        else:
            lookup_table[instrument_token] = {
                "ctr": 1
            }
    elif position == 'SELL' or position == 'CLOSE SHORT':
        if str(instrument_token) in lookup_table:
            lookup_table[str(instrument_token)]['ctr'] = lookup_table[str(instrument_token)]['ctr'] - 1
        else:
            lookup_table[instrument_token] = {
                "ctr": -1
            }
    while True:
        # Save lookup table
        with open('../Data/lookup_table.json', 'w') as f:
            json.dump(lookup_table, f, indent=4)
            break


    

def addOrderToOrderReference(order_id,username,instrument_nomenclature,quantity, position, strategy, nomenclature_to_details):
    """ 
    This function adds the order to the order reference table.

    Arguments:
    order_id {str} -- The order id of the order
    username {str} -- The username of the user placing the order
    instrument_nomenclature {str} -- The instrument nomenclature of the instrument to be traded
    quantity {int} -- The number of units to be placed
    position {str} -- The position to be taken
    strategy {str} -- The strategy name

    Keyword Arguments:
    None

    Returns:
    Order status (True/False : returned by addOrderToOrderReference function)
    """
    # print('ORDER REFERENCE CALLED')
    
    
    if position == 'BUY' or position == 'OPEN SHORT':
        instrument_data = nomenclature_to_details.process_order_nomenclature(instrument_nomenclature)[instrument_nomenclature]   #Get details on the instrument to be placed based on instrument nomenclature
        spread = instrument_data['SPREAD']  #Check if spread, spreads have minor changes in saving to order reference
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') #Get current time, which will be saved as order placement time
        
        for instrument in instrument_data['INSTRUMENTS']:
            tradingsymbol = instrument['TRADINGSYMBOL']
            exchange_token = instrument['EXCHANGE_TOKEN']
            instrument_token = instrument['INSTRUMENT_TOKEN']

            exchange = instrument['EXCHANGE']
            segment = instrument['SEGMENT']
            nomenclature = instrument['NOMENCLATURE']

            refresh_lookup_table(instrument_token, position)

            expiry = instrument['EXPIRY']
            lot_size = instrument['LOT_SIZE']

            if spread:
                index_peg = instrument_data['INDEX_PEG']
                position_spread = instrument['POSITION']
                position_target_percent = instrument['TARGET']
                position_stoploss_percent = instrument['STOPLOSS']
                if index_peg != 'N':
                    cur.execute('UPDATE orderbook SET index_peg = {} WHERE order_id = {};'.format(gSF(index_peg),order_id))
                if position_spread == 'BUY':
                    cur.execute('INSERT INTO order_reference VALUES ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {},{} ,{}, {})'.format(gSF(order_id),gSF("IN PROGRESS"),gSF(current_time),quantity,gSF(expiry),gSF(exchange),gSF(segment),exchange_token,gSF(tradingsymbol),instrument_token,lot_size,position_stoploss_percent,position_target_percent,0,0,0,0,gSF(position_spread),gSF(nomenclature)))
                    ret = addOrderToOrderBuffer(username = username, tradingsymbol=tradingsymbol,lot_size=lot_size,exchange_token=exchange_token,quantity=quantity, strategy_name=strategy, instrument_nomenclature=instrument_nomenclature, position = position_spread, exchange=exchange, segment=segment, instrument_token=instrument_token)
                elif position_spread == 'OPEN SHORT':
                    cur.execute('INSERT INTO order_reference VALUES ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})'.format(gSF(order_id), gSF("IN PROGRESS"),gSF(current_time),quantity*-1,gSF(expiry),gSF(exchange),gSF(segment),exchange_token,gSF(tradingsymbol),instrument_token,lot_size,position_stoploss_percent,position_target_percent,0,0,0,0,gSF(position_spread),gSF(nomenclature)))
                    ret = addOrderToOrderBuffer(username = username, tradingsymbol=tradingsymbol,lot_size=lot_size,exchange_token=exchange_token,quantity=quantity*-1, strategy_name=strategy, instrument_nomenclature=instrument_nomenclature, position = position_spread, exchange=exchange, segment=segment, instrument_token=instrument_token)
                
            else:
                if position == 'BUY':
                    cur.execute('INSERT INTO order_reference VALUES ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})'.format(gSF(order_id), gSF("IN PROGRESS"),gSF(current_time),quantity,gSF(expiry),gSF(exchange),gSF(segment),exchange_token,gSF(tradingsymbol),instrument_token,lot_size,0,0,0,0,0,0,gSF(position),gSF(nomenclature)))
                if position == 'OPEN SHORT':
                    print('INSERT INTO order_reference VALUES ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})'.format(gSF(order_id), gSF("IN PROGRESS"),gSF(current_time),quantity,gSF(expiry),gSF(exchange),gSF(segment),exchange_token,gSF(tradingsymbol),instrument_token,lot_size,0,0,0,0,0,0,gSF(position),gSF(nomenclature)))
                    print('INSERT INTO order_reference VALUES ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})'.format(gSF(order_id), gSF("IN PROGRESS"),gSF(current_time),quantity*-1,gSF(expiry),gSF(exchange),gSF(segment),exchange_token,gSF(tradingsymbol),instrument_token,lot_size,0,0,0,0,0,0,gSF(position),gSF(nomenclature)))
                    cur.execute('INSERT INTO order_reference VALUES ({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})'.format(gSF(order_id), gSF("IN PROGRESS"),gSF(current_time),quantity,gSF(expiry),gSF(exchange),gSF(segment),exchange_token,gSF(tradingsymbol),instrument_token,lot_size,0,0,0,0,0,0,gSF(position),gSF(nomenclature)))

                ret = addOrderToOrderBuffer(username = username, tradingsymbol=tradingsymbol,lot_size=lot_size,exchange_token=exchange_token,quantity=quantity, strategy_name=strategy, instrument_nomenclature=instrument_nomenclature, position = position, exchange=exchange, segment=segment, instrument_token=instrument_token)

    
    
    elif position == "SELL" or position == 'CLOSE SHORT':
        
        try:
            #Fetch list of instruments associated with that order
            cur.execute("SELECT * FROM order_reference WHERE order_id = {};".format(order_id))
            instrument_data = nomenclature_to_details.process_order_nomenclature(instrument_nomenclature)[instrument_nomenclature]   #Get details on the instrument to be placed based on instrument nomenclature
            spread = instrument_data['SPREAD']
            bought_instruments = list(cur.fetchall())
            cur.execute("UPDATE order_reference SET position_status={} WHERE order_id={};".format(gSF('CLOSING'),order_id))
        except sqlite3.Error as e:
            print("Error while fetching data from sqlite", e)
            return False

        
        #Iterate through instrument list
        for instrument in bought_instruments:
            instrument_data_list = list(instrument)
            exchange_token = instrument_data_list[7]
            tradingsymbol = instrument_data_list[8]
            exchange = instrument_data_list[5]
            segment = instrument_data_list[6]
            instrument_token = instrument_data_list[9]

            refresh_lookup_table(instrument_token, position)

            lot_size = instrument_data_list[10]
            spread_position = instrument_data_list[17]
            if spread:
                if spread_position == 'BUY':
                    ret = addOrderToOrderBuffer(username = username, tradingsymbol=tradingsymbol,lot_size=lot_size,exchange_token=exchange_token,quantity=(quantity*(-1)), strategy_name=strategy, instrument_nomenclature=instrument_nomenclature, position = 'SELL', exchange=exchange, segment=segment, instrument_token=instrument_token)
                if spread_position == 'OPEN SHORT':
                    ret = addOrderToOrderBuffer(username = username, tradingsymbol=tradingsymbol,lot_size=lot_size,exchange_token=exchange_token,quantity=quantity, strategy_name=strategy, instrument_nomenclature=instrument_nomenclature, position = 'CLOSE SHORT', exchange=exchange, segment=segment, instrument_token=instrument_token)
            else:
                if position == 'SELL':
                    #Add the position to orderbuffer for each instrument, if sell, qty*-1
                    ret = addOrderToOrderBuffer(username = username, tradingsymbol=tradingsymbol,lot_size=lot_size,exchange_token=exchange_token,quantity=(quantity*(-1)), strategy_name=strategy, instrument_nomenclature=instrument_nomenclature, position = position, exchange=exchange, segment=segment, instrument_token=instrument_token)
                if position == 'CLOSE SHORT':
                    ret = addOrderToOrderBuffer(username = username, tradingsymbol=tradingsymbol,lot_size=lot_size,exchange_token=exchange_token,quantity=(quantity*(-1)), strategy_name=strategy, instrument_nomenclature=instrument_nomenclature, position = position, exchange=exchange, segment=segment, instrument_token=instrument_token)

    return ret


def addOrderToOrderBuffer(username, tradingsymbol, lot_size, exchange_token, quantity, strategy_name, instrument_nomenclature, position,exchange,segment, instrument_token, rollover = 'N'):
    """ 
    This function adds the order to the orderbuffer table in the database and returns True if successful.

    Parameters:
    username (str): Username of the user
    tradingsymbol (str): Tradingsymbol of the instrument
    lot_size (int): Lot size of the instrument
    exchange_token (int): Exchange token of the instrument
    quantity (int): Quantity of the instrument
    strategy_name (str): Strategy name of the order
    instrument_nomenclature (str): Instrument nomenclature of the order
    position (str): Position of the order to be taken

    Returns:
    bool: True if successful, False otherwise

    Keywork Arguments:
    None
    """
    print("Adding to orderbuffer")

    try:
        cur.execute('SELECT * FROM orderbuffer WHERE username = {} and tradingsymbol = {}'.format(gSF(username),gSF((tradingsymbol))))
        res = cur.fetchall()
    except sqlite3.Error as e:
        print("Error while fetching data from orderbuffer: ", e)
        return False
    
    if len(res) == 0:
        #New position in orderbuffer
        position_id = str(hash(datetime.datetime.now()))
        try:
            cur.execute('INSERT INTO orderbuffer values ({}, {}, {}, {}, {}, {}, {}, {},{}, {}, {},{}, {})'.format(gSF(username),gSF(tradingsymbol),gSF(str(instrument_token)),lot_size, gSF(exchange),gSF(segment),exchange_token,quantity,0,0,0,position_id, gSF(rollover)))
        except sqlite3.Error as e:
            print("Error while adding to orderbuffer: ", e)
            return False  
    else:
        #Position already exists
        position_id = list(res[0])[10]
        try:
            cur.execute('UPDATE orderbuffer SET total_qty = total_qty + {} WHERE username = {} and tradingsymbol = {};'.format(quantity, gSF(username),gSF(tradingsymbol)))
        except sqlite3.Error as e:
            print("Error while updating orderbuffer: ", e)
            return False
        
    return addOrderToPositionReference(position_id=position_id, strategy_name = strategy_name, instrument_nomenclature = instrument_nomenclature, position_type = position, username = username, rollover = rollover)

def addOrderToPositionReference(position_id, strategy_name, instrument_nomenclature, position_type, username, rollover):
    """ 
    This function adds the order to the position reference table in the database and returns True if successful.

    Parameters:
    position_id (str): Position ID of the order
    strategy_name (str): Strategy name of the order
    instrument_nomenclature (str): Instrument nomenclature of the order
    position_type (str): Position of the order to be taken
    username (str): Username of the user

    Returns:
    bool: True if successful, False otherwise

    Keywork Arguments:
    None
    """
    try:
        cur.execute('INSERT INTO position_reference values ({}, {}, {}, {}, {})'.format(position_id,gSF(strategy_name),gSF(instrument_nomenclature),gSF(position_type),gSF(username)))
        return True
    except sqlite3.Error as e:
        print("Error while adding to position reference : {}".format(e))
        return False

async def getUserDetails(strategy, instrument, position):
    """ 
    Fetch username from strategy name from ADS server API.

    Parameters:
    strategy (str): Strategy name

    Returns:
    dict: Dictionary of user details

    Keywork Arguments:
    None
    """
    #Fetch user data from ADS(A)
    with open('../Data/user_data.json', 'r') as f:
        ud = json.load(f)
    if ud['LAST_UPDATED'] + 7200 < time.time():
        #Fetch user data from ADS server
        ads = ADS_Interface(config.ADS_SERVER_ADDRESS)
        user_data = ads.get('get/user_data')
        user_data = json.loads(user_data)
        ud['LAST_UPDATED'] = time.time()
        ud['USER_DATA'] = user_data
        with open('../Data/user_data.json', 'w') as f:
            json.dump(ud, f, indent=4)
    else:
        user_data = ud['USER_DATA']

    #Fetch user names from user data (are keys in dict) and have same strategy name
    user_names = list(user_data.keys())

    user_details = {}
    
    for user in user_names:
        # Print list of strategies for each user
        print('Checking user {} for strategy {}'.format(user, strategy))
        
        if strategy in list(user_data[user]['STRATEGY_DETAILS'].keys()):
            if position == 'BUY' or position == 'OPEN SHORT':
                # d = 0 for BUY and d = 1 for OPEN SHORT | d is short/long position in strategy details
                if position == 'BUY':
                    d = 0
                elif position == 'OPEN SHORT':
                    d = 1
                if user_data[user]['STRATEGY_DETAILS'][strategy][instrument][d] > 0:
                    user_details[user] = user_data[user]['STRATEGY_DETAILS'][strategy]
            elif position == 'SELL' or position == 'CLOSE SHORT':
                user_details[user] = user_data[user]['STRATEGY_DETAILS'][strategy]
    print('Number of users with strategy {}: {}'.format(strategy, len(user_details)))
    return user_details

def getOrderBook():
    """ 
    Fetch order book from ../Data/OrderData.db database.

    Parameters:
    None

    Returns:
    dict: Dictionary of order book

    Keywork Arguments:
    None
    """

    try:
        cur.execute('SELECT * FROM orderbook')
        res = cur.fetchall()

        #############################
        # Sample orderbook response #
        # res = [
        #     ('OPEN', 'user1', 'strategy1', 'NIFTY', 'BUY', 100, 10000, 0.5, 1, 2, 1000000, 'order1', 0, 'N'),
        #     ('OPEN', 'user1', 'strategy1', 'NIFTY', 'SELL', 100, 10000, 0.5, 1, 2, 1000000, 'order2', 0, 'NIFTY'),
        # ]
        #############################

        print("Order book: ", res)
        order_book = []
        for order in res:
            order_book.append({
                'status': order[0],
                'username': order[1],
                'strategy_name': order[2],
                'instrument_nomenclature': order[3],
                'position_type': order[4],
                'quantity': order[5],
                'net_entry_price': order[6],
                'net_stoploss_perc': order[7],
                'net_target_perc': order[8],
                'net_stoploss_value': order[9],
                'net_target_value': order[10],
                'net_position_value': order[11],
                'order_id': order[12],
                'index_peg': order[13]
            })
        return order_book
        
    except sqlite3.Error as e:
        print("Error while fetching data from orderbook: ", e)
        return False
    



################# """ ROUTES """ ##################


@app.get("/")
async def index():
    '''
    Default route.
    
    Arguments:
    None {None} -- None.

    Keyword Arguments:
    None

    Returns:
    dict {Dict} -- A default message.
    '''
    return {"message": "FINVANT RESEARCH CAPITAL API"}


## Route to generate access token
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    '''
    Login route.
    
    Arguments:
    form_data {OAuth2PasswordRequestForm} -- None.

    Keyword Arguments:
    None

    Returns:
    dict {Dict} -- The access token and token type if valid.
    HTTPException {HTTPException} -- In case of invalid login
    '''
    try:
        user = await authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )
        user_obj = await User_Pydantic.from_tortoise_orm(user)
        ## Add expiration time to token
        access_token_expires = timedelta(minutes=Config().EXPIRY_MINUTES)
        data = {
            "id": user_obj.id,
            "username": user_obj.username,
            "password": user_obj.password_hash,
        }
        access_token = create_access_token(data, expires_delta=access_token_expires)
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        log.postLog(severity='INFO', message='Error in login route: {}'.format(e), tag='OMS_Main_6')

## Routes for API USERS
## Route to create a new user
@app.post("/users/create", response_model=User_Pydantic)

async def create_user(userIn: UserIn_Pydantic):
    '''
    Create new user route.
    
    Arguments:
    userIn {PyDantic model} -- None.

    Keyword Arguments:
    None

    Returns:
    user object {PyDantic Model} -- The user model of the newly created user. 
    '''
    try:
        user_obj = User(
            username=userIn.username,
            password_hash=bcrypt.hash(userIn.password_hash),
        )
        await user_obj.save()
        return await User_Pydantic.from_tortoise_orm(user_obj)
    except Exception as e:
        log.postLog(severity='INFO', message='Error in create user route: {}'.format(e), tag='OMS_Main_7')


## Route to get a user by id
@app.get("/users/{user_id}", response_model=User_Pydantic)
async def get_user(user_id: int, user: User_Pydantic = Depends(get_current_user)):
    '''
    Get user by user_id route.
    
    Arguments:
    user_id {int} -- The user id.

    Keyword Arguments:
    None

    Returns:
    user object {PyDantic Model} -- The user model of the newly created user. 
    '''

    try:
        user_obj = await User.get(id=user_id)
        return await User_Pydantic.from_tortoise_orm(user_obj)
    except DoesNotExist:
        log.postLog(severity='INFO', message='Error in get user by id route: {}'.format(e), tag='OMS_Main_8')
        raise HTTPException(status_code=404, detail="User not found")
        


## Route to get current logged-in user
@app.get("/users/current/", response_model=User_Pydantic)
async def get_user(user: User_Pydantic = Depends(get_current_user)):
    '''
    Get current logged in user.
    
    Arguments:
    user {Pydantic model} -- The user model.

    Keyword Arguments:
    None

    Returns:
    user object {PyDantic Model} -- The user model of the newly created user. 
    '''
    return user
#########################################################

## ROUTES FOR API USERS end ## 
################
################
## GET ROUTES ##


## POST ROUTES ##
@app.post("/orders/rollover")
async def rollover_order(data: dict, user: User_Pydantic = Depends(get_current_user)):
    '''
    Rollover an existing order

    Arguments:
    data {dict} -- The order data. It should be in the following format:
    {
        "ORDERS":[
            {
                "STRATEGY": "<string>",
                "USERNAME": <string>
                "ORDER_ID": "<int>"
            }
        ]
    }
    And the order should be encrypted using the public key of the user, in following format:
    {
        "encrypted_key": "hex format of encrypted key",
        "encrypted_data": "hex format of encrypted data"
    }

    Keyword Arguments:
    None

    Returns:
    order success message {dict} -- The success message of the order.
    '''
    try:
        # Decypting the orderIn
        # Get encrypted key and encrypted data from request
        encrypted_key = data["encrypted_key"]
        encrypted_data = data["encrypted_data"]

        # Convert encrypted key and encrypted data from hex format to bytes
        encrypted_key = bytes.fromhex(encrypted_key)
        encrypted_data = bytes.fromhex(encrypted_data)

        # Decrypt encrypted key and encrypted data
        encryption = EncryptionHybrid()
        decrypted_message = encryption.decrypt(encrypted_key, encrypted_data)
        decrypted_message = decrypted_message.replace("\'", '\"') 
        decrypted_message = json.loads(decrypted_message)
        print('RUNNING ROLLOVER ORDER')
        return rollOverOrder()
    except Exception as e:
        log.postLog(severity='INFO', message='Error in rollover order route: {}'.format(e), tag='OMS_Main_10')
        return {"message": "Error in rollover order route: {}".format(e)}
    


## Route to return orderbook from OrderData.db
@app.get("/orders/orderbook")
async def get_orderbook(user: User_Pydantic = Depends(get_current_user)):
    '''
    Get orderbook route.

    Arguments:
    None

    Keyword Arguments:
    None

    Returns:
    orderbook {dict} -- The orderbook.
    '''
    try:
        orderbook = getOrderBook()
        return orderbook
    except Exception as e:
        log.postLog(severity='INFO', message='Error in get orderbook route: {}'.format(e), tag='OMS_Main_9')

## Route to post orders (check validity of order) and add to database
@app.post("/orders/create")
async def create_order(data: dict, user: User_Pydantic = Depends(get_current_user)):
    '''
    Create new order route.

    Arguments:
    data {dict} -- The order data. It should be in the following format:
    {
        "ORDERS":[
            {
                "STRATEGY": "<string>",
                "INSTRUMENT_NOMENCLATURE": "<string>",
                "POSITION":"<string>",
                "TARGET":<int>,
                "STOPLOSS":<int>
            }
        ]
    }
    And the order should be encrypted using the public key of the user, in following format:
    {
        "encrypted_key": "hex format of encrypted key",
        "encrypted_data": "hex format of encrypted data"
    }

    Keyword Arguments:
    None

    Returns:
    order success message {dict} -- The success message of the order.
    '''


    # Decypting the orderIn
    # Get encrypted key and encrypted data from request
    encrypted_key = data["encrypted_key"]
    encrypted_data = data["encrypted_data"]

    # Convert encrypted key and encrypted data from hex format to bytes
    encrypted_key = bytes.fromhex(encrypted_key)
    encrypted_data = bytes.fromhex(encrypted_data)

    # Decrypt encrypted key and encrypted data
    encryption = EncryptionHybrid()
    decrypted_message = encryption.decrypt(encrypted_key, encrypted_data)
    decrypted_message = decrypted_message.replace("\'", '\"') 
    decrypted_message = json.loads(decrypted_message)


    valid_users = []
    for order in decrypted_message["ORDERS"]:

        strategy = order["STRATEGY"]
        instrument_nomenclature = order["INSTRUMENT_NOMENCLATURE"]
        position = order["POSITION"]
        target = order["TARGET"]
        stoploss = order["STOPLOSS"]

        # Get list of all user_names with same strategy (from ADS(A) server)
        user_details = await asyncio.create_task(getUserDetails(strategy, instrument_nomenclature, position)) # async allows to run multiple tasks at the same time
        
        # Check order validity (if order is valid, add to database)
        if user_details:
            user_result = {}
            # Create list of valid users for the order
            for user_name in user_details:
                print('Executing for : {}'.format(user_name))

                # Check if order is valid
                is_valid = await asyncio.create_task(checkOrderValidity(user_name, strategy, instrument_nomenclature, position))
                if is_valid:
                    temp_details = {}
                    temp_details["user_name"] = user_name
                    temp_details["strategy"] = strategy
                    temp_details["instrument_nomenclature"] = instrument_nomenclature
                    temp_details["position"] = position
                    temp_details["target"] = target
                    temp_details["stoploss"] = stoploss

                    # Get quantity from user_details (from ADS(A) server)
                    if position == "BUY":
                        temp_details["quantity"] = user_details[user_name][instrument_nomenclature][0]
                    elif position == "OPEN SHORT":
                        temp_details["quantity"] = user_details[user_name][instrument_nomenclature][1]
                    valid_users.append(temp_details)
        else:
            # If no users found for the order, return error message
            return {"message": "No users found for the order with strategy: {}, instrument_nomenclature: {}, position: {}".format(strategy, instrument_nomenclature, position)}


    nomenclature_to_details = NomeclatureToDetails(config.ADS_SERVER_ADDRESS) # object to get details of instrument nomenclature
    # Create order for each valid user
    for user in valid_users:
        print('Placing order for : {}'.format(user['user_name']))
        user_name = user["user_name"]
        strategy = user["strategy"]
        instrument_nomenclature = user["instrument_nomenclature"]
        position = user["position"]
        target = user["target"]
        stoploss = user["stoploss"]
        

        # Place order in database
        if position == "BUY" or position == "OPEN SHORT":
            quantity = user["quantity"]
            try:
                if placeOrder(user_name, strategy, instrument_nomenclature, position, quantity, stoploss, target, nomenclature_to_details):
                    user_result[user_name] = "Order placement successful"

            except sqlite3.Error as e:
                log.postLog(severity="INFO", message="Error placing order: " + str(e), tag="OMS_Main_9")
        if position == "SELL" or position == "CLOSE SHORT":
            # quantity = 1 # it will come from the table -> reference order ref table
            if position == "SELL":
                query = "SELECT quantity, position FROM orderbook WHERE username = '" + user_name + "' AND strategy_name = '" + strategy + "' AND instrument_nomenclature = '" + instrument_nomenclature + "' AND position = 'BUY'"
            elif position == "CLOSE SHORT":
                query = "SELECT quantity, position FROM orderbook WHERE username = '" + user_name + "' AND strategy_name = '" + strategy + "' AND instrument_nomenclature = '" + instrument_nomenclature + "' AND position = 'OPEN SHORT'"
            row = list(cur.execute(query).fetchall()[0])
            quantity = int(row[0])
            position = row[1]

            # If position is BUY/OPEN SHORT, change it to SELL/CLOSE SHORT to close the position
            if position == "BUY":
                position = "SELL"
            elif position == "OPEN SHORT":
                position = "CLOSE SHORT"
            
            try:
                if placeOrder(user_name, strategy, instrument_nomenclature, position, quantity, stoploss, target, nomenclature_to_details):
                    user_result[user_name] = "Order placement successful" 
            except sqlite3.Error as e:
                print("Error placing order: " + str(e))
        
        if user_name not in user_result:
            user_result[user_name] = "Order placement unsuccessful."
    

    con.commit() # commit changes to database here to allow bulk order placement
    log.postLog(severity="INFO", message="Order placement successful for users: " + str(valid_users), tag="OMS_Main_9", publish=True)
    return user_result

## EDIT ROUTES ##

################## """ DATABASE SETUP """ ##################
register_tortoise(
    app,
    db_url="sqlite://../Data/db.sqlite3",
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)
