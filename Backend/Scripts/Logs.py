import logging
from datetime import  datetime
import traceback
import sys





def logInfo(message):
    date = str(datetime.now().date())
    logging.basicConfig(filename='../Logs/log_'+date+'.log', filemode='a', format='%(name)s - %(levelname)s - %(message)s',level=logging.INFO)
    '''
    A generic message, does not indicate any severity
    '''

    print('Info message: '+str(message))
    logging.info(str(datetime.now())+" - "+str(message))

def logWarning(message):
    date = str(datetime.now().date())
    logging.basicConfig(filename='../Logs/log_'+date+'.log', filemode='a', format='%(name)s - %(levelname)s - %(message)s',level=logging.INFO)
    '''
    A warning message, of mild severity
    '''
    print('Warning message: '+str(message))
    logging.warning(str(datetime.now())+" - "+str(message))

def logError(message):
    date = str(datetime.now().date())
    logging.basicConfig(filename='../Logs/log_'+date+'.log', filemode='a', format='%(name)s - %(levelname)s - %(message)s',level=logging.INFO)
    '''
    A error message of high severity
    '''
    print('Error message: '+str(message))
    logging.error(str(datetime.now())+" - "+str(message))

def logCritical(message,exit = False):
    date = str(datetime.now().date())
    logging.basicConfig(filename='../Logs/log_'+date+'.log', filemode='a', format='%(name)s - %(levelname)s - %(message)s',level=logging.INFO)
    '''
    A critical message, Hari Om
    System closes on critical errors
    '''
    print('Critical message: '+str(message))
    for i in traceback.format_exc().splitlines():
        print(i)
    logging.critical('CRITICAL ERROR:'+str(datetime.now())+" - "+str(message)+'\n'+str(traceback.format_exc().splitlines()))
    if exit:
        sys.exit(1)


