import XTS
import AutoLoginXTS
from Log_Server_Interface import Log_Server_Interface
from Config import Config
config = Config()
config.refresh_config()
li = Log_Server_Interface(config=config)
token = AutoLoginXTS.AutoLoginXTS(endpoint = "http://103.156.122.4:10121/", app_key = "595e4768e1d3fb41b5e282", secret = "Bovq746$m0", source = "WEBAPI", log_interface = li)
xts_obj = XTS.XTS(token = token, client_id='9PR22', endpoint="http://103.156.122.4:10121/",log_interface=li)
order_id = xts_obj.place_order(exchange_token=37834, order_type='MARKET',position='BUY',quantity=50)
