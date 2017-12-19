"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^stats$', views.stats, name='stats'),
    url(r'^viewers$', views.viewers, name='viewers'),
    url(r'^viewers_month$', views.viewers_month, name='viewers_month'),
    url(r'^users$', views.users, name='users'),
    url(r'^chats', views.chats, name='chats'),
    url(r'^moderators', views.moderators, name='moderators'),
    url(r'^money$', views.money, name='money'),
    url(r'^user/(?P<user_id>\d+)$', views.user, name='user'),
    url(r'^user/(?P<username>[a-zA-Z0-9_]+)$', views.user_by_name, name='user_by_name'),
    url(r'^channel/(?P<channel_id>\w+)$', views.channel, name='channel'),
    url(r'^voice/(?P<url>[a-zA-Z0-9_\.\/:]+)$', views.voice_player, name='voice_player'),
    url(r'^chathistory/(?P<message_id>\d+)_(?P<hash>\w+)$', views.chathistory, name='chathistory'),
]
