"""
    ADT-287  Example code for creating a full factory map for flex.
"""
import os
from cryptography.fernet import Fernet
from typing import Dict, List
import pickle
import pandas as pd
from archfx_cloud.api.connection import Api

DEBUG = False


class QueryFactoryMap:
    def __init__(self, email: str):
        self._email = email
        self.token_filename = ".cloud_api_token"
        self.__initialize_connection()
        self._sites = {}
        self._tree = {}
        self._area = {}
        self._line = {}
        self._devices = {}

    def __initialize_connection(self):
        # api = Api('https://arch.archfx.io')
        api = Api("https://flex.archfx.io")

        passwd = self.get_password()
        ok = api.login(email=self._email, password=passwd)
        if ok:
            print("logged in successfully!")
            self.api = api
            # api.logout()

    # ----------------------------------------------------------------------------------------------------------------
    # deal with secrets
    def read_enc_passwd(self):
        with open(".archfx_enc_passwd", "rb") as reader:
            return reader.read()


    def get_password(self) -> str:
        key = self.read_token_file()
        f = Fernet(key)
        token = self.read_enc_passwd()
        passwd = f.decrypt(token)
        passwd = passwd.decode()  # convert to string
        assert isinstance(passwd, str)
        return passwd


    def read_token_file(self):
        filename = os.path.abspath(self.token_filename)
        print(f"filename: {filename}")

        with open(filename, "rb") as reader:
            key = reader.read()
            return key


    # ----------------------------------------------------------------------------------------------------------------
    # factory_map generating code
    def create_factory_map(self):
        org_name_list = self.query_all_orgs()
        self.query_all_sites(org_name_list)
        self.query_all_areas()

        self.query_all_lines()
        self.save_result_so_far()

        self.query_all_devices()
        self.save_result_so_far()


    def query_all_orgs(self) -> List[str]:
        result_dict = self.api.org.get()
        assert isinstance(result_dict, dict)
        if "results" not in result_dict:
            return None
        results = result_dict["results"]
        org_name_list = []
        for n, result in enumerate(results):
            org_name = result.get("slug")
            if DEBUG:
                if org_name != "flex-smt":
                    continue
            result.pop("avatar")
            if "thumbnail" in result:
                result.pop("thumbnail")
            print("")
            print(n, result)
            org_name_list.append(org_name)
        return org_name_list


    def query_all_sites(self, org_name_list=List[str]):
        for org_name in org_name_list:
            self._tree[org_name] = {}
            print(f"{'#' * 60}     {org_name}        {'#' * 60}")
            self.query_specific_site(org_name)


    def query_specific_site(self, org_name: str):
        result_dict: Dict = self.api.site.get(org=org_name)
        assert isinstance(result_dict, dict)
        if "results" not in result_dict:
            return None
        results = result_dict["results"]
        for n, result in enumerate(results):
            site_slug_id = result["id"]
            if DEBUG:
                if site_slug_id != "ps--0000-0027":
                    continue
            org = str(result.get("org", ""))
            site_name = result.get("name", "")

            basic_site_info = {"site_name": site_name,
                               "site_slug_id": site_slug_id, "org": org}
            self._sites[site_slug_id] = basic_site_info
            if site_slug_id not in self._tree[org]:
                self._tree[org][site_slug_id] = {}


    def query_all_areas(self):
        for site_slug_id in self._sites.keys():
            result_dict: Dict = self.api.area.get(site=site_slug_id)
            for n, result in enumerate(result_dict["results"]):
                area_name = result.get("name", "")
                area_slug_id = result.get("slug")
                site_slug_id = result.get("site")
                area_type = result.get("area_type")
                site_info: Dict = self._sites[site_slug_id]
                basic_area_info = {
                    "area_name": area_name,
                    "area_slug_id": area_slug_id,
                    "area_type": area_type,
                    "site_slug_id": site_slug_id,
                }
                basic_area_info.update(site_info)
                self._area[area_slug_id] = basic_area_info
                org = site_info["org"]
                if area_slug_id not in self._tree[org][site_slug_id]:
                    self._tree[org][site_slug_id][area_slug_id] = {}


    def query_all_lines(self):
        for area_slug_id in self._area.keys():
            print(f"{'$' * 60}     area_slug_id: {area_slug_id}        {'$' * 60}")

            print("area_slug_id", area_slug_id)
            result_dict: Dict = self.api.line.get(area=area_slug_id)
            for n, result in enumerate(result_dict["results"]):
                line_name = result.get("name", "")
                line_slug_id = result.get("slug")
                area_slug_id = result.get("area")
                site_slug_id = result.get("site")
                line_type = result.get("line_type")

                area_info: Dict = self._area[area_slug_id]
                basic_line_info = {
                    "line_name": line_name,
                    "line_slug_id": line_slug_id,
                    "area_slug_id": area_slug_id,
                    "site_slug_id": site_slug_id,
                    "line_type": line_type,
                }
                basic_line_info.update(area_info)
                self._line[line_slug_id] = basic_line_info
                org = area_info["org"]
                if line_slug_id not in self._tree[org][site_slug_id][area_slug_id]:     # pylint: disable=line-too-long  # noqa
                    self._tree[org][site_slug_id][area_slug_id][line_slug_id] = {}  # noqa
                print("*" * 40)
                print("")
                print(f"n: {n}, ", result)

    def query_all_devices(self):
        num_lines = len(self._line.keys())
        for nn, line_slug_id in enumerate(self._line.keys()):
            print(f"{'%' * 60}     {line_slug_id}        {'%' * 60}")
            print(f"nn: {nn} out of {num_lines}, line_slug_id", line_slug_id)
            result_dict: Dict = self.api.device.get(parent=line_slug_id)
            for n, result in enumerate(result_dict["results"]):
                name_label = result.get("label")
                device_slug_id = result.get("slug")
                line_slug_id = result.get("parent")
                connector_type = result.get("connector_type")
                state = result.get("state")

                line_info: Dict = self._line[line_slug_id]
                basic_device_info = {
                    "name_label": name_label,
                    "device_slug_id": device_slug_id,
                    "line_slug_id": line_slug_id,
                    "connector_type": connector_type,
                    "state": state,
                }
                basic_device_info.update(line_info)
                self._devices[device_slug_id] = basic_device_info
                area_slug_id = basic_device_info.get("area_slug_id")
                site_slug_id = basic_device_info.get("site_slug_id")

                org = line_info["org"]
                if device_slug_id not in self._tree[org][site_slug_id][area_slug_id][line_slug_id]:     # noqa
                    self._tree[org][site_slug_id][area_slug_id][line_slug_id][device_slug_id] = basic_device_info   # noqa
                print("*" * 40)
                print("")
                print(f"n: {n}, ", result)

    def save_result_so_far(self):
        with open("result5B.tmp", "wb") as writer:
            writer.write(pickle.dumps([self._tree, self._sites, self._area, self._line, self._devices]))     # noqa


    # ----------------------------------------------------------------------------------------------------------------
    def display_all_devices(self):
        self.read_result_so_far()
        self.iter_over_devices()


    def read_result_so_far(self):
        with open("result5B.tmp", "rb") as reader:
            data = reader.read()
            result = pickle.loads(data)
            self._tree, self._sites, self._area, self._line, self._devices = result  # noqa


    def iter_over_devices(self):
        for n, device_slug_id in enumerate(self._devices):
            print("-" * 60)
            print("")
            print(n, self._devices[device_slug_id])


    # ----------------------------------------------------------------------------------------------------------------
    # convert to pandas
    def result_to_dataframe(self):
        record_list = []
        for x in self._devices:
            record_list.append(self._devices[x])
        df = pd.DataFrame(record_list)
        print(df)
        df.to_csv("result5C.csv")


if __name__ == "__main__":
    email = "mbrady@archsys.io"
    fm = QueryFactoryMap(email)
    fm.create_factory_map()
    # fm.display_all_devices()
    # fm.read_result_so_far()
    fm.result_to_dataframe()
