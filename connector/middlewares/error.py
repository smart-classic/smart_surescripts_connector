"""
Middleware (filters) for SMArt

inspired by django.contrib.auth middleware, but doing it differently
for tighter integration into email-centric users in Indivo (now SMArt).
"""

class Error(object):
  def process_exception(self, request, exception):
    print "PROCESSING EXCEPTION"
    import sys, traceback
    print >> sys.stderr, exception, dir(exception)
    traceback.print_exc(file=sys.stderr)
    
    sys.stderr.flush()
