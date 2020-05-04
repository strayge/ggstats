from django.conf.urls import url

from ggchat.views.simple import index
from ggchat.views.viewers import viewers_month, viewers_week, viewers_year

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^viewers$', viewers_week, name='viewers_week'),
    url(r'^viewers_month$', viewers_month, name='viewers_month'),
    url(r'^viewers_year$', viewers_year, name='viewers_year'),
]
