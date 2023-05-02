""" MODULES IMPORT """
import base64
from datetime import timedelta, datetime
import datetime
import json
import traceback
from typing import Optional

import os
import jwt

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from passlib.hash import bcrypt
from tortoise.contrib.fastapi import register_tortoise
from tortoise.exceptions import DoesNotExist

from Config import *

# Import jsonable_encoder to convert the pydantic object to a json serializable object
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse

from encryption_hybrid import EncryptionHybrid

from models import (
    User,
    User_Pydantic,
    UserIn_Pydantic,
)

EDITOR = os.environ.get("EDITRO", "vim")


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
        print({"Section": SECTION,"Severity": "ERROR","Message": str(e),"Publish": True,"Tags": "ADS_Main_3"})




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
        print({"Section": SECTION,"Severity": "ERROR","Message": str(e),"Publish": True,"Tags": "ADS_Main_4"})

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


## ROUTES FOR API USERS end ## 
################
################
## GET ROUTES ##
@app.get("/get/user_data")
async def get_user_data(user: User_Pydantic = Depends(get_current_user)):
    '''
    Route to get user data json.
    
    Arguments:
    user {Pydantic model} -- The user model.

    Keyword Arguments:
    None

    Returns:
    JSONResponse {Json} -- The key + encrypted data if valid.
    HTTPException {HTTPException} -- Invalid login. 
    '''
    try:
        try:
            encryption = EncryptionHybrid()
            with open("../Data/user_data.json", "r") as f:
                user_data = f.read()
            
            # Encrypt user data
            encrypted_key, encrypted_data = encryption.encrypt(user_data)
            # convert to hex format
            encrypted_key = encrypted_key.hex()
            encrypted_data = encrypted_data.hex()
            # Package encrypted key and encrypted user data into a dictionary
            response = {
                "encrypted_key": str(encrypted_key),
                "encrypted_data": str(encrypted_data),
            }
            # Encode response to json serializable object for api return
            json_compatible_item_data = jsonable_encoder(
                response, custom_encoder={bytes: lambda v: v.decode("utf-8")}
            )
            return JSONResponse(content=json_compatible_item_data)
            
        except DoesNotExist:
            traceback.print_exc()
            raise HTTPException(status_code=404, detail="User data not found")
    except Exception as e:
        print({"Section": SECTION,"Severity": "ERROR","Message": str(e),"Publish": True,"Tags": "ADS_Main_7"})
        

@app.get("/get/spreads")
async def get_option_spreads(user: User_Pydantic = Depends(get_current_user)):
    '''
    Route to get option spreads json.
    
    Arguments:
    user {Pydantic model} -- The user model.

    Keyword Arguments:
    None

    Returns:
    JSONResponse {Json} -- The key + encrypted data if valid.
    HTTPException {HTTPException} -- Invalid login. 
    '''
    try:
        encryption = EncryptionHybrid()
        try:
            with open("../Data/spreads.json", "r") as f:
                option_spreads = f.read()
        except Exception as e:
            print(e)
            traceback.print_exc()
            raise HTTPException(status_code=404, detail="Option spreads not found")
            
        # Encrypt spread data
        encrypted_key, encrypted_data = encryption.encrypt(option_spreads)
        # convert to hex format
        encrypted_key = encrypted_key.hex()
        encrypted_data = encrypted_data.hex()
        # Package encrypted key and encrypted user data into a dictionary
        response = {
            "encrypted_key": str(encrypted_key),
            "encrypted_data": str(encrypted_data),
        }
        # Encode response to json serializable object for api return
        json_compatible_item_data = jsonable_encoder(
            response, custom_encoder={bytes: lambda v: v.decode("utf-8")}
        )
        return JSONResponse(content=json_compatible_item_data)
        
    except Exception as e:
        print({"Section": SECTION,"Severity": "ERROR","Message": str(e),"Publish": True,"Tags": "ADS_Main_8"})

@app.get("/get/config")
async def get_config(config_file: str, user: User_Pydantic = Depends(get_current_user)):
    print("Getting config")
    '''
    Route to get config data json..
    
    Arguments:
    user {Pydantic model} -- The user model.

    Keyword Arguments:
    None

    Returns:
    JSONResponse {Json} -- The key + encrypted data if valid.
    HTTPException {HTTPException} -- Invalid login. 
    '''
    try:
        try:
            with open(f"../Config/{config_file}.json", "r") as f:
                config = f.read()
                print(config)
        except Exception as e:
            print(e)
            traceback.print_exc()
            raise HTTPException(status_code=404, detail="Config file not found")
        encryption = EncryptionHybrid()
        # Encrypt spread data
        encrypted_key, encrypted_data = encryption.encrypt(config)
        # convert to hex format
        encrypted_key = encrypted_key.hex()
        encrypted_data = encrypted_data.hex()
        # Package encrypted key and encrypted user data into a dictionary
        response = {
            "encrypted_key": str(encrypted_key),
            "encrypted_data": str(encrypted_data),
        }
        # Encode response to json serializable object for api return
        json_compatible_item_data = jsonable_encoder(
            response, custom_encoder={bytes: lambda v: v.decode("utf-8")}
        )
        return JSONResponse(content=json_compatible_item_data)
        
    except Exception as e:
        print({"Section": SECTION,"Severity": "ERROR","Message": str(e),"Publish": True,"Tags": "ADS_Main_9"})

