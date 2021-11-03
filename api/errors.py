from flask import Flask


class LoggedError:
    app: Flask
    msg: str

    def __init__(self, app: Flask, msg: str):
        self.app = app
        self.msg = msg

    def __call__(self, *args, **kwargs):
        self.app.logger.error(self.msg.format(args))
