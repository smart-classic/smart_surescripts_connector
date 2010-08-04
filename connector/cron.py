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
import time


def sync_regenstrief():
    tokens = get_tokens_regenstrief()
    print "got tokens, ", tokens
    smart_client = SmartClient()
    regenstrief_client = SSClient()
    for record in tokens:
        t = tokens[record]
        print "Syncing up ", record, t['smart_token'], t['smart_secret'], time.time()

        smart_client.set_token(oauth.OAuthToken(token=t['smart_token'], secret = t['smart_secret']))
        r = smart_client.get_record()
        if (r == None): continue

        #open("/home/jmandel/Desktop/smart/smart_surescripts_connector/connector/tad.xml").read()#
        dispensed_ccr =  regenstrief_client.get_dispensed_meds(r)
        record_id = record.split("http://smartplatforms.org/record/")[1]

        print "GOT CCR: ", time.time()
        put = smart_client.put_ccr_to_smart(record_id, dispensed_ccr)
        print "put is ", put


def sync_google():
    tokens = get_tokens_google()
    print "got tokens, ", tokens
    smart_client = SmartClient()
    gc = H9Client()
    for record in tokens:
        t = tokens[record]
        print "Syncing up ", record, t['google_token'],  t['google_secret']
        smart_client.set_token(oauth.OAuthToken(token=t['smart_token'], secret = t['smart_secret']))
        
        gt = oauth.OAuthToken(token=t['google_token'], secret = t['google_secret'])
        print "GT", gt
        gc.set_token(gt)
         
        h9_ccr = gc.get_meds()

        record_id = record.split("http://smartplatforms.org/record/")[1]

        print "GOT CCR: ", time.time()
        put = smart_client.put_ccr_to_smart(record_id, h9_ccr)
        print "put is ", put

def sync_all():
    try:
        sync_google()
    except: pass
    
    try:
        sync_regenstrief()
    except: pass

if __name__ == "__main__":
    sync_all()