## POST ROUTES ##
@app.post("/post/user_data")
async def post_user_data(data: dict, user: User_Pydantic = Depends(get_current_user)):
    '''
    Route to post new user data.
    
    Arguments:
    data {dict} -- The encrypted user data + key.
    user {Pydantic model} -- The user model.

    Keyword Arguments:
    None

    Returns:
    Json {Json} -- A message stating user data is saved.
    HTTPException {HTTPException} -- Invalid login. 
    '''
    try:
        encrypted_aes_key = data["encrypted_key"]
        encrypted_message = data["encrypted_data"]

        encryption = EncryptionHybrid()
        # convert hex to bytes
        encrypted_aes_key = bytes.fromhex(encrypted_aes_key)
        encrypted_message = bytes.fromhex(encrypted_message)

        decrypted_data = encryption.decrypt(encrypted_aes_key, encrypted_message)
        # convert string to json
        decrypted_data = decrypted_data.replace("\'", '\"')
        decrypted_data = json.loads(decrypted_data)

        # Write to file
        with open("../Data/user_data.json", "w") as f:
            json.dump(decrypted_data, f, indent=4)
        
        
        return {"message": "User data saved"}
    except Exception as e:
        print({"Section": SECTION,"Severity": "ERROR","Message": str(e),"Publish": True,"Tags": "ADS_Main_10"})
        raise HTTPException(status_code=404, detail="Config file not found")
@app.post("/post/spreads")      
async def post_option_spreads(data: dict, user: User_Pydantic = Depends(get_current_user)):
    '''
    Route to post option spreads data.
    
    Arguments:
    data {dict} -- The encrypted spreads data + key.
    user {Pydantic model} -- The user model.

    Keyword Arguments:
    None

    Returns:
    Json {Json} -- A message stating user data is saved.
    HTTPException {HTTPException} -- Invalid login. 
    '''
    try:
        encrypted_aes_key = data["encrypted_key"]
        encrypted_message = data["encrypted_data"]

        encryption = EncryptionHybrid()
        # convert hex to bytes
        encrypted_aes_key = bytes.fromhex(encrypted_aes_key)
        encrypted_message = bytes.fromhex(encrypted_message)

        decrypted_data = encryption.decrypt(encrypted_aes_key, encrypted_message)
        # convert string to json
        decrypted_data = decrypted_data.replace("\'", '\"')
        decrypted_data = json.loads(decrypted_data)
        
        with open("../Data/spreads.json", "w") as f:
            json.dump(decrypted_data, f, indent=4)
        return {"message": "Option spreads saved"}
    except Exception as e:
        print({"Section": SECTION,"Severity": "ERROR","Message": str(e),"Publish": True,"Tags": "ADS_Main_11"})
        raise HTTPException(status_code=404, detail="Config file not found")

@app.post("/post/config")
async def post_config(config_file: str, data: dict, user: User_Pydantic = Depends(get_current_user)):
    '''
    Route to post config spreads data.
    
    Arguments:
    config_file {str} -- The config file to be updated.
    data {dict} -- The encrypted spreads data + key.
    user {Pydantic model} -- The user model.

    Keyword Arguments:
    None

    Returns:
    Json {Json} -- A message stating user data is saved.
    HTTPException {HTTPException} -- Invalid login. 
    '''
    try:
        encrypted_aes_key = data["encrypted_key"]
        encrypted_message = data["encrypted_data"]

        encryption = EncryptionHybrid()
        # convert hex to bytes
        encrypted_aes_key = bytes.fromhex(encrypted_aes_key)
        encrypted_message = bytes.fromhex(encrypted_message)

        decrypted_data = encryption.decrypt(encrypted_aes_key, encrypted_message)
        # convert string to json
        decrypted_data = decrypted_data.replace("\'", '\"')
        decrypted_data = json.loads(decrypted_data)

        with open(f"../Config/{config_file}.json", "w") as f:
            json.dump(decrypted_data, f, indent=4)
        return {"message": "Config saved"}
    except Exception as e:
        print({"Section": SECTION,"Severity": "ERROR","Message": str(e),"Publish": True,"Tags": "ADS_Main_12"})
        raise HTTPException(status_code=404, detail="Config file not found")

## EDIT ROUTES ##
@app.post("/edit/user_data")
async def edit_user_data(user_data_kvp: dict, user_id, user: User_Pydantic = Depends(get_current_user)):
    """
    Edits user data json.
    """
    try:
        try:
            with open("../Data/user_data.json", "r") as f:
                user_data = json.load(f)
            user_data[user_id].update(user_data_kvp)
            with open("../Data/user_data.json", "w") as f:
                json.dump(user_data, f, indent=4)
            return {"message": "User data saved"}
        except:
            raise HTTPException(status_code=404, detail="User data not found")
    except:
        print({"Section": SECTION,"Severity": "ERROR","Message": str(e),"Publish": True,"Tags": "ADS_Main_13"})

################## """ DATABASE SETUP """ ##################
register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)
