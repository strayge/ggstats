from django.shortcuts import render_to_response
from django.utils import timezone
from django.views.decorators.cache import cache_page

from ggchat.models import *


@cache_page(30 * 60)
def money(request):
    week_ago = timezone.now() - datetime.timedelta(days=7)
    donates_data = Donation.objects.filter(timestamp__gte=week_ago).order_by('-timestamp').values('user_id', 'channel_id', 'amount', 'timestamp')

    grouped_by_date = {}
    for donate in donates_data:
        date = donate['timestamp'].date()
        grouped_by_date[date] = grouped_by_date.get(date, 0) + donate['amount']
    grouped_by_date_list = []
    for date, amount in grouped_by_date.items():
        grouped_by_date_list.append({'date': date, 'amount': int(amount)})

    chart_donate_total = {'data': grouped_by_date_list,
                          'x_keyword': 'date',
                          'y_keyword': 'amount',
                          'type': 'column',
                          'name': 'Донат',
                          'title': '',
                          'y_title': 'Рублей',
                          }

    grouped_by_channel = {}
    for donate in donates_data:
        channel_id = donate['channel_id']
        # skip donates to cups
        if channel_id is None:
            continue
        grouped_by_channel[channel_id] = grouped_by_channel.get(channel_id, 0) + donate['amount']
    grouped_by_channel_list = []
    for channel_id, amount in grouped_by_channel.items():
        channel = Channel.objects.filter(channel_id=channel_id).first()
        if channel and channel.streamer:
            streamer_name = channel.streamer.username
        else:
            streamer_name = ''
        grouped_by_channel_list.append({'channel_id': channel_id, 'amount': int(amount), 'username': streamer_name})
    grouped_by_channel_list.sort(key=lambda x: x['amount'], reverse=True)

    # common prems stats
    # latest_date = CommonPremiumPayments.objects.order_by('-date').first().date
    # current_month_prems = CommonPremiumPayments.objects.filter(date=latest_date).values('channel_id', 'channel__streamer__username', 'amount').order_by('-amount').all()
    # current_month_days = min(latest_date.day, 7)
    #
    # prev_month_days = 7 - current_month_days
    # prev_month_last_day = latest_date - datetime.timedelta(days=latest_date.day)
    # prev_month_day = CommonPremiumPayments.objects.filter(date__year=prev_month_last_day.year, date__month=prev_month_last_day.month).order_by('-date').first().date
    # prev_month_prems = CommonPremiumPayments.objects.filter(date=prev_month_day).values('channel_id', 'channel__streamer__username', 'amount').order_by('-amount').all()
    #
    # # union dicts
    # common_prems_dict = {}
    # for prem in current_month_prems:
    #     channel_id = prem['channel_id']
    #     # if channel_id == '5':
    #     #     print('cur', prem['amount'], latest_date.day, current_month_days, prem['amount'] / latest_date.day * current_month_days)
    #     prem['amount'] = prem['amount'] / latest_date.day * current_month_days
    #     common_prems_dict[channel_id] = prem
    #
    # if prev_month_days:
    #     for prem in prev_month_prems:
    #         channel_id = prem['channel_id']
    #         # if channel_id == '5':
    #         #     print('prev', prem['amount'], prev_month_day.day, prev_month_days, prem['amount'] / prev_month_day.day * prev_month_days)
    #         prem['amount'] = prem['amount'] / prev_month_day.day * prev_month_days
    #         if channel_id in common_prems_dict:
    #             # if channel_id == '5':
    #             #     print('exists', common_prems_dict[channel_id]['amount'], prem['amount'])
    #             common_prems_dict[channel_id]['amount'] += prem['amount']
    #         else:
    #             # if channel_id == '5':
    #             #     print('not exists', prem['amount'])
    #             common_prems_dict[channel_id] = prem
    #
    # # convert resulted dict to list
    # common_prems = list(common_prems_dict.values())
    # common_prems.sort(key=lambda x: x['amount'], reverse=True)

    # common_prems = CommonPremiumPayments.objects.filter(date__gte=week_ago).values('channel_id', 'channel__streamer__username').annotate(sum=Sum('amount')).order_by('-sum')[:20]
    # for i in range(len(common_prems)):
    #     common_prems[i]['sum'] /= 7

    content = {'chart_donate_total': chart_donate_total,
               'donate_top_per_channel': grouped_by_channel_list[:15],
               # 'common_prems': common_prems[:20],
               }

    return render_to_response('ggchat/money.html', content)
