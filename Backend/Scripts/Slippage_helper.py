""" MODULES IMPORT """
from datetime import timedelta, datetime
import traceback
import pymysql
import time
from kiteconnect import KiteConnect, KiteTicker
from selenium import webdriver
import pyotp

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

        # Get candlestick data from kite
        print(to)
        candle = kite.historical_data(
        instrument_nomenclature,
        from_date = to - timedelta(minutes=10) ,
        to_date = to,
        interval = "5minute"
        )

        # Get VIX data from kite
        vix_candle = kite.historical_data(
        264969,
        from_date = to - timedelta(minutes=10) ,
        to_date = to,
        interval = "5minute"
        )

        # from instrument_token get trading symbol from kite

        print(candle)
        print('CLOSE: ',candle[-2]['close'])

        print(vix_candle)
        print('VIX CLOSE: ',vix_candle[-2]['close'])

        response =  {"candle" : candle, "close" : candle[-2]['close'], "vix_candle" : vix_candle, "vix_close" : vix_candle[-2]['close']}
    
        return response

    except Exception as e:
        print(e)
        traceback.print_exc()
        return -1

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
        browser = webdriver.Chrome(options = options,executable_path='../Chrome/chromedriver')
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


def get_candlestick_data(history_list: list):
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
            # conn = sqlite3.connect('database.db')
            # cur = conn.cursor()


            conn = pymysql.connect(host="database-1.cc8twgnxgsjl.ap-south-1.rds.amazonaws.com",user="admin",password="FinvantResearch" ,db="test")
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
                'position text NOT NULL,'\
                'vix_close integer NOT NULL,'\
                'slippage_points integer NOT NULL'\
            ');')

            # Calculate slippage
            if position == 'CLOSE SHORT' or position == 'BUY':
                slippage = (float(candlestick_data['close']) - float(price))/float(candlestick_data['close'])*100
            elif position == 'OPEN SHORT' or position == 'SELL':
                slippage = (float(price) - float(candlestick_data['close']))/float(candlestick_data['close'])*100
            
            # Calculate slippage_points
            if position == 'OPEN SHORT' or position == 'BUY':
                slippage_points = price - candlestick_data['close']
            elif position == 'CLOSE SHORT' or position == 'SELL':
                slippage_points = candlestick_data['close'] - price


            vix_close = candlestick_data['vix_close']

            # slippage_points = price - candlestick_data['close']
            # Rouding off to 2 decimal places
            slippage = round(slippage, 2)
            slippage_points = round(slippage_points, 2)

            # Insert into table
            # print(f'INSERT INTO slippage VALUES ("{end_date}", "{trading_symbol}", {candlestick_data["close"]}, {price}, {slippage}, "{username}", "{brokerage}", "{position}", {vix_close}, {slippage_points});')
            query = f'INSERT INTO slippage VALUES ("{end_date}", "{trading_symbol}", {candlestick_data["close"]}, {price}, {slippage}, "{username}", "{brokerage}", "{position}", {vix_close}, {slippage_points});'
            cur.execute(query)

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