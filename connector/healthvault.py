"""
Connect to the hospital API
"""

from utils import *

import urllib, uuid
import httplib

from smart_client.oauth import *
from django.conf import settings

from string import Template
import uuid, datetime
import sha
import base64
import hmac
import hashlib
import urllib, urllib2
import sys
from M2Crypto import BIO, RSA, EVP
from xml.dom.minidom import parse, parseString

def healthvault_start_auth(request):
    # create the client to Indivo
    client = HVClient()

    request.session['hv_app_token'] = client.get_app_token()
    
    # redirect to the place for authorization
    r = client.redirect_url()
    print "Redirecting to...", r
    return HttpResponseRedirect(r)


def healthvault_after_auth(request):
    # create the client to Indivo
    client = HVClient()
    client.app_token = request.session['hv_app_token']
    client.user_token = request.GET['wctoken']
    r = client.get_meds()
    return render_template('hv_after_auth', {"meds": r})

 

def s(i):
  return "smart"

class HVClient():    
    def __init__(self):
        self.url = "https://platform.healthvault-ppe.com/platform/wildcat.ashx"
        self.shared_secret = "71f4bbba-c1fd-11df-beac-6cf049c58eec"
        self.thumbprint="A7155DE6FF020FFD891148F8D774F05394CDA53E"
        self.app_id="d83310ea-f754-43c8-872c-384c0091cb6a"

        pass

    def redirect_url(self):
        return "https://account.healthvault-ppe.com/redirect.aspx?target=APPAUTH&targetqs=?appid=d83310ea-f754-43c8-872c-384c0091cb6a"
    
    def get_app_token(self):
        rsa = RSA.load_key("%s%s"%(settings.CRYPTO_LOC, "smart.pem"), s)
    
        currtime=datetime.datetime.today().isoformat()
    
        content = Template("""<content><app-id>$app_id</app-id><shared-secret><hmac-alg algName="HMACSHA1">$shared_secret</hmac-alg></shared-secret></content>""")
        content = content.substitute(app_id=self.app_id, shared_secret=base64.b64encode(self.shared_secret))
    
        digest = sha.sha(content).digest()
        rsa_signed_content = base64.b64encode(rsa.sign(digest))
    
    
        message = Template("""<wc-request:request xmlns:wc-request="urn:com.microsoft.wc.request"><header>
        <method>CreateAuthenticatedSessionToken</method><method-version>1</method-version><app-id>$app_id</app-id><language>en</language><country>US</country><msg-time>$currtime</msg-time><msg-ttl>1800</msg-ttl><version>1.1.2193.4712</version></header><info><auth-info><app-id>$app_id</app-id><credential><appserver><sig digestMethod="SHA1" sigMethod="RSA-SHA1" thumbprint="$thumbprint">$rsa_signed_content</sig>$content</appserver></credential></auth-info></info></wc-request:request>""")
    
        message = message.substitute(app_id=self.app_id, currtime=currtime, thumbprint=self.thumbprint, rsa_signed_content=rsa_signed_content,content=content)
        print "Asking for app tokens\n",message
        req = urllib2.Request(self.url, message)
        response = urllib2.urlopen(req)
        the_page = response.read()
        
        print "And got respose\n", the_page
        x = parseString(the_page)
        self.app_token = x.getElementsByTagName("token")[0].childNodes[0].data
        return self.app_token
        
    def get_person(self):
        #https://account.healthvault-ppe.com/redirect.aspx?target=AUTH&targetqs=?appid=d83310ea-f754-43c8-872c-384c0091cb6a
    
        currtime=datetime.datetime.today().isoformat()
        info = """<info><group-membership>true</group-membership></info>"""
    
        s = hashlib.sha1()
        print "info |%s|"%info
        s.update(info)
        info_hash = base64.b64encode(s.digest())
    
        header = Template("""<header><method>GetPersonInfo</method><method-version>1</method-version><auth-session><auth-token>$app_token</auth-token><user-auth-token>$user_token</user-auth-token></auth-session><language>en</language><country>US</country><msg-time>$currtime</msg-time><msg-ttl>1800</msg-ttl><version>0.9.1730.2528</version><info-hash><hash-data algName="SHA1">$info_hash</hash-data></info-hash></header>""").substitute(app_token=self.app_token, user_token=self.user_token,currtime=currtime, info_hash=info_hash)
    
        h = hmac.new(self.shared_secret, "", hashlib.sha1)
        h.update(header)
        header_hash = base64.b64encode(h.digest())
    
        message = Template("""<wc-request:request xmlns:wc-request="urn:com.microsoft.wc.request"><auth><hmac-data algName="HMACSHA1">$header_hash</hmac-data></auth>$header$info</wc-request:request>""").substitute(header_hash=header_hash,header=header,info=info)
    
        req = urllib2.Request(self.url, message)
        response = urllib2.urlopen(req)
        the_page = response.read()
        x = parseString(the_page)
        self.record_id = x.getElementsByTagName("selected-record-id")[0].childNodes[0].data
        return self.record_id
    
    def get_meds(self):
        self.get_person()
        currtime=datetime.datetime.today().isoformat()
    
        info = """<info><group><filter><type-id>30cafccc-047d-4288-94ef-643571f7919d</type-id></filter><format><section>core</section><xml /></format></group></info>"""
    
        s = hashlib.sha1()
        s.update(info)
        info_hash = base64.b64encode(s.digest())
    
        header = Template("""<header><method>GetThings</method><method-version>1</method-version><record-id>$record_id</record-id><auth-session><auth-token>$app_token</auth-token><user-auth-token>$user_token</user-auth-token></auth-session><language>en</language><country>US</country><msg-time>$currtime</msg-time><msg-ttl>1800</msg-ttl><version>0.9.1730.2528</version><info-hash><hash-data algName="SHA1">$info_hash</hash-data></info-hash></header>""").substitute(record_id=self.record_id, app_token=self.app_token, user_token=self.user_token,currtime=currtime, info_hash=info_hash)
    
        h = hmac.new(self.shared_secret, "", hashlib.sha1)
        h.update(header)
        header_hash = base64.b64encode(h.digest())
    
    
        message = Template("""<wc-request:request xmlns:wc-request="urn:com.microsoft.wc.request"><auth><hmac-data algName="HMACSHA1">$header_hash</hmac-data></auth>$header$info</wc-request:request>""").substitute(header_hash=header_hash,header=header,info=info)
    
        req = urllib2.Request(self.url, message)
        response = urllib2.urlopen(req)
        the_page = response.read()
        x = parseString(the_page)
        r = " ".join([m.childNodes[0].data for m in x.getElementsByTagName("text")])

        print the_page
        return r