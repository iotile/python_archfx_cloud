import os
from cryptography.fernet import Fernet
from archfx_cloud.api.connection import Api
from typing import Dict, List

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
        self._sites = {}
        self._tree = {}

    def __initialize_connection(self):
        # api = Api('https://arch.archfx.io')
        api = Api('https://flex.archfx.io')

        passwd = self.get_password()
        ok = api.login(email=self.email, password=passwd)
        if ok:
            print("logged in successfully!")
            self.api = api
            # Do something
            
            # api.logout()


    def query_all_orgs(self) -> List[str]:
        result_dict = self.api.org.get()
        assert isinstance(result_dict, dict)
        # print(result_dict)
        if 'results' not in result_dict:
            return None
        results = result_dict['results']
        org_name_list = []
        for n, result in enumerate(results):
            result.pop('avatar')
            if 'thumbnail' in result: result.pop('thumbnail')
            print("")
            print(n, result)
            org_name = result.get('slug')
            org_name_list.append(org_name)
        return org_name_list


    def query_all_sites(self, org_name_list = List[str]):
        for org_name in org_name_list:
            self._tree[org_name] = {}
            print("#" * 140)
            self.query_specific_site(org_name)

    def query_specific_site(self, org_name: str):
        result_dict: Dict = self.api.site.get(org=org_name)
        print(org_name, result_dict['count'])
        # import pdb; pdb.set_trace()
        assert isinstance(result_dict, dict)
        if 'results' not in result_dict:
            return None
        results = result_dict['results']
        for n, result in enumerate(results):
            org = str(result.get('org', ''))
            site_name = result.get('name', '')

            # if ('demo' in org) or ('-it' in org):
            #     continue
            site_slug_id = result['id']
            basic_site_info = {'site_name': site_name, 'site_slug_id': site_slug_id, 'org': org}
            self._sites[site_slug_id] = basic_site_info
            self._tree[org][site_slug_id] = basic_site_info

            # print("*" * 40)
            # print("")
            # print("org ", org)
            # print("site_name", site_name)
            # print(n, result)
        print(org_name, len(self._sites))
        # import pdb; pdb.set_trace()


    def main(self):
        org_name_list = self.query_all_orgs()
        self.query_all_sites(org_name_list)
        # import pdb; pdb.set_trace()


if __name__ == "__main__":
    hw = HelloWorld()
    hw.main()
