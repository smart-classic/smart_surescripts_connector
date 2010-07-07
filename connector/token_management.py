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

def get_record(access_token):
    x = SmartClient(access_token).get("/record_by_token/", None)
    result = parseString(x)
    return [result.firstChild.getAttribute(l) for l in ['id', 'label']]


def get_predicate(graph, p):
    return [str(x[2]) for x in graph.triples((None, URIRef(p), None))][0]

def get_tokens_for_record(record_id):
    print "Getting tokens for ", record_id
    q = """CONSTRUCT {?s ?p ?o} WHERE {?s ?p ?o
                                filter (?s = <http://smartplatforms.org/record/%s>)
                     }"""%record_id
    g = ConjunctiveGraph()
    r = SmartClient().get_rdf_store(q)
    print r
    g.parse(StringIO(r))
    
    base = "http://surescripts-loader.apps.smartplatforms.org/%s"
    targets = ['smart_token', 'smart_secret', 'google_token', 'google_secret']
    
    ret = {}
    for t in targets:
        try:
            ret[t] = get_predicate(g, base%t)
        except: pass
    print "tokens ", ret
    return ret

def get_tokens():
    q = """CONSTRUCT {
        ?record <http://surescripts-loader.apps.smartplatforms.org/smart_token> ?smart_token.
        ?record <http://surescripts-loader.apps.smartplatforms.org/smart_secret> ?smart_secret.
        ?record <http://surescripts-loader.apps.smartplatforms.org/google_token> ?google_token.
        ?record <http://surescripts-loader.apps.smartplatforms.org/google_secret> ?google_secret.
        } WHERE {
        ?record <http://surescripts-loader.apps.smartplatforms.org/smart_token> ?smart_token.
        ?record <http://surescripts-loader.apps.smartplatforms.org/smart_secret> ?smart_secret.
        ?record <http://surescripts-loader.apps.smartplatforms.org/google_token> ?google_token.
        ?record <http://surescripts-loader.apps.smartplatforms.org/google_secret> ?google_secret.
        }"""
    g = ConjunctiveGraph()
    r = SmartClient().get_rdf_store(q)
    print r
    g.parse(StringIO(r))

    base = "http://surescripts-loader.apps.smartplatforms.org/%s"
    targets = ['smart_token', 'smart_secret', 'google_token', 'google_secret']
    tokens = {}
    for r in set(g.subjects()):
        token = {}
        for t in targets:
            token[t] = str(g.triples((r, URIRef(base%t), None)).next()[2])
        tokens[r] = token
    return tokens


def delete_token(id, service):
    q = """
        CONSTRUCT { <http://smartplatforms.org/record/%s> ?p ?t.}
        WHERE { 
        <http://smartplatforms.org/record/%s> ?p ?t
        FILTER (
            ?p = <http://surescripts-loader.apps.smartplatforms.org/%s_token> || 
            ?p = <http://surescripts-loader.apps.smartplatforms.org/%s_secret>)
        }""" % (id,id,service,service)
    
    print "*******************Woudl delete", q
    SmartClient().delete_rdf_store(q)
    
def save_token(id, service, access_token, label=None):
    # Don't want multiple keys pointing to multiple tokens -- get rid of the existing ones first!
    delete_token(id, service)
    graph = ConjunctiveGraph()    
    ss=Namespace("http://surescripts-loader.apps.smartplatforms.org/")
    record=Namespace("http://smartplatforms.org/record/")
    dc = Namespace('http://purl.org/dc/elements/1.1/')
        
    if (label):
        graph.add((record[id], dc['title'], Literal(label)))
    graph.add((record[id], ss['%s_token'%service], Literal(access_token['oauth_token'])))
    graph.add((record[id], ss['%s_secret'%service], Literal(access_token['oauth_token_secret'])))

    SmartClient().put_rdf_store(graph)
    
