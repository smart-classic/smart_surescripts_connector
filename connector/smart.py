"""
Connect to the SMArt API
"""

import urllib, uuid
import httplib
from django.conf import settings
from indivo_client_py.oauth.oauth import *
from indivo_client_py.oauth import oauth
from rdf_utils import *
import time

import RDF
    
class SmartClient(OAuthClient):
    def __init__(self, token_dict=None):
        """
        server params includes request_token_url, access_token_url, and authorize_url
        """
       # create an oauth client
        consumer = OAuthConsumer(consumer_key=settings.SMART_SERVER_OAUTH['consumer_key'], 
                             secret      =settings.SMART_SERVER_OAUTH['consumer_secret'])

        super(SmartClient, self).__init__(consumer = consumer);
        self.server_params = settings.SMART_SERVER_PARAMS
        if (token_dict):
            token = OAuthToken(token=token_dict['oauth_token'], secret=token_dict['oauth_token_secret'])
            self.set_token(token)

        il = settings.SMART_SERVER_LOCATION
        self.baseURL = "%s://%s:%s"%(il['scheme'], il['host'], il['port'])
        self.saved_ids = {}
        
    def access_resource(self, http_request, oauth_parameters = {}, with_content_type=False):
        """
        host is a dictionary containing protocol, hostname, and port
        if port is not specified, it is assumed to be 80 for http, and 443 for https
        """
        # prepare the oauth request
        
        oauth_request = OAuthRequest(self.consumer, self.token, http_request, oauth_parameters=oauth_parameters)
        oauth_request.sign()        
        header = oauth_request.to_header(with_content_type=with_content_type)
    
        from urlparse import urlparse
        o = urlparse(http_request.path)

        if (o.scheme == "http"):
            conn = httplib.HTTPConnection("%s"%o.netloc)
        elif (o.scheme == "https"):
            conn = httplib.HTTPSConnection("%s"%o.netloc)
    
        data = None
        path = o.path
        if (http_request.method == "GET"):
            path +=  "?"+(http_request.data or "")
        else:
            data = http_request.data or {}
        conn.request(http_request.method, path, data, header)
        r = conn.getresponse()
        data = r.read()
        conn.close()
        return data
    
    
    def put_rdf_store(self, graph):
        req = HTTPRequest('PUT', '%s/rdf_store/'%self.baseURL, data=graph.serialize(), data_content_type="application/rdf+xml")
        return self.access_resource(req,with_content_type=True)
    
    def delete_rdf_store(self, sparql):
        req = HTTPRequest('DELETE', '%s/rdf_store/'%self.baseURL, data=urllib.urlencode({'SPARQL' : sparql}), data_content_type="application/x-www-form-urlencoded")
        return self.access_resource(req,with_content_type=True)
        
    def get_rdf_store(self, sparql=None):
        if sparql:
            req = HTTPRequest('GET', '%s/rdf_store/'%self.baseURL, 
                              data=urllib.urlencode({ "SPARQL": sparql }),
                              data_content_type="application/x-www-form-urlencoded")
            
            return self.access_resource(req, with_content_type=True)

        else:
            req = HTTPRequest('GET', '%s/rdf_store/'%self.baseURL, data=None)
            return self.access_resource(req)

    def get(self, url, data):
            req = HTTPRequest('GET', '%s%s'%(self.baseURL, url), data=data)
            return self.access_resource(req)

    def post(self, url, data, content_type):
            req = HTTPRequest('POST', '%s%s'%(self.baseURL, url), data=data, data_content_type=content_type)
            return self.access_resource(req,with_content_type=True)
        
    def put(self, url, data, content_type):
            req = HTTPRequest('PUT', '%s%s'%(self.baseURL, url), data=data, data_content_type=content_type)
            return self.access_resource(req,with_content_type=True)

    def post_med_ccr(self, record_id, data):
            return self.post("/med_store/records/%s/"%record_id, data, "application/xml" )


    def update_token(self, token):
        self.set_token(oauth.OAuthToken(token=token.token, secret = token.secret))
    
    def get_request_token(self, params={}):
        http_request = HTTPRequest('POST', self.server_params['request_token_url'], data = urllib.urlencode(params), data_content_type="application/x-www-form-urlencoded")

        return OAuthToken.from_string(self.access_resource(http_request, oauth_parameters={'oauth_callback': self.server_params['oauth_callback']}, with_content_type=True))
    
    def redirect_url(self, request_token):
        ret = "%s?oauth_token=%s" % (self.server_params['authorize_url'], request_token.token)
        return ret

    def exchange(self, request_token, verifier=None):
        """
        generate a random token, secret, and record_id
        """
        req = HTTPRequest('GET', self.server_params['access_token_url'], data = None)
        token = OAuthToken.from_string(self.access_resource(req, oauth_parameters={'oauth_verifier' : verifier}))
        self.set_token(token)
        return token

    def get_record(self):
        result = self.get("/record_by_token/", None)
        demographics = RDF.Model()
        parse_rdf(result, demographics)

        q = RDF.SPARQLQuery("""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX foaf:   <http://xmlns.com/foaf/0.1/>
        PREFIX sp: <http://smartplatforms.org/>
        SELECT DISTINCT ?s, ?gn, ?fn, ?zip, ?gender, ?birthday
        WHERE {
            ?s rdf:type foaf:Person.
            ?s foaf:givenName ?gn.
            ?s foaf:familyName ?fn.
            ?s sp:zipcode ?zip.
            ?s foaf:gender ?gender.
            ?s sp:birthday ?birthday.
        }""")
              
        try:
            r =  q.execute(demographics)
            r = r.next()
            ret = {}
            ret['givenName'] = r['gn'].literal_value['string']
            ret['familyName'] = r['fn'].literal_value['string']
            ret['zipCode'] = r['zip'].literal_value['string']
            ret['gender'] = r['gender'].literal_value['string']
            ret['DOB'] = r['birthday'].literal_value['string']
            return ret
        except:
            return None


    def put_ccr_to_smart(self, record_id, ccr_string):
        rdf_string  = xslt_ccr_to_rdf(ccr_string)
        model = parse_rdf(rdf_string)
        
        print "START PUTTING:  ", time.time()
        med_uris = get_medication_uris(model)

        for med_uri in med_uris:
            self.put_med_helper(model, med_uri, record_id)    
        
        print "MEDS DONE: ", time.time()
        med_count = {}
        for med_uri in med_uris:
            med_count[str(med_uri)] = 0
            for fill_uri in get_fill_uris(model, med_uri):
                med_count[str(med_uri)] += 1
                self.put_fill_helper(model, med_uri, fill_uri, record_id)
        print "FILLS DONE: ", time.time()
        
        total = 0
        print "Total fills: ", len(med_count.keys())
        
    def put_med_helper(self, g, med_uri, record_id):
        external_id = med_external_id(g, med_uri)
        med = get_medication_model(g, med_uri)
        self.smart_med_put(record_id, external_id, serialize_rdf(med))    
        
    def put_fill_helper(self, g, med_uri, fill_uri, record_id):
        ext_med = med_external_id(g, med_uri)
        ext_fill = fill_external_id(g, fill_uri)
        ext_fill = "%s_%s"%(ext_med, ext_fill)
        
        fill = get_fill_model(g, fill_uri)        
        
        self.smart_fill_put(record_id, ext_med, ext_fill, serialize_rdf(fill)) 

    def smart_med_put(self, record_id, external_id, data):
        try:
            if (self.saved_ids[external_id]): return
        except KeyError:           
            self.saved_ids[external_id]  = True
        
        return self.put("/records/%s/medications/external_id/%s"%(record_id, external_id), data, "application/rdf+xml")
    
    def smart_fill_put(self, record_id, med_external_id, fill_external_id, data):
        try:
            if (self.saved_ids[fill_external_id]): return
        except KeyError:           
            self.saved_ids[fill_external_id]  = True
        
        return self.put("/records/%s/medications/external_id/%s/fulfillments/external_id/%s"%(record_id, med_external_id, fill_external_id), 
                        data, "application/rdf+xml")
        
