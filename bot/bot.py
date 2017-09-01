from collections import defaultdict
import json
import logging
import time

from slackclient import SlackClient


class Bot(object):
    def __init__(self, username, token, icon):
        self._username = username
        self._token = token
        self._icon = icon

        self._event_handlers = defaultdict(list)

        self._slack = SlackClient(token)

    def _connect(self):
        logging.info("Connecting...")
        if not self._slack.rtm_connect():
            raise Exception("Failed to connect to Slack.")

        resp = self._slack_api_call("api.test")
        if not response_ok(resp):
            raise Exception("API test failed.")

    def on_start(self):
        pass

    def start(self):
        logging.info("Starting bot...")
        self.on_start()

        self._connect()

        logging.info("Running loop...")
        while True:
            event_dict = self.recv_events()
            for typ, events in event_dict.items():
                if typ in self._event_handlers:
                    handlers = self._event_handlers[typ]
                    for handler in handlers:
                        for ev in events:
                            handler.handle(ev, self)

            time.sleep(.1)

    def _slack_api_call(self, m, **kwargs):
        response = self._slack.api_call(m, **kwargs)
        if not response_ok(response):
            logging.warning("Slack API error: " + json.dumps(response))
        return response

    def recv_events(self):
        events = self._slack.rtm_read()
        event_dict = defaultdict(list)
        for ev in events:
            if "type" not in ev:
                logging.info("Event with unknown type " + json.dumps(ev))
                continue
            event_dict[ev["type"]].append(ev)
        return event_dict

    def send_message(self, channel, message, attachments=None):
        resp = self._slack_api_call(
            "chat.postMessage",
            text=message,
            channel=channel,
            username=self._username,
            icon_url=self._icon,
            attachments=attachments)
        if not response_ok(resp):
            logging.warning("Failed to send message: " + json.dumps(resp))

    def register_event_handler(self, typ, handler):
        self._event_handlers[typ].append(handler)
        handler.on_register(self)


def response_ok(response):
    return response and 'ok' in response and response['ok']
