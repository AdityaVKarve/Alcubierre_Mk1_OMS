import json
import threading
import time
from AutoLoginZerodha import auto_login_zerodha
from AutoLoginOdin import ODIN
from AutoLoginXTS import AutoLoginXTS
from XTS import XTS
import DBManager
from BP import BPWEALTH

class UserProfileGenerator:
    def __init__(self) -> None:
        self.user_groups = []
        self.dict = {}
    
    def thread_function(self,user_data, log_interface):
        print('Number of users in this group: ', len(user_data))
        print("user_data : ", user_data)

        for u in user_data:
            print('Logging in user: ', user_data[u])
            username = u
            user_type = user_data[username]['USER_TYPE']
            login_details = user_data[username]['LOGIN_DETAILS']
            paper_trade = user_data[username]['PAPER_TRADE']
            try:
                if user_type == 'ZERODHA':
                    brokerage_interface = auto_login_zerodha(login_details, log_interface=log_interface)
                elif user_type == 'ODIN':
                    brokerage_interface = ODIN(login_details, log_interface=log_interface)
                elif user_type == 'XTS':
                    brokerage_interface = XTS(app_key=login_details['APP_KEY'],secret=login_details['SECRET'],source=login_details['SOURCE'],client_id=login_details['CLIENT_ID'],endpoint=login_details['ENDPOINT'],log_interface=log_interface)
                elif user_type == 'BPWEALTH':
                    brokerage_interface = BPWEALTH(username=login_details['USERNAME'], password=login_details['PASSWORD'], groupid=login_details['GROUP_ID'], prodcode=login_details['PROD_CODE'], log_interface=log_interface)
                    
                self.dict[username] = {}
                self.dict[username]['USER_TYPE'] = user_type
                self.dict[username]['BROKERAGE_OBJECT'] = brokerage_interface
                self.dict[username]['PAPER_TRADE'] = paper_trade
            except Exception as e:
                log_interface.postLog(severity = "CRITICAL", message = "Failed to login for: {}.".format(username), publish = 1, tag = '')
        

    def create_user_thread(self,username, log_interface):
        thread = threading.Thread(target = self.thread_function, args=[username, log_interface])
        thread.setDaemon(True)
        return thread

    def create_user_profiles(self,user_data, log_interface, debug=False):
        # Slice user_data dict into groups of n users with each group in a dict for multithreading
        user_list_temp = {}
        for i, u in enumerate(user_data):
            if i % 5 == 0 and i > 0:
                self.user_groups.append(user_list_temp)
                user_list_temp = {}
                user_list_temp[u] = user_data[u]
            else:
                user_list_temp[u] = user_data[u]
        self.user_groups.append(user_list_temp)

        if debug:
            print('Number of user groups: ', len(self.user_groups))
            print('User groups: ', self.user_groups)
                            
        user_threads = []
        for u in self.user_groups:
            user_threads.append(self.create_user_thread(u, log_interface))
        with open('../Data/metrics.json','r') as f:
            metrics = json.load(f)
            
        time_before = time.time()
        for t in user_threads:
            t.start()
        for t in user_threads:
            t.join()
        time_after = time.time()
        metrics['USER_PROFILE_GENERATION_TIME'] = (time_after - time_before)*1000

        with open('../Data/metrics.json','w') as f:
            json.dump(metrics,f,indent=4)
            f.close()

        print('LOGIN COMPLETE')
        return self.dict
