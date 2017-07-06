from django import template
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag()
def chart_load_js():
    jquery_path = 'https://cdnjs.cloudflare.com/ajax/libs/jquery/1.7.2/jquery.min.js'
    highcharts_path = 'https://cdnjs.cloudflare.com/ajax/libs/highcharts/5.0.12/highcharts.js'
    out = ''
    out += '<script src="{}" type="text/javascript"></script>\n'.format(jquery_path)
    out += '<script src="{}" type="text/javascript"></script>\n'.format(highcharts_path)

    highcharts_set_lang = '''
    Highcharts.setOptions({
            lang: {
                loading: 'Загрузка...',
                months: ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'],
                weekdays: ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота'],
                shortWeekdays: ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'],
                shortMonths: ['Янв', 'Фев', 'Март', 'Апр', 'Май', 'Июнь', 'Июль', 'Авг', 'Сент', 'Окт', 'Нояб', 'Дек'],
                downloadPNG: 'Скачать PNG',
                downloadJPEG: 'Скачать JPEG',
                downloadPDF: 'Скачать PDF',
                downloadSVG: 'Скачать SVG',
                printChart: 'Напечатать график',
                resetZoom: "Весь график",
                resetZoomTitle: "Сбросить увеличение до 1:1",
                noData: "Нет данных для отображения",
                drillUpText: "Назад к {series.name}",
            }
    });
    '''

    out += '<script>%s</script>\n' % highcharts_set_lang

    return mark_safe(out)

@register.simple_tag()
def chart_datetime(container, chart_data):
    data = chart_data.get('data', [])
    zoom = bool(chart_data.get('zoom', False))
    legend = bool(chart_data.get('legend', False))
    x_keyword = conditional_escape(chart_data.get('x_keyword'))
    y_keyword = conditional_escape(chart_data.get('y_keyword'))
    chart_type = conditional_escape(chart_data.get('type', 'line'))
    title = conditional_escape(chart_data.get('title', ''))
    x_title = conditional_escape(chart_data.get('x_title', ''))
    y_title = conditional_escape(chart_data.get('y_title', ''))
    series_name = conditional_escape(chart_data.get('series_name', ''))

    js_data = ''
    for row in data:
        x = row[x_keyword].timestamp() * 1000
        y = row[y_keyword]
        js_data += format_html('[{}, {}],', x, y)
    js_data = '[' + js_data + ']'

    js_series = "type: '%s'," % chart_type
    js_series += "data: %s," % js_data
    if series_name:
        js_series += "name: '%s'," % series_name

    js_chart = ''
    if zoom:
        js_chart = "zoomType: 'x'"

    js_xaxis = "type: 'datetime',"
    if x_title:
        js_xaxis += "title: {text: '%s'}" % x_title

    js_yaxis = ''
    if y_title:
        js_yaxis = "title: {text: '%s'}" % y_title

    js_title = ''
    if title:
        js_title = "text: '%s'" % title

    js_legend = "enabled: false"
    if legend:
        js_legend = "enabled: true"

    js = '<script>Highcharts.chart("%s",{chart:{%s},xAxis:{%s},yAxis:{%s},series:[{%s}],title:{%s},legend:{%s}});</script>' % \
         (container, js_chart, js_xaxis,  js_yaxis, js_series, js_title, js_legend)

    return mark_safe(js)

'''
    all_needed_data = ChannelStats.objects.filter(channel_id='5').values('timestamp', 'users').all()
    data = ''
    for row in all_needed_data:
        x = row['timestamp'].timestamp() * 1000
        y = row['users']
        data += '[%s, %s],' % (x, y)
    data = '[' + data + ']'
    return render_to_response('ggchat/chart.html', {'data': data})

<script>
    Highcharts.chart('container', {
        chart: {
            zoomType: 'x'
        },
        xAxis: {
            type: 'datetime',
            title: {
                text: 'xAxis title'
            }
        },
        series: [{
            type: 'line',
            data: {{ data }},
            name: 'series1 name'
        }],
        title: {
            text: 'Main title'
        },
        yAxis: {
            title: {
                text: 'yAxis title'
            }
        },
        legend: {
            enabled: false
        },
    });
</script>
'''