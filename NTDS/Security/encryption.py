import base64
import requests

import json
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.fernet import Fernet
import time
import numpy as np
import matplotlib.pyplot as plt
from fastapi.encoders import jsonable_encoder


class Encryption:
    def __init__(self, public_key_path, private_key_path):
        self.backend = default_backend()
        self.public_key = None
        self.private_key = None
        self.fernet = None
        self.public_key_path = public_key_path
        self.private_key_path = private_key_path

    def decrypt(self, encrypted_aes_key, encrypted_message):
        """ Decrypt a message using hybrid encryption (RSA + AES). """

        ## Decrypt the AES key with RSA
        with open(self.private_key_path, 'rb') as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
        aes_key = private_key.decrypt(
            encrypted_aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        ## Decrypt the message with AES
        f = Fernet(aes_key)
        decrypted_message = f.decrypt(encrypted_message).decode('utf-8')
        ## Return the decrypted message
        return decrypted_message

    def encrypt(self, message):
        """ Encrypt a message using hybrid encryption (RSA + AES). """

        ## Generate a random AES key
        with open(self.public_key_path, 'rb') as f:
            public_key = serialization.load_pem_public_key(
                f.read(),
                backend=default_backend()
            )
        aes_key = Fernet.generate_key()
        ## Encrypt the AES key with RSA
        encrypted_aes_key = public_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        ## Encrypt the message with AES
        f = Fernet(aes_key)
        message = str(message)
        encrypted_message = f.encrypt(message.encode('utf-8'))

        # convert to hex format
        encrypted_key = encrypted_aes_key.hex()
        encrypted_data = encrypted_message.hex()
        # Package encrypted key and encrypted user data into a dictionary
        response = {
            "encrypted_key": str(encrypted_key),
            "encrypted_data": str(encrypted_data),
        }
        # Encode response to json serializable object for api return
        json_compatible_item_data = jsonable_encoder(
            response, custom_encoder={bytes: lambda v: v.decode("utf-8")}
        )

        return json_compatible_item_data