""" 
Views for the SMArt Connector App

Ben Adida
ben.adida@childrens.harvard.edu

Josh Mandel
joshua.mandel@childrens.harvard.edu
"""
from smart_client.oauth import *
from utils import *
from models import *
from connector.hospital import H9Client
from django.utils import simplejson
from django.utils.safestring import mark_safe
import regenstrief
from smart_client.smart import SmartClient
from xml.dom.minidom import parse, parseString

def indivo_start_auth(request):
    """
    begin the oAuth protocol with the server
    """

    client = get_smart_client() 

    account_id = request.GET.get('account_id', None)
    record_id = request.GET.get('record_id', None)
    request.session['smart_record_id'] = record_id

    print "Started auth for account id", account_id, record_id

    # prepare request token parameters

    params = {'offline' : 'true'}
    
    if record_id:
        params['record_id'] = record_id

    request_token = client.get_request_token(params)
    
    # store the request token in the session for when we return from auth
    request.session['smart_request_token'] = request_token
    
    print "Stored request token ", request_token

    # redirect to the UI server
    return HttpResponseRedirect(client.redirect_url(request_token))

            
def indivo_after_auth(request):
    """
    after Indivo authorization, exchange the request token for an access token and store it in the web session.
    """
    oauth_token, oauth_verifier = request.GET['oauth_token'], request.GET['oauth_verifier']
    token_in_session = request.session['smart_request_token']

    # is this the right token?
    if token_in_session.token != oauth_token:
        return HttpResponse("oh oh bad token")

    # get the indivo client and use the request token as the token for the exchange
    client = get_smart_client()
    client.update_token(token_in_session)

    parsed_token = client.exchange(token_in_session, oauth_verifier)
    get_smart_client().save_token(request.session['smart_record_id'],  parsed_token, "smart")
    
    return HttpResponseRedirect(reverse(home))
    
def hospital_start_auth(request):
    # create the client to Indivo
    client = H9Client()
    print "Client SP", client.server_params

    record_id = request.session.get('smart_record_id', None)
    if (record_id == None):
        raise Exception("Hospital auth shouldn't start with no smart_record_id defined!")

    # request a request token
    request_token = client.get_request_token()
    
    # store the request token in the session for when we return from auth
    request.session['hospital_request_token'] = request_token
    
    # redirect to the place for authorization
    return HttpResponseRedirect(client.redirect_url(request_token))

def hospital_after_auth(request):
    # get the token and verifier from the URL parameters
    oauth_token = request.GET['oauth_token']
    
    try:  oauth_verifier = request.GET['oauth_verifier']
    except:  oauth_verifier = None
    
    print "T,V: ", oauth_token, oauth_verifier

    # retrieve request token stored in the session
    token_in_session = request.session['hospital_request_token']
    print "TiS: ", token_in_session

    # is this the right token?
    if token_in_session.token != oauth_token:
        return HttpResponse("oh oh bad token")

    # get the indivo client and use the request token as the token for the exchange
    client = H9Client()

    # create the client
    parsed_token = client.exchange(token_in_session, oauth_verifier)
    get_smart_client().save_token(request.session['smart_record_id'], parsed_token, "google")
    return render_template('hospital_after_auth', {})

def home(request):
    id = request.session.get('smart_record_id', None) # fetch ID
    sc = get_smart_client()

    smart_access_token = None
    hospital_access_token = None

 
    if (id):
        tokens = {}

        tokens['smart_token'] = sc.get_tokens_for_record(id, "smart")
        tokens['google_token'] = sc.get_tokens_for_record(id, "google")
            
        smart_access_token = 'smart_token' in tokens.keys() and tokens['smart_token'] and tokens['smart_token'].token
        hospital_access_token = 'google_token' in tokens.keys() and tokens['google_token'] and tokens['google_token'].token
    
            
    return render_template('home', {'smart_access_token': smart_access_token, 'hospital_access_token': hospital_access_token})

    
def reset(request):
    id = request.session.get('smart_record_id', None)
    client = get_smart_client()
    client.delete_token(id, "smart")
    client.delete_token(id, "google")
    request.session.flush()
    return render_template('reset')

def google_health_meds(request):
    client = H9Client() # needs tokens here if thsi s gonna work.  
    return HttpResponse(client.get_meds(), mimetype="application/xml")
