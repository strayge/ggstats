import calendar
import datetime
from django import template
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import mark_safe
import json

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
    # data = chart_data.get('data', [])
    zoom = bool(chart_data.get('zoom', False))
    legend = bool(chart_data.get('legend', False))
    # x_keyword = conditional_escape(chart_data.get('x_keyword'))
    # y_keyword = conditional_escape(chart_data.get('y_keyword'))
    # chart_type = conditional_escape(chart_data.get('type', 'line'))
    title = conditional_escape(chart_data.get('title', ''))
    x_title = conditional_escape(chart_data.get('x_title', ''))
    y_title = conditional_escape(chart_data.get('y_title', ''))
    # name = conditional_escape(chart_data.get('name', ''))
    x_type = conditional_escape(chart_data.get('x_type', 'datetime'))
    tooltips = {}

    all_js_series = ''
    for i in range(1, 10):
        if i == 1:
            i = ''
        if f'data{i}' in chart_data and f'x_keyword{i}' in chart_data and f'y_keyword{i}' in chart_data:
            data = chart_data.get(f'data{i}', [])
            x_keyword = conditional_escape(chart_data.get(f'x_keyword{i}'))
            y_keyword = conditional_escape(chart_data.get(f'y_keyword{i}'))
            chart_type = conditional_escape(chart_data.get(f'type{i}', 'line'))
            name = conditional_escape(chart_data.get(f'name{i}', ''))
            visible = bool(chart_data.get(f'visible{i}', True))
            color = conditional_escape(chart_data.get(f'color{i}', ''))
            tooltip = chart_data.get(f'tooltips{i}', {})
            tooltips[name] = tooltip

            js_data = ''
            for row in data:
                if type(row[x_keyword]) is datetime.datetime:
                    x = row[x_keyword].timestamp() * 1000
                elif type(row[x_keyword]) is datetime.date:
                    date = row[x_keyword]
                    x = calendar.timegm(date.timetuple()) * 1000
                else:
                    x = row[x_keyword]
                y = row[y_keyword]
                js_data += format_html('[{}, {}],', x, y)
            js_data = '[' + js_data + ']'

            js_series = "type: '%s'," % chart_type
            js_series += "data: %s," % js_data
            if name:
                js_series += "name: '%s'," % name

            # true by default
            if visible == False:
                js_series += "visible: false,"

            if color:
                js_series += "color: '%s'," % color

            js_series = '{' + js_series + '},'
            all_js_series += js_series

    js_chart = "zoomType: 'x'" if zoom else ''
    js_xaxis = f"type: '{x_type}',title: {{text: '{x_title}'}}" if x_title else f"type: '{x_type}',"
    js_yaxis = f"title: {{text: '{y_title}'}}" if y_title else ''
    js_title = f"text: '{title}'" if title else "text: '', style: {display: 'none'}"
    js_legend = "enabled: true" if legend else  "enabled: false"

    # text += '<span style="color:' + this.series.color + '">' + this.series.name + '</span>: <b>' + this.y + '</b><br/>';
    js_tooltip = '''
    formatter: function(tooltip) {
        elements = tooltip.defaultFormatter.call(this, tooltip);
        if (tooltips[this.series.name] && tooltips[this.series.name][this.x]) {
            elements.push(tooltips[this.series.name][this.x]);
        };
        return elements;
    }
    '''
    js = f'''
    <script>
    tooltips = {json.dumps(tooltips)};
    Highcharts.chart(
        "{container}",
        {{
            chart:{{{js_chart}}},
            xAxis:{{{js_xaxis}}},
            yAxis:{{{js_yaxis}}},
            series:[{all_js_series}],
            title:{{{js_title}}},
            legend:{{{js_legend}}},
            tooltip:{{{js_tooltip}}}
        }}
    );
    </script>
    '''
    return mark_safe(js)
