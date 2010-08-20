"""
Connect to the hospital API
"""

from utils import *

import urllib, uuid
import httplib

from smart_client.oauth import *
from django.conf import settings

class H9Client(OAuthClient):
    
    def __init__(self, token_dict=None):
        """
        server params includes request_token_url, access_token_url, and authorize_url
        """
       # create an oauth client
        consumer = OAuthConsumer(consumer_key=settings.HOSPITAL_SERVER_OAUTH['consumer_key'], 
                             secret      =settings.HOSPITAL_SERVER_OAUTH['consumer_secret'])
        super(H9Client, self).__init__(consumer = consumer);
        
        self.server_params = settings.HOSPITAL_SERVER_PARAMS
        

        if (token_dict):
            token = OAuthToken(token=token_dict['oauth_token'], secret=token_dict['oauth_token_secret'])
            self.set_token(token)

        il = settings.HOSPITAL_SERVER_LOCATION
        self.baseURL = "%s://%s/"%(il['scheme'], il['host'])

    
    def update_token(self, token):
        # update the access token
        print "uypdating to ", token.token, token.secret
        self.set_token(oauth.OAuthToken(token=token.token, secret = token.secret))
    
    def get_request_token(self):
        print "SPO AR ESTILL", self.server_params        
        http_request = HTTPRequest('POST', self.server_params['request_token_url'], data = None)
        return OAuthToken.from_string(self.access_resource(http_request, oauth_parameters={'scope': 'https://www.google.com/h9/feeds/'}))
    
    def redirect_url(self, request_token):
        """
        Google only does OAuth 1.0, not 1.0a (6/30/2010) so we need to cram in an oauth_Callback parameter here
        """
        ret = "%s?oauth_token=%s&oauth_callback=%s&permission=1" % (self.server_params['authorize_url'], request_token.token, self.server_params['oauth_callback'])
        print "redir to ", ret
        return ret

    def exchange(self, request_token, verifier=None):
        """
        generate a random token, secret, and record_id
        """
        
        access_token = self.fetch_access_token(request_token,verifier)
        return access_token
    
    def access_resource(self, http_request, oauth_parameters = {}, with_content_type=False):
        """
        host is a dictionary containing protocol, hostname, and port
        if port is not specified, it is assumed to be 80 for http, and 443 for https
        """
        # prepare the oauth request
        
        oauth_request = OAuthRequest(self.consumer, self.token, http_request, oauth_parameters=oauth_parameters)
        oauth_request.sign()        
        header = oauth_request.to_header(with_content_type=with_content_type)
        print "accessing", header, http_request.method, http_request.path, http_request.data
    
        # connect and make the request
        url = http_request.path
        data = None
    
        if http_request.method == "GET":
          url += "?" + (http_request.data or "")
        else:
          data = http_request.data or {}
          
        request = urllib2.Request(url, data, header)
        return urllib2.urlopen(request).read()
    
    def get_meds(self):
        med_req = HTTPRequest('GET', '%sh9/feeds/profile/default/-/medication'%self.baseURL, data=None)
        return self.access_resource(med_req)
    
