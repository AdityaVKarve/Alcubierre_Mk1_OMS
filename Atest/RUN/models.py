from tortoise import fields, models
from tortoise.models import Model
from tortoise.contrib.pydantic import pydantic_model_creator

from passlib.hash import bcrypt
from typing import List, Optional, Union

""" SCHEMA """


class User(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=20, unique=True)
    password_hash = fields.CharField(max_length=100)

    class Meta: 
        table = "users"

    def __str__(self):
        return self.username

    def verify_password(self, password):
        return bcrypt.verify(password, self.password_hash)


class User_Finvant(Model):
    id_ = fields.IntField(pk=True)
    username = fields.CharField(max_length=20, unique=True)
    password_hash = fields.CharField(max_length=100)

    API_KEY = fields.CharField(max_length=100, unique=True)
    API_SECRET = fields.CharField(max_length=100, unique=True)
    pin = fields.IntField(max_length=40, unique=True)
    ID = fields.CharField(max_length=100, unique=True)
    amount = fields.IntField(max_length=40, unique=True)
    totp_pin = fields.CharField(max_length=100, unique=True)

    class Meta:
        table = "users_finvant"

    def __str__(self):
        return self.username

    def verify_password(self, password):
        return bcrypt.verify(password, self.password_hash)


class OptionSpread(Model):
    ## Name of the option spread is a unique identifier
    name = fields.CharField(max_length=100, unique=True)
    leg_count = fields.IntField(default=0)
    # legs is a list of lists
    legs: List[List[Union[str, int, float]]] = fields.JSONField()

    class Meta:
        table = "option_spreads"

    def count_legs(self):
        ## Set the leg_count as the length of the legs list
        self.leg_count = int(len(self.legs))
        return self.leg_count

    class PydanticMeta:
        computed = ["count_legs"]

    def __str__(self):
        return self.name


## Pydantic Models
## USERS
User_Pydantic = pydantic_model_creator(User, name="User")  ## User_Pydantic = User Model
UserIn_Pydantic = pydantic_model_creator(
    User, name="UserIn", exclude_readonly=True
)  ## Incoming

## OPTION SPREADS
OptionSpread_Pydantic = pydantic_model_creator(OptionSpread, name="OptionSpread")
OptionSpreadIn_Pydantic = pydantic_model_creator(
    OptionSpread, name="OptionSpreadIn", exclude_readonly=True
)  # Incoming


## USERS FINVANT
User_Finvant_Pydantic = pydantic_model_creator(User_Finvant, name="User_Finvant")
UserIn_Finvant_Pydantic = pydantic_model_creator(
    User_Finvant, name="UserIn_Finvant", exclude_readonly=True
)  # Incoming