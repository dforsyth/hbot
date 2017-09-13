import logging
import os

from bot.bot import Bot
from h import database
from bot.handler import MessageEventHandler
from handlers import (StocksCommandHandler, BangCommandHandler,
                      CommandsCommandHandler, CoinCommandHandler)

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]


class HBot(Bot):
    def __init__(self, username, token, icon, db):
        super(HBot, self).__init__(username, token, icon)
        self._db = db
        self._models = []

    @property
    def db(self):
        return self._db

    def on_start(self):
        self._db.connect()
        self._db.create_tables(self._models, safe=True)
        logging.info("Database prepared.")

    def register_model(self, model):
        self._models.append(model)


def main():
    logging.basicConfig(level=logging.DEBUG)

    bot = HBot(
        os.environ.get("H_BOT_NAME", "hbot"), SLACK_BOT_TOKEN,
        "http://i.imgur.com/gLeA41v.jpg", database)
    message_handler = MessageEventHandler()
    message_handler.register_command('!',
                                     StocksCommandHandler(
                                         "stocks", help="ticker quotes"))
    message_handler.register_command('!',
                                     BangCommandHandler(
                                         "bang", help="pulse check"))
    message_handler.register_command('!',
                                     CommandsCommandHandler(
                                         "help", message_handler, help="this"))
    message_handler.register_command('!', CoinCommandHandler("coin"))

    bot.register_event_handler('message', message_handler)

    bot.start()


if __name__ == '__main__':
    main()
