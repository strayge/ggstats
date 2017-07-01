from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader

from ggchat.models import Donation


def index(request):
    latest_payments = Donation.objects.order_by('-timestamp')[:5]
    template = loader.get_template('ggchat/index.html')
    context = {'latest_payments': latest_payments}
    return HttpResponse(template.render(context, request))


def stats(request):
    output = 'stats: <br /> latest donation: <br />'
    latest_donation = Donation.objects.order_by('-timestamp').first()
    if latest_donation:
        output += str(latest_donation)
    return HttpResponse(output)
