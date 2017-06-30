from django.http import HttpResponse
from django.shortcuts import render

from ggchat.models import Donation


def index(request):
    output = 'index.html'
    return HttpResponse(output)


def stats(request):
    output = 'stats: <br /> latest donation: <br />'
    latest_donation = Donation.objects.order_by('-timestamp').first()
    if latest_donation:
        output += str(latest_donation)
    return HttpResponse(output)