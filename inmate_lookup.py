from urllib.parse import urlencode
from bs4 import BeautifulSoup
from opener import Opener

class InmateLookup:
    url_root = 'http://66.217.205.242:8180/'

    def __init__(self):
        self.opener = Opener('inmate')

    def url(self, url):
        return InmateLookup.url_root + url

    def open_home_page(self):
        url = self.url('IML')
        page = self.opener.open(url)
        return BeautifulSoup(page.read(), 'html.parser')

    def do_inmate_search(self):
        data = {
            'flow_action': 'searchbyname',
            'quantity':'10',
            'systemUser_identifiervalue':'',
            'searchtype':'PIN',
            'systemUser_includereleasedinmate':'Y',
            'systemUser_includereleasedinmate2':'N',
            'systemUser_firstName':'',
            'systemUser_lastName':'',
            'systemUser_dateOfBirth':'',
            'releasedA':'checkbox',
            'identifierbox':'PIN',
            'identifier':''
        }
        data = urlencode(data)
        url = self.url('IML')
        page = self.opener.open(url, data)
        return BeautifulSoup(page.read(), 'html.parser')
