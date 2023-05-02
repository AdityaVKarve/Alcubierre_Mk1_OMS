## Imports
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.fernet import Fernet


## Class to encrypt and decrypt data using hybrid encryption (RSA + AES)
class EncryptionHybrid:
    def __init__(self):
        self.public_key_path = '../Keys/public_key_.pem'
        self.private_key_path = '../Keys/private_key_.pem'
        self.public_key = None
        self.private_key = None
        self.load_keys()

    def generate_keys(self):
        """ Generate a public and private key pair. """
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
    
    def load_keys(self):
        """ Load the public and private keys from the files. """
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
    
    def encrypt(self, message):
        """ Encrypt a message using hybrid encryption (RSA + AES). """
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
    
    def decrypt(self, encrypted_aes_key, encrypted_message):
        """ Decrypt a message using hybrid encryption (RSA + AES). """
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


# Test the encryption and decryption
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