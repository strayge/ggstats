from django.conf.urls import url

from ggchat.views.simple import info
from ggchat.views.user import user, user_by_name
from ggchat.views.viewers import viewers_month, viewers_week, viewers_year

urlpatterns = [
    url(r'^$', viewers_week, name='week'),
    url(r'^month$', viewers_month, name='month'),
    url(r'^year$', viewers_year, name='year'),
    url(r'^info$', info, name='info'),
    url(r'^user/(?P<user_id>\d+)$', user, name='user'),
    url(r'^user/(?P<username>[a-zA-Z0-9_.-]+)$', user_by_name, name='user_by_name'),
]
