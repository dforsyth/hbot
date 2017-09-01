from collections import defaultdict
import logging

class EventHandler(object):
    def on_register(self, bot):
        pass

    def _on_register(self, bot):
        self.on_register(bot)

    def handle(self, obj, bot):
        pass

class MessageEventHandler(EventHandler):
    def __init__(self):
        self._msg_handlers = []
        self._cmd_handlers = defaultdict(dict)

    def register_command(self, prefix, command):
        self._cmd_handlers[prefix][command.name] = command

    def register_message_handler(self, handler):
        self._msg_handlers.append(handler)

    def handle(self, obj, bot):
        if 'type' not in obj or obj['type'] != 'message':
            return

        if 'text' not in obj:
            return

        dispatched = False
        msg_text = obj['text']
        for pfx, cmds in self._cmd_handlers.items():
            if msg_text.startswith(pfx):
                self._dispatch_command(obj, bot, cmds)
                dispatched = True

        if not dispatched:
            self._dispatch_message(obj, bot, self._msg_handlers)

    def _dispatch_command(self, obj, bot, handlers):
        tokens = obj['text'].split(' ')
        cmd = tokens[0][1:]
        handler = handlers.get(cmd)
        if handler:
            handler.handle(obj, bot)

    def _dispatch_message(self, obj, bot, handlers):
        for handler in handlers:
            handler.handle(obj, bot)

    def on_register(self, bot):
        for _, handlers in self._cmd_handlers.items():
            for _, handler in handlers.items():
                handler.on_register(bot)
        for handler in self._msg_handlers:
            handler.on_register(bot)

    @property
    def command_handlers(self):
        return self._cmd_handlers
