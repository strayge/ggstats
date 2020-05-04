from django.shortcuts import render_to_response
from django.views.decorators.cache import cache_page


@cache_page(30 * 60)
def index(request):
    return render_to_response('ggchat/index.html')
