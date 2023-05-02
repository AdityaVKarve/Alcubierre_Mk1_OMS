import json
import requests
import os, sys, tempfile
from subprocess import call


class Helper:
    def __init__(self) -> None:
        self.user_name = None
        self.user_pass = None
        self.TOKEN = None
        self.endpoint = "http://127.0.0.1:8000/"
        self.OPTION_SPREADS = None

        self.EDITOR = os.environ.get("EDITOR", "vim")

        self.login()

    def getUserDetails(self):
        """Get user details from user"""
        self.user_name = input("Username: ")
        self.user_pass = input("Password: ")

    def login(self):
        """Retrieve access token for accessing protected endpoints"""
        header = {
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        if self.user_name is None or self.user_pass is None:
            self.getUserDetails()
        data = {"username": self.user_name, "password": self.user_pass}
        try:
            print("Signing in...")
            r = requests.post(self.endpoint + "token", headers=header, data=data)
            self.TOKEN = r.json()["access_token"]
        except requests.exceptions.RequestException as e:
            print(e)
            print("Error: Could not connect to server")
            exit(1)
        print("Sign in successful")

    def getFile(self, file):
        """Retrieve file from server"""
        header = {"Authorization": "Bearer " + self.TOKEN}
        try:
            r = requests.get(self.endpoint + "data/" + file + "/get", headers=header)
            return r.json()
        except requests.exceptions.RequestException as e:
            print(e)
            if r.status_code == 401:
                print("Signing in again. Please wait...")
                Helper.login(self)
                Helper.getFile(self, file)
            elif r.status_code == 400:
                print(r.json())
                print("Error: Could not retrieve file")
                exit(1)

    def postFile(self, file, data):
        """Post file to server"""
        header = {"Authorization": "Bearer " + self.TOKEN}
        try:
            r = requests.post(
                self.endpoint + "data/" + file + "/edit", headers=header, data=data
            )
            return "File edited"
        except requests.exceptions.RequestException as e:
            print(e)
            if r.status_code == 401:
                print("Signing in again. Please wait...")
                Helper.login(self)
                Helper.postFile(self, file, data)
            elif r.status_code == 400:
                print(r.json())
                print("Error: Could not post file")
                exit(1)

    def editFile(self, file):
        initial_message = self.getFile(file)
        ## print("Editing file: " + str(initial_message))

        ## Create temporary file with initial message
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(json.dumps(initial_message, indent=4))
            f.close()
            ## print("Editing file: " + f.name)
            call([self.EDITOR, f.name])

            ## Pass the temporary file to the postFile function
            with open(f.name) as f:
                data = f.read()
                message = self.postFile(file, data)
                print("Message: " + message)
                os.remove(f.name)
                return "File edited"