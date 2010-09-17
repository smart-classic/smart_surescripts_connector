from django.conf.urls.defaults import *

from views import *
from healthvault import healthvault_start_auth, healthvault_after_auth

urlpatterns = patterns('',
   # authentication
   (r'^smart/start_auth', indivo_start_auth),
   (r'^smart/after_auth', indivo_after_auth),

   (r'^google/start_auth', hospital_start_auth),
   (r'^google/after_auth', hospital_after_auth),
   (r'^google/meds', google_health_meds),


   (r'^healthvault/start_auth', healthvault_start_auth),
   (r'^healthvault/after_auth', healthvault_after_auth),

   # screens
   (r'^$', home),
   (r'^reset$', reset),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/(.*)', admin.site.root),

    # static
    ## WARNING NOT FOR PRODUCTION
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/web/indivo_hospital_connector/static'}),

)
