import os
from cryptography.fernet import Fernet
from archfx_cloud.api.connection import Api

c = Api('https://arch.archfx.io')

email = 'mbrady@archsys.io'
token_filename = '.cloud_api_token'

encrypted_password = b'gAAAAABkwWCtTgQRu9InSILJcLOJSamWDZv5102IxyS3i3MyGkzpby28we57TUXUsGxYotm6hQqdwpAlDlVAoZe-58QZXSB6MA=='

def read_enc_passwd():
    with open('.archfx_enc_passwd', 'rb') as reader:
        return reader.read()


def get_password() -> str:
    key = read_token_file()
    f = Fernet(key)
    secret = f.encrypt(b'Gamma!23')
    print(f"secret: {secret}")
    # token = f.encrypt(b"my deep dark secret")
    # token
    # b'...'
    token = read_enc_passwd()
    passwd = f.decrypt(token)
    passwd = passwd.decode()
    return passwd
    # b'my deep dark secret'



def read_token_file():
    filename = os.path.abspath(token_filename)
    print(f"filename: {filename}")

    with open(filename, 'rb') as reader:
        key = reader.read()
        return key


passwd = get_password()
ok = c.login(email=email, password=passwd)
if ok:
    print("logged in successfully!")
    # Do something
    
    c.logout()
