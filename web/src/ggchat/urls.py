from django.conf.urls import url

from ggchat.views.channel import channel
from ggchat.views.chat_history import chathistory
from ggchat.views.chats import chats
from ggchat.views.moderators import moderators
from ggchat.views.money import money
from ggchat.views.search import search
from ggchat.views.simple import index, removed, stats, voice_player
from ggchat.views.user import user, user_by_name
from ggchat.views.users import users
from ggchat.views.viewers import viewers_month, viewers_week, viewers_year

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^stats$', stats, name='stats'),
    url(r'^viewers$', viewers_week, name='viewers_week'),
    url(r'^viewers_month$', viewers_month, name='viewers_month'),
    url(r'^viewers_year$', viewers_year, name='viewers_year'),
    url(r'^users$', users, name='users'),
    url(r'^chats', chats, name='chats'),
    url(r'^moderators', moderators, name='moderators'),
    url(r'^money$', money, name='money'),
    url(r'^user/(?P<user_id>\d+)$', user, name='user'),
    url(r'^user/(?P<username>[a-zA-Z0-9_]+)$', user_by_name, name='user_by_name'),
    url(r'^channel/(?P<channel_id>\w+)$', channel, name='channel'),
    url(r'^voice/(?P<url>[a-zA-Z0-9_\.\/:]+)$', voice_player, name='voice_player'),
    url(r'^chathistory/(?P<message_id>\d+)_(?P<hash>\w+)$', chathistory, name='chathistory'),
    url(r'^removed$', removed, name='removed'),
    url(r'^search/(?P<channel_id>r?\d+)/(?P<text>.+)$', search, name='search'),
]
