
from feedgen.feed import FeedGenerator
from feedgen.entry import FeedEntry
import requests
import json
import time
from collections import OrderedDict
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from urllib3.exceptions import MaxRetryError
from requests.exceptions import RetryError
import re
import pickle
import os

def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session



def json_save(obj, filename):
    f = open(filename, 'wt')
    f.write(json.dumps(obj))
    f.close()

def json_load(filename):
    f = open(filename, 'rt')
    j = json.loads(f.read())
    f.close()
    return j

def pickle_save(obj, filename):
    f = open(filename, 'wb')
    pickle.dump(obj, f)
    f.close()

def pickle_load(filename):
    f = open(filename, 'rb')
    obj = pickle.load(f)
    f.close()
    return obj


state_filename = '/data/topics.pickle'

def load_state():
    if os.path.isfile(state_filename):
        stored_topics = pickle_load(state_filename)
    else:
        stored_topics = OrderedDict()
    return stored_topics

def save_state(stored_topics):
    pickle_save(stored_topics, state_filename)


def update_topics(stored_topics):
    s = requests_retry_session()
    hot_topics = s.get('https://goodgame.ru/api/4/forum/').json()['hotTopics']
    
    def get_comments(topic_id):
        print('  fetching comments')
        r = s.get('https://goodgame.ru/api/4/comments?objId={}&objType=11&page={}'.format(topic_id, 1))
        comments = r.json()
        comments_len = comments['info']['qty']
        print('  total {} comments'.format(comments_len))
        last_page = 1 + comments_len // 25
        start_page = max(2, last_page - 4)
        for page in range(start_page, last_page+1):
            r = s.get('https://goodgame.ru/api/4/comments?objId={}&objType=11&page={}'.format(topic_id, page))
            for comment in r.json()['comments']:
                comments['comments'].append(comment)
        comments['comments'] = comments['comments'][-50:]
        return comments

    def update_topic_in_rss(topic, comments):
        print('saved #{}'.format(topic['id']))
        topic['comments'] = comments
        stored_topics[topic['id']] = topic

    updated_count = 0
    for i, topic in enumerate(reversed(hot_topics)):
        topic_id = topic['id']
        print('processing topic #{} ({}/{})'.format(topic_id, i+1,len(hot_topics)))
        comments = get_comments(topic_id)
        if len(comments['comments']):
            last_comment_time = float(comments['comments'][-1]['date'])
        else:
            last_comment_time = float(topic['utc_date'])
        if topic_id not in stored_topics or stored_topics[topic_id]['processed_time'] < last_comment_time:
            update_topic_in_rss(topic, comments)
            topic['processed_time'] = time.time()
            stored_topics[topic_id] = topic
            updated_count += 1
        else:
            print('  skipped')
    print('updated {} topics'.format(updated_count))
    return updated_count

def feed_header():
    fg = FeedGenerator()
    fg.id('https://goodgame.ru/forum/')
    fg.title('Goodgame forum')
    fg.description('forum')
    fg.author( {'name':'strayge','email':'strayge@gmail.com'} )
    fg.link( href='https://goodgame.ru/forum/', rel='alternate' )
    fg.language('ru')
    return fg

