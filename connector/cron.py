"""
Views for the Indivo Problems app

Ben Adida
ben.adida@childrens.harvard.edu
"""
from smart_client.oauth import *
from utils import *
from hospital import H9Client
from regenstrief import SSClient
from smart_client.smart import SmartClient
from xml.dom.minidom import parse, parseString
import time


def sync_regenstrief():
    
    tokens = get_smart_client().get_all_tokens(["smart"])
    print "got tokens, ", tokens

    regenstrief_client = SSClient()
    smart_client = get_smart_client()

    for record in tokens:
        st = tokens[record]['smart']
        print "Syncing up ", record, st.token, st.secret, time.time()

        smart_client.set_token(st)

        r = smart_client.get_record()
        if (r == None): continue

        dispensed_ccr =   open("/home/jmandel/Desktop/smart/smart_surescripts_connector/connector/tad.xml").read()#
#        dispensed_ccr =  regenstrief_client.get_dispensed_meds(r)
        print "rid: ", record
        record_id = record.split("http://smartplatforms.org/records/")[1]

        print "GOT CCR: ", time.time()
        put = smart_client.put_ccr_to_smart(record_id, dispensed_ccr)
        print "put is ", put


def sync_google():
    print "Getting tokens"
    tokens = get_smart_client().get_all_tokens(["smart", "google"])
    print "got tokens, ", tokens

    gc = H9Client()
    for record in tokens:
        try:
            gt = tokens[record]['google']
        except: 
            continue

        st = tokens[record]['smart']

        smart_client = get_smart_client()
        print "Syncing up ", record, st.token, st.secret

        smart_client.set_token(st)
        gc.set_token(gt)
         
        h9_ccr = gc.get_meds()
        print "record", record
        record_id = record.split("http://smartplatforms.org/records/")[1]

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

