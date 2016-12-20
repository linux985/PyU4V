try:
    import ConfigParser as Config
except ImportError:
    import configparser as Config
import json
import logging.config
import requests
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# register configuration file
CONF_FILE = "PyU4V.conf"
LOG = logging.getLogger("PyU4V")
logging.config.fileConfig(CONF_FILE)
CFG = Config.ConfigParser()
CFG.read(CONF_FILE)


class Restful:

    def __init__(self):
        self.username = CFG.get('setup', 'username')
        self.password = CFG.get('setup', 'password')
        server_ip = CFG.get('setup', 'server_ip')
        port = CFG.get('setup', 'port')
        self.verifySSL = CFG.getboolean('setup', 'verify')
        self.cert = CFG.get('setup', 'cert')
        self.base_url = 'https://%s:%s/univmax/restapi' % (server_ip, port)
        self.headers = {'content-type': 'application/json',
                        'accept': 'application/json'}
        self.session = self.establish_rest_session()

    def establish_rest_session(self):
        session = requests.session()
        session.headers = self.headers
        session.auth = HTTPBasicAuth(self.username, self.password)
        session.verify = self.verifySSL
        session.cert = self.cert
        return session

    @staticmethod
    def print_json(json_obj):
        """Takes a REST response and formats the output for
        ease of reading

        :param json_obj: the unformatted json response object
        :returns formatted and printed json object
        """
        print(json.dumps(json_obj, sort_keys=False, indent=2))

    def rest_request(self, target_url, method,
                     params=None, request_object=None):
        """Sends a request (GET, POST, PUT, DELETE) to the target api.

        :param target_url: target url (string)
        :param method: The method (GET, POST, PUT, or DELETE)
        :param params: Additional URL parameters
        :param request_object: request payload (dict)
        :return: server response object (dict)
        """
        if not self.session:
            self.establish_rest_session()
        url = ("%(self.base_url)s%(target_url)s" %
               {'self.base_url': self.base_url,
                'target_url': target_url})
        try:
            if request_object:
                response = self.session.request(
                    method=method, url=url, timeout=60,
                    data=json.dumps(request_object, sort_keys=True,
                                    indent=4))
            elif params:
                response = self.session.request(method=method, url=url,
                                                params=params, timeout=30)
            else:
                response = self.session.request(method=method, url=url,
                                                timeout=30)
            status_code = response.status_code
            try:
                response = response.json()
            except ValueError:
                LOG.info("No response received from API. Status code "
                         "received is: %(status_code)s" %
                         {'status_code': status_code})
                response = status_code
            LOG.info("%(method)s request to %(url)s has returned with "
                     "a status code of: %(status_code)s"
                     % {'method': method, 'url': url,
                        'status_code': status_code})
            return response

        except (requests.Timeout, requests.ConnectionError):
            LOG.error(("The %(method)s request to URL %(url)s "
                       "timed-out, but may have been successful."
                       "Please check the array. ")
                      % {'method': method, 'url': url})
        except Exception as e:
                LOG.error(("The %(method)s request to URL %(url)s "
                           "failed with exception %(e)s")
                          % {'method': method, 'url': url, 'e': e})
                raise
            
    def close_session(self):
        """
        Close the current rest session
        """
        return self.session.close()
