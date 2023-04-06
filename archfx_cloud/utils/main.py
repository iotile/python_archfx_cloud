import sys
import logging
import argparse
import getpass
import configparser

from archfx_cloud.api.connection import Api
from archfx_cloud.api.exceptions import HttpClientError

LOG = logging.getLogger(__name__)
CONFIG = configparser.ConfigParser()


class BaseMain(object):
    parser = None
    args = None
    api = None
    domain = 'https://arch.archfx.io'
    logging_level = logging.INFO

    def __init__(self, config_path='.ini'):
        """
        Initialize Logging configuration
        Initialize argument parsing
        Process any extra arguments
        Only hard codes one required argument: --user
        Additional arguments can be configured by overwriting the add_extra_args() method
        Logging configuration can be changed by overwriting the config_logging() method
        """
        CONFIG.read(config_path)
        self.parser = argparse.ArgumentParser(description=__doc__)
        self.parser.add_argument(
            '-u', '--user', dest='email', type=str, help='Email used for login'
        )
        self.parser.add_argument(
            '--server', dest='server_type', type=str, default='prod',
            help='Server Type: prod/stage/dev'
        )
        self.parser.add_argument(
            '--customer', dest='customer', type=str, default='arch',
            help='Customer slug: arch, stage, acme'
        )

        self.add_extra_args()

        self.args = self.parser.parse_args()
        self.config_logging()

    def _critical_exit(self, msg):
        LOG.error(msg)
        sys.exit(1)

    def main(self):
        """
        Main function to call to initiate execution.
        1. Get domain name and use to instantiate Api object
        2. Call before_login to allow for work before logging in
        3. Logging into the server
        4. Call after_loging to do actual work with server data
        5. Logout
        6. Call after_logout to do work at end of script
        :return: Nothing
        """
        self.domain = self.get_domain()
        self.api = Api(self.domain)
        self.before_login()
        ok = self.login()
        if ok:
            self.after_login()
            self.logout()
            self.after_logout()

    # Following functions can be overwritten if needed
    # ================================================

    def config_logging(self):
        """
        Overwrite to change the way the logging package is configured
        :return: Nothing
        """
        logging.basicConfig(level=self.logging_level,
                            format='[%(asctime)-15s] %(levelname)-6s %(message)s',
                            datefmt='%d/%b/%Y %H:%M:%S')

    def add_extra_args(self):
        """
        Overwrite to change the way extra arguments are added to the args parser
        :return: Nothing
        """
        pass

    def get_domain(self) -> str:
        """
        Figure out server domain URL based on --server and --customer args
        """
        SERVER_TYPE = {
            'prod': 'https://{}.archfx.io',
            'dev': 'http://127.0.0.1:8000'
        }

        domain_template = SERVER_TYPE[self.args.server_type]
        if self.args.server_type == 'prod':
            return domain_template.format(self.args.customer)
        return SERVER_TYPE.get(self.args.server_type)

    def login(self) -> bool:
        """
        Check if we can use token from .ini
        """

        customer_section = f'c-{self.args.customer}'
        try:
            customer_config = CONFIG[customer_section]

            token = customer_config.get('token')
            jwt = {
                'access': customer_config.get('jwt_access'),
                'refresh': customer_config.get('jwt_refresh')
            }
        except (configparser.NoSectionError, KeyError):
            token = None
            jwt = None

        if token:
            self.api.set_token(token, token_type='token')
        elif jwt:
            self.api.set_token(jwt, token_type='jwt')

        if self.api.token:
            try:
                user = getattr(self.api.auth, 'user-info').get()
                LOG.info('Using token for {}'.format(user['email']))
                return True
            except HttpClientError as err:
                LOG.debug(err)
                LOG.info('Token is illegal or has expired')

        if not self.args.email:
            LOG.error('User email is required: --user')
            sys.exit(1)

        password = getpass.getpass()
        ok = self.api.login(email=self.args.email, password=password)
        if ok:
            LOG.info('Welcome {0}'.format(self.args.email))
        return ok

    def logout(self):
        """
        Overwrite to change how to logout from server
        :return: Nothing
        """
        self.api.logout()

    def before_login(self):
        """
        Overwrite to do work after parsing, but before logging in to the server
        This is a good place to do additional custom argument checks
        :return: Nothing
        """
        pass

    def after_login(self):
        """
        This function MUST be overwritten to do actual work after logging into the Server
        :return: Nothing
        """
        LOG.warning('No actual work done')

    def after_logout(self):
        """
        Overwrite if you want to do work after loging out of the server
        :return: Nothing
        """
        pass
