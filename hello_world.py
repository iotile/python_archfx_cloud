import os
from cryptography.fernet import Fernet
from archfx_cloud.api.connection import Api

c = Api('https://arch.archfx.io')


class HelloWorld:

    email = 'mbrady@archsys.io'
    token_filename = '.cloud_api_token'

    def read_enc_passwd(self):
        with open('.archfx_enc_passwd', 'rb') as reader:
            return reader.read()


    def get_password(self) -> str:
        key = self.read_token_file()
        f = Fernet(key)
        secret = f.encrypt(b'Gamma!23')
        print(f"secret: {secret}")
        # token = f.encrypt(b"my deep dark secret")
        # token
        # b'...'
        token = self.read_enc_passwd()
        passwd = f.decrypt(token)
        passwd = passwd.decode()
        return passwd
        # b'my deep dark secret'



    def read_token_file(self):
        filename = os.path.abspath(self.token_filename)
        print(f"filename: {filename}")

        with open(filename, 'rb') as reader:
            key = reader.read()
            return key

    def __init__(self):
        self.__initialize_connection()

    def __initialize_connection(self):
        passwd = self.get_password()
        ok = c.login(email=self.email, password=passwd)
        if ok:
            print("logged in successfully!")
            # Do something
            
            c.logout()


if __name__ == "__main__":
    hw = HelloWorld()