def cleanup_html(text):
    def quote_process(match):
        title = match.group(1)
        text = match.group(2)
        text = text.replace('<p>', '').replace('</p>', '\n')
        text = text.strip()
        return '<blockquote><i>{} писал:</i><br />{}</blockquote>'.format(title, text)

    def spoiler_process(match):
        title = match.group(1)
        text = match.group(2)
        text = text.replace('<p>', '').replace('</p>', '\n')
        text = text.strip()
        return '<blockquote><i>{}</i><br />{}</blockquote>'.format(title, text)

    text = text.replace('\r\n', '\n')
    text = text.replace('<br>', '\n').replace('<br />', '\n').replace('<br/>', '\n')
    text = text.replace('&nbsp;', ' ')
    
    text = text.replace('<p class="ng-scope">', '<p>')
    
    text = re.sub('<p>(&nbsp;|\s)*</p>', '\n', text, flags=re.IGNORECASE)
    
    text = text.replace('<br>&nbsp;<br>', '\n')
    text = re.sub('(&nbsp;|\s)*<p>', '<p>', text, flags=re.IGNORECASE)
    text = re.sub('<p>(&nbsp;|\s)*', '<p>', text, flags=re.IGNORECASE)
    text = re.sub('(&nbsp;|\s)*</p>', '</p>', text, flags=re.IGNORECASE)
    text = re.sub('</p>(&nbsp;|\s)*', '</p>', text, flags=re.IGNORECASE)
    #text = text.replace('</p>\n<p>', '</p><p>')
    
    while '  ' in text:
        text = text.replace('  ', ' ')
    while '\n\n' in text:
        text = text.replace('\n\n', '\n')

    text = re.sub('<a (class="bb" )?href="(/comment/\d+/|#\w+)"( target="\w+")?>(#\d+)</a>', 
                  '\\4', text, flags=re.IGNORECASE)

    text = re.sub(r'<img[^<>\n\r\t]*src="/images/smiles/(\w+)\.gif" />', 
                  ':\\1:', text, flags=re.IGNORECASE)
    text = re.sub(r'<img[^<>\n\r\t]*class="smiles? (\w+)(-big)?( [\w_-]+)?" src="[^<>"]+blank\.gif"[^<>\n\r\t]*/?>',
                  ':\\1:', text, flags=re.IGNORECASE)

    text = re.sub(r'<div class="[\w -]*quote[\w -]*"><div class="[\w -]*author[\w -]*">([^<>]+?)</div>([\s\S]+?)</div>',
                  quote_process, text, flags=re.IGNORECASE)
    
    text = re.sub(r'<div class="[\w -]*quote[\w -]*"[^<>\r\t\n]*>\s*<div>([\s\S]+?)</div>([\s\S]*?)</div>',
                  quote_process, text, flags=re.IGNORECASE)

    text = re.sub(r'<div gg-youtube="([\w_-]+)" data-info="{&quot;title&quot;:&quot;(.*?)&quot;,&quot;desc&[^<>]*?></div>',
                  '<a href="https://www.youtube.com/watch?v=\\1">\\2</a>', text, flags=re.IGNORECASE)

    text = re.sub(r'<div gg-youtube="[\w_-]+" gg-clip="(\d+)"[^<>]*?thumb&quot;:&quot;([^<>]+?)&quot;}">',
                  '<a href="https://goodgame.ru/clip/\\1"><img src="\\2"></img></a>', text, flags=re.IGNORECASE)
    
    text = re.sub(r'<gg-custom-spoiler[^<>]*?title="([^<>"]*?)"[^<>]*>([\s\S]*?)</gg-custom-spoiler>',
                  spoiler_process, text, flags=re.IGNORECASE)
    
    text = re.sub(r'<gg-spoiler[^<>]*?title="([^<>"]*?)"[^<>]*>([\s\S]*?)</gg-spoiler>',
                  spoiler_process, text, flags=re.IGNORECASE)
    
    text = text.strip()
    return text

def render_comment(comment):
    num = comment['i']
    if comment['deleted']:
        if 'deleted_by' in comment:
            text += 'Удалил {}'.format(comment['deleted_by'])
        else:
            return '' #  '{} Удалено'.format(num)
    author = comment['author']['nickname']
    text = comment['text']
    
    text = cleanup_html(text)
    
    rating = comment['rating']['up'] - comment['rating']['down']
    if rating > 0:
        rating_text = '+{}'.format(rating)
    else:
        rating_text = '{}'.format(rating)
    result = '<b>#{} {}</b>  [{}]\n{}'.format(num, author, rating_text, text)
    return result

def is_title_blacklisted(title):
    for word in ['заработка', 'продажа', 'продам', 'купить', 'розыгрыш', '$$$', 'деньги', 'магазин', \
                 'заработок', '지', '와', '클', '카', 'халява', 'халявные', 'биржа', 'раскрутка', \
                 'заработать', 'возможность выиграть', 'обмен аккаунтами', 'бесплатные игры', 'для cs:go', \
                 'танки онлайн', 'подарочные карты', 'с гарантией', 'продаю ключи', 'steam ключи', \
                 'поднимаемся на ставках', 'бесплатный кейс', 'в подарок', 'tankionline', 'халявные', \
                 '시', 'сервер ксго', 'бустану', 'через гарант', 'казино', 'продаю аккаунты', \
                 'поднять бабла', 'пассивному заработку', 'работа для всех']:
        if word in title.lower():
            return True
    return False

def generate_feed(stored_topics):
    fg = feed_header()
    
    for topic_id in stored_topics:
        topic = stored_topics[topic_id]

        
        if len(topic['comments']['comments']):
            last_comment_time = topic['comments']['comments'][-1]['date']
        else:
            last_comment_time = topic['utc_date']
        entry_id = '{}_{}'.format(topic['id'], last_comment_time)

        title = topic['title']

        if is_title_blacklisted(title):
            continue

        text = topic['text']

        text = cleanup_html(text)

        summary = text
        if len(summary) > 400:
            summary = summary[:390] + '...'
        
        text += '<p>Автор: <b>{}</b></p>'.format(topic['author'])

        for comment in topic['comments']['comments']:
            rendered = render_comment(comment)
            if rendered:
                text += '<p>{}</p>'.format(rendered)
        
        text = text.replace('\n', '<br />')
        url = topic['link']
        author = topic['author']

        entry = FeedEntry()

        entry.id(entry_id)
        entry.title(title)
        #entry.description(summary)
        entry.content(text)
        entry.link({'href': url})
        entry.author({'name': author})
        fg.add_entry(entry)
    return fg

if __name__ == '__main__':
    rss_filename = '/static/ggforum.rss'
    state = load_state()
    updated = update_topics(state)
    if updated or not os.path.isfile(rss_filename):
        feed = generate_feed(state)
        feed.rss_file(rss_filename, pretty=True)
        save_state(state)


