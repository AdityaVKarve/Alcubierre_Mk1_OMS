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


# Import jsonable_encoder to convert the pydantic object to a json serializable object
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse

from A.RUN.encryption_hybrid import EncryptionHybrid

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
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt


async def authenticate_user(username: str, password: str):
    """
    Authenticates user.
    """
    user = await User.get(username=username)
    if user is None:
        return False
    if not user.verify_password(password):
        return False
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)):
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





################# """ ROUTES """ ##################


@app.get("/")
async def index():
    return {"message": "FINVANT RESEARCH CAPITAL API"}


## Route to generate access token
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
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


## Routes for API USERS
## Route to create a new user
@app.post("/users/create", response_model=User_Pydantic)
async def create_user(userIn: UserIn_Pydantic):
    user_obj = User(
        username=userIn.username,
        password_hash=bcrypt.hash(userIn.password_hash),
    )
    await user_obj.save()
    return await User_Pydantic.from_tortoise_orm(user_obj)


## Route to get a user by id
@app.get("/users/{user_id}", response_model=User_Pydantic)
async def get_user(user_id: int, user: User_Pydantic = Depends(get_current_user)):
    try:
        user_obj = await User.get(id=user_id)
        return await User_Pydantic.from_tortoise_orm(user_obj)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")


## Route to get current logged-in user
@app.get("/users/current/", response_model=User_Pydantic)
async def get_user(user: User_Pydantic = Depends(get_current_user)):
    return user


## ROUTES FOR API USERS end ## 
################
################
## GET ROUTES ##
@app.get("/get/user_data")
async def get_user_data(user: User_Pydantic = Depends(get_current_user)):
    """
    Returns user data json.
    """
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
        
    except Exception as e:
        print(e)
        traceback.print_exc()
        raise HTTPException(status_code=404, detail="User data not found")

@app.get("/get/spreads")
async def get_option_spreads(user: User_Pydantic = Depends(get_current_user)):
    """
    Returns option spreads json.
    """
    try:
        encryption = EncryptionHybrid()
        with open("../Data/spreads.json", "r") as f:
            option_spreads = f.read()
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
        print(e)
        traceback.print_exc()
        raise HTTPException(status_code=404, detail="Option spreads not found")

@app.get("/get/config")
async def get_config(config_file: str, user: User_Pydantic = Depends(get_current_user)):
    """
    Returns config json.
    """
    try:
        with open(f"../Config/{config_file}.json", "r") as f:
            config = f.read()
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
        print(e)
        traceback.print_exc()
        raise HTTPException(status_code=404, detail="Config file not found")

## POST ROUTES ##
@app.post("/post/user_data")
async def post_user_data(data: dict, user: User_Pydantic = Depends(get_current_user)):
    """
    Posts user data json.
    """
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
        print(e)
        traceback.print_exc()
        raise HTTPException(status_code=404, detail="User data not found")

@app.post("/post/spreads")      
async def post_option_spreads(data: dict, user: User_Pydantic = Depends(get_current_user)):
    """
    Posts option spreads json.
    """
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
    except:
        raise HTTPException(status_code=404, detail="Option spreads not found")

@app.post("/post/config")
async def post_config(config_file: str, data: dict, user: User_Pydantic = Depends(get_current_user)):
    """
    Posts config json.
    """
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
    except:
        raise HTTPException(status_code=404, detail="Config file not found")

## EDIT ROUTES ##
@app.post("/edit/user_data")
async def edit_user_data(user_data_kvp: dict, user_id, user: User_Pydantic = Depends(get_current_user)):
    """
    Edits user data json.
    """
    try:
        with open("../Data/user_data.json", "r") as f:
            user_data = json.load(f)
        user_data[user_id].update(user_data_kvp)
        with open("../Data/user_data.json", "w") as f:
            json.dump(user_data, f, indent=4)
        return {"message": "User data saved"}
    except:
        raise HTTPException(status_code=404, detail="User data not found")

################## """ DATABASE SETUP """ ##################
register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)
