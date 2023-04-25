import requests
from Log_Server_Interface import Log_Server_Interface

def AutoLoginXTS(endpoint: str, app_key:str, secret:str, source:str, log_interface:Log_Server_Interface):
    log_interface.postLog(severity='INFO',message='Attempting XTS login.',publish=0)
    parameters = {
        "appKey": app_key,
        "secretKey": secret,
        "source": source
    }
    try:
        url = endpoint+"/interactive/user/session"
        r = requests.post(url, data = parameters).json()
        token = r['result']['token']
        return token
    except:
        log_interface.postLog(severity='CRITICAL',message='XTS Login failed.',publish=1, tag='OMSB_AuLoU_2')
        return -1