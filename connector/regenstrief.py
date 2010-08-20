"""
Connect to the hospital API
"""

from utils import *

import urllib, uuid
import httplib

from smart_client.oauth import *
from django.conf import settings

class SSClient():
    def __init__(self, token_dict=None):
       # create an oauth client
        il = settings.REGENSTRIEF_SERVER_LOCATION
        self.baseURL = "%s://%s"%(il['scheme'], il['host'])

    def get_dispensed_meds(self, record):
        url = "%s/sharpAPIServer/meds/query?ln=%s&fn=%s&zipCode=%s&gender=%s&dob=%s"% (
                        self.baseURL, 
                        record['familyName'], 
                        record['givenName'], 
                        record['zipCode'], 
                        (record['gender']=='male' and "M" or "F"),
                        record['DOB']) 
        print "URL: ",url
        request = urllib2.Request(url)
        return urllib2.urlopen(request).read()
