from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.stations_on_map),
    url(r'^(?P<station_number>\d+)/$', views.station_on_map),
    url(r'^(?P<country>[a-zA-Z \-]+)/$', views.stations_on_map),
    url(r'^(?P<country>[a-zA-Z \-]+)/(?P<cluster>[a-zA-Z \-]+)/$', views.stations_on_map),
    url(r'^(?P<country>[a-zA-Z \-]+)/(?P<cluster>[a-zA-Z \-]+)/(?P<subcluster>[a-zA-Z \-]+)/$', views.stations_on_map),
]
