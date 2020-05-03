import logging
import logging.handlers
import multiprocessing
from multiprocessing import Queue, Process

from django.core.management import BaseCommand

from ggchat.management.commands._ws_client import ChatWsClient
from ggchat.management.commands._msg_parser import ChatMsgParser
from ggchat.management.commands._common import setup_logger


class Command(BaseCommand):
    help = 'keep connection for chat and fetch data to db'

    def handle(self, *args, **options):
        log_level = logging.INFO
        log = setup_logger(log_level)
        queue_msg_parse = Queue()
        try:
            kwargs = {
                'log_level': log_level,
                'queue_msg_parse': queue_msg_parse,
            }
            Process(target=ChatWsClient, kwargs=kwargs, name='ws').start()

            kwargs = {
                'log_level': log_level,
                'queue_msg_parse': queue_msg_parse,
            }
            multiprocessing.current_process().name = 'parser'
            ChatMsgParser(**kwargs)  # blocking call
        except KeyboardInterrupt:
            log.warning('fetcher2 interrupted')


if __name__ == '__main__':
    Command().handle()
