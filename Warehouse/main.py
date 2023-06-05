""" MODULES IMPORT """
import base64
import csv
from datetime import timedelta, datetime
import datetime
import json
import sqlite3
import traceback
from typing import Optional
import pandas as pd

import os
import jwt

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from passlib.hash import bcrypt
from tortoise.contrib.fastapi import register_tortoise
from tortoise.exceptions import DoesNotExist


import traceback
from selenium import webdriver
import time
from datetime import datetime, timedelta
import pandas as pd
from kiteconnect import KiteConnect, KiteTicker
#import Logs as logs
import pyotp
from encryption_hybrid import EncryptionHybrid

# Import jsonable_encoder to convert the pydantic object to a json serializable object
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse



from models import (
    User,
    User_Pydantic,
    UserIn_Pydantic,
)

EDITOR = os.environ.get("EDITRO", "vim")
SECTION = 'Warehouse'


####### API SETUP #######

############# Start APP #############
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app = FastAPI()


#################### """ APP CONFIG """ ###############################
SECRET_KEY = (
    "3092325@$@(234#24@$(8finvantResearchCapitalSecretKeyApi208u39324935@$#(*3@#(989898"
)
EXPIRY_MINUTES = 30
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
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
        return encoded_jwt
    except Exception as e:
        print({"Section": SECTION,"Severity": "ERROR","Message": str(e),"Publish": True,"Tags": "ADS_Main_1"})


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
        print({"Section": SECTION,"Severity": "ERROR","Message": str(e),"Publish": True,"Tags": "ADS_Main_2"})


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
    try:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user = await User.get(id=payload.get("id"))
            if user is None:
                raise credentials_exception

        except:
            raise credentials_exception
        return await User_Pydantic.from_tortoise_orm(user)
    except Exception as e:
        print({"Section": "SECTION","Severity": "ERROR","Message": str(e),"Publish": True,"Tags": "ADS_Main_3"})




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
        access_token_expires = timedelta(minutes=EXPIRY_MINUTES)
        # access_token = jwt.encode(user_obj.dict(), secret_key)
        data = {
            "id": user_obj.id,
            "username": user_obj.username,
            "password": user_obj.password_hash,
        }
        access_token = create_access_token(data, expires_delta=access_token_expires)
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        print({"Section": "SECTION","Severity": "ERROR","Message": str(e),"Publish": True,"Tags": "ADS_Main_4"})

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
        print({"Section": SECTION,"Severity": "ERROR","Message": str(e),"Publish": True,"Tags": "ADS_Main_5"})


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
        try:
            user_obj = await User.get(id=user_id)
            return await User_Pydantic.from_tortoise_orm(user_obj)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        print({"Section": SECTION,"Severity": "ERROR","Message": str(e),"Publish": True,"Tags": "ADS_Main_6"})


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

def automate_login(browser_url:str, user_id:str, password:str, pin:str):
    '''
    Returns request token for Zerodha Kite.

    Arguments:
    browser_url {str} -- The url of the user API.
    user_id {str} -- The user ID to log into.
    password {str} -- The password of the account to log into.
    pin {str} -- The TOTP pin of the account to log into.

    Keyword Arguments:
    None

    Returns:
    request_token {str} -- The request token of the login request.
    '''
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("start-maximized")
    options.add_argument("enable-automation")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-dev-shm-usage")
    try:
        browser = webdriver.Chrome(options = options,executable_path='Chrome/chromedriver')
        browser.get(browser_url)
    except:
        print("Running on cloud server...")
        browser = webdriver.Chrome(options = options)
        browser.get(browser_url)
    
    flag_login = 0
    flag_pin = 0

    for i in range(5):
        try:
            print("Trying to login...")
            userid_element = browser.find_element('xpath',"//input[@type = 'text']")
            userid_element.send_keys(user_id)
            time.sleep(1)
            password_element = browser.find_element('xpath',"//input[@type = 'password']")
            time.sleep(1)
            password_element.send_keys(password)
            password_element.find_element('xpath',"//button[@type='submit']").click()
            time.sleep(1)
            flag_login = 1
            break
        except:
            time.sleep(1)
    if flag_login == 0:
        return -1
    for i in range(5):
        try:
            print("Trying to enter pin...")
            totp = pyotp.TOTP(pin).now()
            pin_element = browser.find_element('xpath',"//input[@type = 'text']")
            pin_element.send_keys(totp)
            time.sleep(1)
            
            flag_pin = 1
            break
        except:
            time.sleep(1)
    if flag_pin == 0:
        return -1
    flag_request = 0
    # time.sleep(2)
    for i in range(5):
        print("Trying to get request token...")
        url = browser.current_url
        tags = url.split('?')[1].split('&')
        request_token = -1
        if len(tags) == 2:
            time.sleep(1)
            continue
        for tag in tags:
            query,result = tag.split('=')
            if query == 'request_token':
                request_token = result
        return str(request_token)
    if flag_request == 0:
        return -1

