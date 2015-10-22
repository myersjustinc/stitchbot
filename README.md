# Stitchbot #

This is a little tool to help me regularly scrape the daily free cross-stitch
patterns from <http://dailycrossstitch.com/>.

## Usage ##

Tested with Python 3.5. Probably works under Python 2.

*   Install with:

        git clone https://github.com/myersjustinc/stitchbot.git
        cd stitchbot
        pip install -r requirements.txt

*   Configure as described in "Configuration" below.

*   Run once with:

        ./stitchbot.py

## Configuration ##

You need an account on `dailycrossstitch.com` in order for this to work. Once
you have one, set the `STITCHBOT_USERNAME` and `STITCHBOT_PASSWORD` environment
variables to your username and password on that site, respectively.

I like to use [virtualenvs](https://virtualenv.pypa.io/en/latest/) for this,
but do whatever you want.

## Scheduling ##

TK
