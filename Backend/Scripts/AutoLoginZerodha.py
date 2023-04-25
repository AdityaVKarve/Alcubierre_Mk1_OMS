from selenium import webdriver
import time
from datetime import datetime
import pandas as pd
from kiteconnect import KiteConnect, KiteTicker
#import Logs as logs
import pyotp
from Config import Config
from Log_Server_Interface import Log_Server_Interface

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

def auto_login_zerodha(user_details: dict,  log_interface: Log_Server_Interface):
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
    log_interface.postLog(severity='INFO',message='OMSB: Zerodha login for {}.'.format(user_id),publish=0)

    try:
        browser_url = "https://kite.trade/connect/login?api_key="+str(api_key)+"&v=3"
        user_id = user_id
        password = password
        key = automate_login(browser_url, user_id, password, totp_pin)
        kite = KiteConnect(api_key=api_key)
        data = kite.generate_session(key, api_secret=api_secret)
        log_interface.postLog(severity='INFO',message='OMSB: Zerodha login succesful for {}.'.format(user_id),publish=0)
        return kite
    except:
        log_interface.postLog(severity="CRITICAL",message='OMSB: Failed auto login to kite for user:{}.'.format(user_id),publish = 1, tag = 'OMSB_AuLoU_1')
    
