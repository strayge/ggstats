from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import loader

from ggchat.models import Donation, ChannelStats


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


def chart(request):
    all_needed_data = ChannelStats.objects.filter(channel_id='5').values('timestamp', 'users').all()
    chart1 = {'data': all_needed_data,
              'x_keyword': 'timestamp',
              'y_keyword': 'users',
              'zoom': True,
              'title': 'Зрители',
              'y_title': 'Количество',
              'series_name': 'Зрителей',
              'type': 'area'}
    return render_to_response('ggchat/chart.html', {'chart1': chart1})
