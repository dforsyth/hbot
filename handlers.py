import datetime
from decimal import Decimal
import json
import logging

from yahoo_finance import Share
from peewee import CharField, DateTimeField, ForeignKeyField
import requests
import gdax

from bot.handler import EventHandler, MessageEventHandler


class CommandEventHandler(EventHandler):
    def __init__(self, name, help=""):
        self._name = name
        self._help = help

    def handle(self, obj, bot):
        # don't let other bots give us orders.
        if obj.get("subtype") == "bot_message":
            return

        text = obj["text"]
        tokens = text.split(" ")
        user = obj["user"]
        channel = obj["channel"]

        self.handle_cmd(tokens[0], tokens[1:], user, channel, bot)

    def handle_cmd(self, command, arguments, user, channel, bot):
        pass

    @property
    def name(self):
        return self._name

    @property
    def help(self):
        return self._help


class StocksCommandHandler(CommandEventHandler):
    def handle_cmd(self, command, arguments, user, channel, bot):
        if len(arguments) == 0:
            return

        output = ""
        for arg in arguments:
            if len(output) > 0:
                output += "\n"
            output += self._fetch_and_output(arg)

        bot.send_message(channel, output)

    def _fetch_and_output(self, symbol):
        sym = symbol.upper()
        try:
            share = Share(sym)
        except Exception as e:
            logging.warning("StocksCommandHandler: " + str(e))
            return sym + ": Something went wrong: " + str(e)

        if share is None or share.get_price() is None:
            return "Can't find info for '" + sym + "'"

        return (sym + " - " + share.get_name() + ": " + share.get_price() +
                " (" + share.get_change() + ")")


class BangCommandHandler(CommandEventHandler):
    def __init__(self, name, help=""):
        super(BangCommandHandler, self).__init__(name, help=help)

    def handle_cmd(self, command, arguments, user, channel, bot):
        bot.send_message(channel, "bang bang")


class CommandsCommandHandler(CommandEventHandler):
    def __init__(self, name, message_event_handler, help=""):
        super(CommandsCommandHandler, self).__init__(name, help=help)
        if type(message_event_handler) != MessageEventHandler:
            raise Exception(
                "message_event_handler must be MessageEventHandler")
        self._message_event_handler = message_event_handler

    def handle_cmd(self, command, arguments, user, channel, bot):
        prefix = command[0]
        commands = self._message_event_handler.command_handlers[prefix]
        output = ""
        for _, command in commands.items():
            output += prefix + command.name + ": " + command.help + "\n"
        bot.send_message(channel, output)


class CoinCommandHandler(CommandEventHandler):
    def __init__(self, name):
        super(CoinCommandHandler, self).__init__(
            name, help="Show currency prices (from GDAX)")
        self.client = gdax.PublicClient()

    def handle_cmd(self, command, arguments, user, channel, bot):
        output = ""
        if not arguments or 'supported' in arguments:
            try:
                r = self.client.get_products()
                output += "Supported currencies:\n"
                for c in r:
                    output += c["id"] + "\n"
            except Exception as e:
                output += "Error: " + str(e) + "\n"
                logging.warning("CoinCommandHandler: " + str(e))
        else:
            for arg in arguments:
                try:
                    currency = arg.upper()
                    r = self.client.get_product_ticker(product_id=currency)
                    if "message" in r and r["message"] == "Not Found":
                        output += currency + ": Not Found.\n"
                    else:
                        output += (
                            currency + ": " +
                            str(Decimal(r["price"]).quantize(Decimal("1.00")))
                            + "\n")
                except Exception as e:
                    output += currency + ": Error (" + str(e) + ")\n"
                    logging.warning("CoinCommadHandler: " + str(e))

        bot.send_message(channel, output)
