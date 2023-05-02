import json
import time
import requests
import helper as helper


class MAIN:
    def __init__(self):
        self.Helper = helper.Helper()

        self.screen_1()

    def getFileScreen(self, file):
        file = self.Helper.getFile(file)

        ## pretty print json
        print(json.dumps(file, indent=4, sort_keys=True))
        # time.sleep(20)

        ## Wait for user to press enter
        print("Press enter to continue")
        input()
        ## clear screen
        print("\033c", end="")
        self.screen_ud()()

    def editFileScreen(self, file):
        message = self.Helper.editFile(file)
        print(message)

        ## Wait for user to press enter
        print("Press enter to continue")
        input()
        print("\033c", end="")
        self.screen_1()

    def screen_1(self):
        print("Welcome to the FINVANT RESEARCH CAPITAL API")
        print("Please select an option:")
        print("1. USER DATA")
        print("2. ORDER BOOK")
        print("3. CONFIGS")
        print("4. Exit")
        option = input("Option: ")
        if option == "1":
            self.screen_ud()
        elif option == "2":
            self.screen_ob()
        elif option == "3":
            self.config_sc()
        elif option == "4":
            exit()
        else:
            print("Invalid option")
            ## clear screen
            print("\033c", end="")
            self.screen_1()

    def config_sc(self):
        print("CONFIGS")
        print("Please select an option:")
        print("1. Get")
        print("2. Edit")

        option = input("Option: ")

        if option == "1":
            self.config_get()
        elif option == "2":
            self.config_edit()
        else:
            print("Invalid option")
            ## clear screen
            print("\033c", end="")
            self.config_sc()

    def config_get(self):
        print("Get config")
        print("Please select an option:")
        print("1. OMS")
        print("2. DATASERVER")
        print("3. LOG")
        print("4. Back")
        option = input("Option: ")

        if option == "1":
            self.getFileScreen("OMS")
        elif option == "2":
            self.getFileScreen("DATASERVER")
        elif option == "3":
            self.getFileScreen("LOG")
        elif option == "4":
            self.config_sc()
        else:
            print("Invalid option")
            ## clear screen
            print("\033c", end="")
            self.config_get()

    def config_edit(self):
        print("Edit config")
        print("Please select an option:")
        print("1. OMS")
        print("2. DATASERVER")
        print("3. LOG")
        print("4. Back")
        option = input("Option: ")

        if option == "1":
            self.editFileScreen("OMS")
        elif option == "2":
            self.editFileScreen("DATASERVER")
        elif option == "3":
            self.editFileScreen("LOG")
        elif option == "4":
            self.config_sc()
        else:
            print("Invalid option")
            ## clear screen
            print("\033c", end="")
            self.config_edit()

    def screen_ob(self):
        print("ORDER BOOK")
        print("Please select an option:")
        print("1. Get order book data")
        print("2. Edit order book")
        print("3. Back")
        option = input("Option: ")

        if option == "1":
            self.getFileScreen("order_book")
        elif option == "2":
            self.editFileScreen("order_book")
        elif option == "3":
            self.screen_1()
        else:
            print("Invalid option")
            ## clear screen
            print("\033c", end="")
            self.screen_ob()

    def screen_ud(self):
        print("USER DATA")
        print("Please select an option:")
        print("1. Get user data data")
        print("2. Edit user data")
        print("3. Back")
        option = input("Option: ")

        if option == "1":
            self.getFileScreen("user_data")
        elif option == "2":
            self.editFileScreen("user_data")
        elif option == "3":
            self.screen_1()
        else:
            print("Invalid option")
            ## clear screen
            print("\033c", end="")
            self.screen_ob()


main = MAIN()