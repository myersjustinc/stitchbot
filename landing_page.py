#!/usr/bin/env python
from flask import Flask


app = Flask(__name__)


@app.route('/')
def home():
    return """
        <!doctype html>
        <html>
            <head>
                <title>Stitchbot landing page</title>
            </head>
            <body>
                <h1>Welcome to Stitchbot!</h1>
                <p>This doesn't really do anything world-facing.</p>
                <p>
                    For more information, or to set up your own Stitchbot, see
                    <a href="https://github.com/myersjustinc/stitchbot">its
                    GitHub project</a>.
                </p>
            </body>
        </html>
    """
    return 'Welcome to Stitchbot!'


if __name__ == '__main__':
    app.run()
