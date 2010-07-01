"""
Views for the Indivo Problems app

Ben Adida
ben.adida@childrens.harvard.edu
"""
from indivo_client_py.oauth.oauth import *
from hospital import H9Client
from smart import SmartClient
from indivo_client_py.oauth import oauth
from rdflib import ConjunctiveGraph, Namespace, Literal, URIRef
from StringIO import StringIO
from xml.dom.minidom import parse, parseString
from token_management import *

def sync():
    tokens = get_tokens()
    print "got tokens, ", tokens
    sc = SmartClient()
    gc = H9Client()
    for record in tokens:
        t = tokens[record]
        print "Syncing up ", record, t['google_token'],  t['google_secret']
        sc.set_token(oauth.OAuthToken(token=t['smart_token'], secret = t['smart_secret']))
        
        gt = oauth.OAuthToken(token=t['google_token'], secret = t['google_secret'])
        print "GT", gt
        gc.set_token(gt)
         
        meds = gc.get_meds()
        print "meds are ", meds
        post = sc.post_med_ccr(meds)
        print "post is ", post