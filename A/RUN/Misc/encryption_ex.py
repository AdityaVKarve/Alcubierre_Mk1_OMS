import json
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

""" Run this file as an example of how to encrypt and decrypt data. """

##################### ENCRYPTION #####################
## Read the public key from the file
with open('../Keys/public_key.pem', 'rb') as f:
    public_key_pem = serialization.load_pem_public_key(
        f.read(),
        backend=default_backend()
    )
### Encrypt a message
message_json = {
    "message": "Hello World"
}
message = json.dumps(message_json).encode('utf-8')
encrypted_message = public_key_pem.encrypt(
    message,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)
## Save the encrypted message to a file
with open('encrypted_message.txt', 'wb') as f:
    f.write(encrypted_message)

##################### DECRYPTION #####################
## Read the private key from the file
with open('../Keys/private_key.pem', 'rb') as f:
    private_key_pem = serialization.load_pem_private_key(
        f.read(),
        password=None,
        backend=default_backend()
    )
### Decrypt the message
with open('encrypted_message.txt', 'rb') as f:
    encrypted_message = f.read()
decrypted_message = private_key_pem.decrypt(
    encrypted_message,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)
message = decrypted_message.decode('utf-8')
message_json = json.loads(message)
print(message_json)

## Save the decrypted message to a file
with open('decrypted_message.txt', 'w') as f:
    f.write(message)