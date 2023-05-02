## Imports
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.fernet import Fernet
from Config import *

## Class to encrypt and decrypt data using hybrid encryption (RSA + AES)
class EncryptionHybrid:
    
    def __init__(self):
        self.public_key_path = '../Keys/public_key.pem'
        self.private_key_path = '../Keys/private_key.pem'
        self.public_key = None
        self.private_key = None
        self.load_keys()

    def generate_keys(self):
        '''
        Generates public + private key pairs. Writes key to public and private key paths.

        Arguments:
        self {self} -- Instance of parent class

        Keyword Arguments:
        None

        Returns:
        None {None} - Returns nothing.
        '''
        try:
            ## Generate a private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            ## Generate a public key
            public_key = private_key.public_key()
            ## Save the private key to a file
            with open(self.private_key_path, 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            ## Save the public key to a file
            with open(self.public_key_path, 'wb') as f:
                f.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
        except Exception as e:
            return {"Section": SECTION,"Severity": "ERROR","Message": str(e),"Publish": True,"Tags": "ADS_EncryptionHybrid_1"}
    
    def load_keys(self):
        '''
        Loads public and private keys and saves them to class objects (self.public_key, self.private_key)
        Arguments:
        self {self} -- Instance of parent class

        Keyword Arguments:
        None

        Returns:
        None {None} - Returns nothing.
        '''
        try:
            with open(self.public_key_path, 'rb') as f:
                self.public_key = serialization.load_pem_public_key(
                    f.read(),
                    backend=default_backend()
                )
            with open(self.private_key_path, 'rb') as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                    backend=default_backend()
                )
        except Exception as e:
            return {"Section": SECTION,"Severity": "ERROR","Message": str(e),"Publish": True,"Tags": "ADS_EncryptionHybrid_2"}
    
    def encrypt(self, message):
        '''
        Encrypts message using hybrid encryption (RSA + AES)

        Arguments:
        self {self} -- Instance of parent class
        message {str} -- message to be encrypted

        Keyword Arguments:
        None

        Returns:
        Tuple {Tuple} - Returns tuple of encrypted message key, encrypted message.
        '''
        try:
            ## Generate a random AES key
            aes_key = Fernet.generate_key()
            ## Encrypt the AES key with RSA
            encrypted_aes_key = self.public_key.encrypt(
                aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            ## Encrypt the message with AES
            f = Fernet(aes_key)
            encrypted_message = f.encrypt(message.encode('utf-8'))
            ## Return the encrypted AES key and the encrypted message
            return encrypted_aes_key, encrypted_message
        except Exception as e:
            return {"Section": SECTION,"Severity": "ERROR","Message": str(e),"Publish": True,"Tags": "ADS_EncryptionHybrid_3"}
    
    def decrypt(self, encrypted_aes_key, encrypted_message):
        '''
        Decrypts message using hybrid encryption (RSA + AES)

        Arguments:
        self {self} -- Instance of parent class
        encrypted_aes_key {bytes} -- key for the encrypted message
        encrypted_message {bytes} -- the encrypted message itself

        Keyword Arguments:
        None

        Returns:
        decrypted_message {str} - Returns decrypted message as a string.
        '''
        """ Decrypt a message using hybrid encryption (RSA + AES). """
        try:
            ## Decrypt the AES key with RSA
            aes_key = self.private_key.decrypt(
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
        except Exception as e:
            return {"Section": SECTION,"Severity": "ERROR","Message": str(e),"Publish": True,"Tags": "ADS_EncryptionHybrid_4"}

# Test the encryption and decryption
'''
if __name__ == '__main__':
    ## Create an EncryptionHybrid object
    encryption = EncryptionHybrid()
    ## Generate a public and private key pair
    # encryption.generate_keys()
    ## Load the public and private keys
    encryption.load_keys()
    ## Load the message to encrypt
    with open('../Data/user_data.json', 'r') as f:
        message = f.read()
    print(type(message))
    # 
    ## Encrypt the message
    encrypted_aes_key, encrypted_message = encryption.encrypt(message)
    ## Decrypt the message
    decrypted_message = encryption.decrypt(encrypted_aes_key, encrypted_message)
    ## Print the decrypted message
    print(decrypted_message)

    msg = {
        "encrypted_aes_key": encrypted_aes_key,
        "encrypted_message": encrypted_message
    }
    print(msg)
'''