"""
RDF Parsing utils for SMArt meds / fills
Josh Mandel
joshua.mandel@childrens.harvard.edu
"""

from xml.dom.minidom import parse, parseString
import urllib
import libxml2, libxslt
import RDF
import datetime
import time
from smart_client.rdf_utils import *

def get_medication_uris(g):
    qs = RDF.Statement(subject=None, 
                       predicate=NS['rdf']['type'], 
                       object=NS['sp']['medication'])
    
    ret = []
    for s in g.find_statements(qs):
        ret.append(s.subject)
        
    return ret

def get_medication_model(g,med_uri):
    properties = [NS['dcterms']['title'], 
                  NS['med']['drug'],
                  NS['med']['strength'],
                  NS['med']['strengthUnit'],
                  NS['med']['dose'],
                  NS['med']['doseUnit'],
                  NS['med']['startDate'],
                  NS['med']['endDate'],
                  NS['rdf']['type']]
    
    one_med = RDF.Model()

    for p in properties:
        one_med.add_statements(get_property(g, med_uri, p))
            
    return one_med
             
def get_fill_uris(g, med_uri):
    parent_statement = RDF.Statement(subject=med_uri, 
                       predicate=NS['sp']['fulfillment'], 
                       object=None)
    
    ret = []
    for s in g.find_statements(parent_statement):
        ret.append(s.object)
    return ret

def get_fill_model(g,fill_uri):
    properties = [NS['sp']['pharmacy'],
                  NS['sp']['prescriber'],
                  NS['sp']['dispenseQuantity'],
                  NS['sp']['PBM'],
                  NS['dc']['date'],
                  NS['rdf']['type']]
    
    one_fill = RDF.Model()

    for p in properties:
        one_fill.add_statements(get_property(g, fill_uri, p))
            
    return one_fill

def med_external_id(g, med_uri):
    qs =  RDF.Statement(subject=med_uri, 
                       predicate=NS['med']['drug'], 
                       object=None)
    
    ret = None
    for s in g.find_statements(qs):
        return str(s.object.uri).split('/')[-1]
    
def fill_external_id(g, fill_uri):
    qs =  RDF.Statement(subject=fill_uri, 
                       predicate=NS['dc']['date'], 
                       object=None)
    
    ret = None
    for s in g.find_statements(qs):
        t = time.mktime(datetime.datetime.strptime(s.object.literal_value['string'], 
                                                   "%Y-%m-%dT%H:%M:%SZ").timetuple())
        return str(int(t))

