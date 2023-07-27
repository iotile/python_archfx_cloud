import os

from cryptography.fernet import Fernet

token_filename = ".cloud_api_token"


def generate_token_file():

    key = Fernet.generate_key()
    print(key)
    filename = os.path.abspath(token_filename)
    print(f"resolved filename: {filename}")

    with open(filename, "wb") as writer:
        writer.write(key)


def read_token_file():
    filename = os.path.abspath(token_filename)
    print(f"filename: {filename}")

    with open(filename, "rb") as reader:
        key = reader.read()
        return key


key = read_token_file()
f = Fernet(key)
secret = f.encrypt(b"Gamma!23")
print(f"secret: {secret}")
# token = f.encrypt(b"my deep dark secret")
# token
# b'...'
# f.decrypt(token)
# b'my deep dark secret'
