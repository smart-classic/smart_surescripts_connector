""" 
Views for the Indivo Problems app

Ben Adida
ben.adida@childrens.harvard.edu
"""
from indivo_client_py.oauth.oauth import *
from utils import *
from models import *

from django.utils import simplejson
import hospital
from smart import SmartClient
from indivo_client_py.oauth import oauth

from rdflib import ConjunctiveGraph, Namespace, Literal
from StringIO import StringIO
from xml.dom.minidom import parse, parseString
from token_management import *



def indivo_start_auth(request):
    """
    begin the oAuth protocol with the server
    """

    client = get_indivo_client(request, with_session_token=False)
    record_id = request.GET.get('record_id', None)
    print "Started auth for record id", record_id
    # prepare request token parameters
    params = {'oauth_callback':'oob'}
    if record_id:
        params['indivo_record_id'] = record_id

    request_token = parse_token_from_response(client.post_request_token(data=params))
    
    # store the request token in the session for when we return from auth
    request.session['indivo_request_token'] = request_token
    
    print "Stored request token ", request_token
    # redirect to the UI server
    return HttpResponseRedirect(settings.INDIVO_UI_SERVER_BASE + '/oauth/authorize?oauth_token=%s' % request_token['oauth_token'])
    return ""
            
def indivo_after_auth(request):
    """
    after Indivo authorization, exchange the request token for an access token and store it in the web session.
    """

    # get the token and verifier from the URL parameters
    oauth_token, oauth_verifier = request.GET['oauth_token'], request.GET['oauth_verifier']

    # retrieve request token stored in the session
    token_in_session = request.session['indivo_request_token']

    # is this the right token?
    if token_in_session['oauth_token'] != oauth_token:
        return HttpResponse("oh oh bad token")

    # get the indivo client and use the request token as the token for the exchange
    client = get_indivo_client(request, with_session_token=False)
    client.update_token(token_in_session)

    # create the client
    params = {'oauth_verifier' : oauth_verifier}
    access_token = parse_token_from_response(client.post_access_token(data=params))

    id, label =  get_record(access_token)
    request.session['smart_record_id'] = id
    
    save_token(request.session['smart_record_id'], "smart", access_token, label)
    
    print "got rr", id, label
    return HttpResponseRedirect(reverse(home))

    
def hospital_start_auth(request):
    # create the client to Indivo
    client = H9Client()
    print "Client SP", client.server_params
    # prepare request token parameters
    params = {'oauth_callback':reverse(hospital_after_auth)}

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
    access_token = {'oauth_token' : parsed_token.token, 'oauth_token_secret' : parsed_token.secret}
    request.session['hospital_access_token'] = access_token

    save_token(request.session['smart_record_id'], "google", access_token)
    return HttpResponseRedirect(reverse(home))


def home(request):
    id = request.session.get('smart_record_id', None) # fetch ID
    
    indivo_access_token = None
    hospital_access_token = None

    if (id):
        tokens = get_tokens_for_record(id)
        indivo_access_token = 'smart_token' in tokens.keys() and tokens['smart_token']
        hospital_access_token = 'google_token' in tokens.keys() and tokens['google_token']
          
    if indivo_access_token or hospital_access_token:
        conditions = {}

        if indivo_access_token:
            conditions['indivo_record_id'] = indivo_access_token#['xoauth_indivo_record_id']
        if hospital_access_token:
            conditions['hospital_record_id'] = hospital_access_token#.params#['xoauth_hospital_record_id']
        
    return render_template('home', {'indivo_access_token': indivo_access_token, 'hospital_access_token': hospital_access_token, 'conn': None})

def connect(request):
    if request.method == "POST":
        indivo_access_token = request.session.get('indivo_access_token', None)
        hospital_access_token = request.session.get('hospital_access_token', None)
    
        Connection.objects.create(indivo_token = indivo_access_token['oauth_token'],
                                  indivo_secret = indivo_access_token['oauth_token_secret'],
                                  indivo_record_id = indivo_access_token['xoauth_indivo_record_id'],
                                  hospital_token = hospital_access_token.token,
                                  hospital_secret = hospital_access_token.secret,
                                  hospital_record_id = hospital_access_token.params['xoauth_hospital_record_id'])

    return HttpResponseRedirect(reverse(home))
    
def reset(request):
    id = request.session.get('smart_record_id', None)
    delete_token(id, "smart")
    delete_token(id, "google")
    request.session.flush()
    return HttpResponseRedirect(reverse(home))

def google_health_meds(request):
    client = H9Client() # needs tokens here if thsi s gonna work.  
    return HttpResponse(client.get_meds(), mimetype="application/xml")