def auto_login_zerodha(user_details: dict,  log_interface):
    '''
    Auto log into Zerodha Kite.

    Arguments:
    config {Config} -- An object of the Config class.

    Keyword Arguments:
    None

    Returns:
    kite,kws object {list} -- The format of returned list is [kite,kws].
    '''
    #logs.logInfo('Attempting Sign in Dual')
    api_key = user_details['API_KEY']
    api_secret = user_details['API_SECRET']
    user_id = user_details['ID']
    password = user_details['PASSWORD']
    totp_pin = user_details['TOTP_PIN']
    # log_interface.postLog(severity='INFO',message='OMSB: Zerodha login for {}.'.format(user_id),publish=0)

    try:
        browser_url = "https://kite.trade/connect/login?api_key="+str(api_key)+"&v=3"
        user_id = user_id
        password = password
        key = automate_login(browser_url, user_id, password, totp_pin)
        kite = KiteConnect(api_key=api_key)
        data = kite.generate_session(key, api_secret=api_secret)
        # log_interface.postLog(severity='INFO',message='OMSB: Zerodha login succesful for {}.'.format(user_id),publish=0)
        return kite
    except Exception as e:
        # log_interface.postLog(severity="CRITICAL",message='OMSB: Failed auto login to kite for user:{}.'.format(user_id),publish = 1, tag = 'OMSB_AuLoU_1')
        print("Failed to login to Zerodha.")
        print(e)
        traceback.print_exc()


def get_candlestick_data_from_kite(to, kite, instrument_nomenclature):
    '''
    Get candlestick data from kite.
    
    Arguments:
    from {str} -- The start date.
    to {str} -- The end date.

    Keyword Arguments:
    None

    Returns:
    candlestick data {JSON} -- The candlestick data between two dates. 
    '''
    try:
        if type(instrument_nomenclature) == str:
            instrument_nomenclature = int(instrument_nomenclature)
        to = datetime.strptime(to, '%Y-%m-%d %H:%M:%S')
        print(to)

        # Roud off to nearest 5 minutes (down)
        to = to - timedelta(minutes=to.minute % 5, seconds=to.second)
        print('ROUNDED TO: ',to)

        print(to)
        candle = kite.historical_data(
        instrument_nomenclature,
        from_date = to - timedelta(minutes=10) ,
        to_date = to,
        interval = "5minute"
        )

        # from instrument_token get trading symbol from kite

        print(candle)
        print('CLOSE: ',candle[-2]['close'])

        response =  {"candle" : candle, "close" : candle[-2]['close']}
    
        return response

    except Exception as e:
        print(e)
        traceback.print_exc()
        return -1


## ROUTES FOR API USERS end ## 
################
################
## GET ROUTES ##
# Get route to return candlestick data between two dates
@app.get("/candlestick/")
async def get_candlestick_data(history_list: list):
    '''
    Get candlestick data between two dates.
    
    Arguments:
    symbol {str} -- The symbol of the stock.
    start_date {str} -- The start date.
    end_date {str} -- The end date.

    Keyword Arguments:
    None

    Returns:
    candlestick data {JSON} -- The candlestick data between two dates. 
    '''
    print(len(history_list))
    responses = []
    kite = auto_login_zerodha(user_details = {'API_KEY':'wd4rw474uonpvn94','API_SECRET':'8bsd661b6i29y064pei4riikj0lr3ede','ID':'WG5235','PASSWORD':'Finvant@Research1','TOTP_PIN':'BK4I753O24NO5BU5JLTO2JPT2TFT54CC'},log_interface = None)
    print('Login complete')
    for history in history_list:
        print(history)
        end_date = history['end_date']
        instrument_nomenclature = history['instrument_nomenclature']
        trading_symbol = history['trading_symbol']
        price = history['price']
        position = history['position']
        username = history['username']
        brokerage = history['brokerage']

        try:
            end_date = end_date.replace('_', ' ')
            candlestick_data = get_candlestick_data_from_kite(end_date, kite, instrument_nomenclature)
            time.sleep(1)
            ## Add to sql database
            conn = sqlite3.connect('database.db')
            cur = conn.cursor()

            # Table headers : Date, Day, Time, Instrument, 5M Close Entry, Position Entry
            # Query for deleting all the tables (for testing) and reinitializing
            # cur.execute("DROP TABLE slippage;")
            cur.execute('CREATE TABLE IF NOT EXISTS slippage ('\
                'order_time text NOT NULL,'\
                'instrument_nomenclature text NOT NULL,'\
                'Close_5M integer NOT NULL,'\
                'Entry_Exit integer NOT NULL,'\
                'slippage integer NOT NULL,'\
                'username text NOT NULL,'\
                'brokerage text NOT NULL,'\
                'position text NOT NULL'\
            ');')

            # Calculate slippage
            if position == 'CLOSE SHORT' or position == 'BUY':
                slippage = float(candlestick_data['close']) - float(price)
            elif position == 'OPEN SHORT' or position == 'SELL':
                slippage = float(price) - float(candlestick_data['close'])

            # Insert into table
            cur.execute("INSERT INTO slippage VALUES (?,?,?,?,?,?,?,?)", (end_date, trading_symbol, candlestick_data['close'], price, slippage, username, brokerage, position))

            # Commit changes
            conn.commit()

            # Close connection
            conn.close()

            response =  {"candlestick_data": candlestick_data, "slippage": slippage, "price": price, "instrument_nomenclature": instrument_nomenclature, "trading_symbol": trading_symbol}
            # print(str(response))
            responses.append(response)
            
            
        except Exception as e:
            traceback.print_exc()
            print({"Section": "SECTION","Severity": "ERROR","Message": str(e),"Publish": True,"Tags": "ADS_Main_7"})
            return {"Section": "SECTION","Severity": "ERROR","Message": str(e),"Publish": True,"Tags": "ADS_Main_7"}
    return responses

################## """ DATABASE SETUP """ ##################
register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)
