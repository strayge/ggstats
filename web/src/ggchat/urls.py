from django.conf.urls import url

from ggchat.views.simple import info
from ggchat.views.viewers import viewers_month, viewers_week, viewers_year

urlpatterns = [
    url(r'^$', viewers_week, name='week'),
    url(r'^month$', viewers_month, name='month'),
    url(r'^year$', viewers_year, name='year'),
    url(r'^info$', info, name='info'),
]
