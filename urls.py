from django.conf.urls.defaults import *

urlpatterns = patterns('',
   # authentication
   (r'^', include('connector.urls')),
)
