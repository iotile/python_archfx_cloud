import os
from cryptography.fernet import Fernet
from archfx_cloud.api.connection import Api


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
        token = self.read_enc_passwd()
        passwd = f.decrypt(token)
        passwd = passwd.decode()    # convert to string
        assert isinstance(passwd, str)
        return passwd



    def read_token_file(self):
        filename = os.path.abspath(self.token_filename)
        print(f"filename: {filename}")

        with open(filename, 'rb') as reader:
            key = reader.read()
            return key

    def __init__(self):
        self.__initialize_connection()

    def __initialize_connection(self):
        api = Api('https://arch.archfx.io')

        passwd = self.get_password()
        ok = api.login(email=self.email, password=passwd)
        if ok:
            print("logged in successfully!")
            self.api = api
            # Do something
            
            # api.logout()

    def query_all_orgs(self):
        result_dict = self.api.org.get()
        assert isinstance(result_dict, dict)
        # print(result_dict)
        if 'results' not in result_dict:
            return None
        results = result_dict['results']
        for n, result in enumerate(results):
            result.pop('avatar')
            if 'thumbnail' in result: result.pop('thumbnail')
            print("")
            print(n, result)
        # import pdb; pdb.set_trace()

    def query_all_sites(self):
        result_dict = self.api.site.get()
        # print(result_dict)
        # import pdb; pdb.set_trace()
        assert isinstance(result_dict, dict)
        if 'results' not in result_dict:
            return None
        results = result_dict['results']
        for n, result in enumerate(results):
        #     result.pop('avatar')
        #     if 'thumbnail' in result: result.pop('thumbnail')
            print("")
            print(n, result)



if __name__ == "__main__":
    hw = HelloWorld()
    # hw.query_all_orgs()
    hw.query_all_sites()
