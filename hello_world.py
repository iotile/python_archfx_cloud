import os
from cryptography.fernet import Fernet
from archfx_cloud.api.connection import Api
from typing import Dict, List
import pickle

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
        self._area = {}
        self._line = {}

    def __initialize_connection(self):
        # api = Api('https://arch.archfx.io')
        api = Api('https://flex.archfx.io')

        passwd = self.get_password()
        ok = api.login(email=self.email, password=passwd)
        if ok:
            print("logged in successfully!")
            self.api = api
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
        assert isinstance(result_dict, dict)
        if 'results' not in result_dict:
            return None
        results = result_dict['results']
        for n, result in enumerate(results):
            org = str(result.get('org', ''))
            site_name = result.get('name', '')

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


    def query_all_areas(self):
        for site_slug_id in self._sites.keys():
            result_dict: Dict = self.api.area.get(site=site_slug_id)
            for n, result in enumerate(result_dict['results']):
                area_name = result.get('name', '')
                area_slug_id = result.get('slug')
                site_slug_id = result.get('site')
                area_type = result.get('area_type')
                site_info: Dict = self._sites[site_slug_id]
                basic_area_info = {'area_name': area_name, 'area_slug_id': area_slug_id, 'area_type': area_type,
                                   'site_slug_id': site_slug_id}
                basic_area_info.update(site_info)
                self._area[area_slug_id] = basic_area_info
                print("*" * 40)
                print("")
                print(f"n: {n}, ", basic_area_info)


    def query_all_lines(self):
        for area_slug_id in self._area.keys():
            print("#" * 140)
            print("area_slug_id", area_slug_id)
            result_dict: Dict = self.api.line.get(area=area_slug_id)
            for n, result in enumerate(result_dict['results']):
                line_name = result.get('name', '')
                line_slug_id = result.get('slug')
                area_slug_id = result.get('area')
                site_slug_id = result.get('site')
                line_type = result.get('line_type')

                area_info: Dict = self._area[area_slug_id]
                basic_line_info = {'line_name': line_name, 'line_slug_id': line_slug_id, 
                                   'area_slug_id': area_slug_id, 'site_slug_id': site_slug_id,
                                   'line_type': line_type}
                basic_line_info.update(area_info)
                self._line[line_slug_id] = basic_line_info
                print("*" * 40)
                print("")
                print(f"n: {n}, ", result)



    def save_result_so_far(self):
        """
            result.tmp was for just self._tree, self._sites
            result2.tmp    ->   self._tree, self._sites, self._area
            result3.tmp    ->   self._tree, self._sites, self._area, self._line

        """
        with open("result3.tmp", "wb") as writer:
            writer.write(pickle.dumps([self._tree, self._sites, self._area, self._line]))

    def read_result_so_far(self):
        with open("result2.tmp", "rb") as reader:
            data = reader.read()
            result = pickle.loads(data)
            self._tree, self._sites, self._area = result


    def main(self):
        # org_name_list = self.query_all_orgs()
        # self.query_all_sites(org_name_list)
        # self.query_all_areas()

        self.read_result_so_far()
        self.query_all_lines()
        self.save_result_so_far()

        # self.query_all_areas()
        # import pdb; pdb.set_trace()
        # self.query_areas_by_site()


if __name__ == "__main__":
    hw = HelloWorld()
    hw.main()
