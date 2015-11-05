# Stitchbot #

This is a little tool to help me regularly scrape the daily free cross-stitch
patterns from <http://dailycrossstitch.com/> and save them to a Google Drive
folder.

## Usage ##

Tested with Python 3.5. Probably works under Python 2.

*   Set up a new project in the [Google Developers Console][google-console],
    and enable the Drive API.

    (For more on what this is all about, check out [this intro][google-intro].)

    *   You'll also need to set up OAuth credentials as described
        [in the Developer Console documentation][oauth].

        Save these in the `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
        environment variables. (See "Configuration" below for more on that.)

*   Install with:

        git clone https://github.com/myersjustinc/stitchbot.git
        cd stitchbot
        pip install -r requirements.txt

*   Configure as described in "Configuration" below.

*   Run once with:

        ./stitchbot.py

[google-console]: https://console.developers.google.com/.
[google-intro]: https://developers.google.com/console/help/new/#managingprojects
[oauth]: https://support.google.com/cloud/answer/6158849?hl=en&ref_topic=6262490

## Configuration ##

You need an account on `dailycrossstitch.com` in order for this to work. Once
you have one, set the `STITCHBOT_USERNAME` and `STITCHBOT_PASSWORD` environment
variables to your username and password on that site, respectively.

You'll also need to keep track of `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
and `GOOGLE_REFRESH_TOKEN` environment variables for authentication to Google
Drive. To get those:

*   Create an application in [Google's developer console][google-console].

*   Set up [OAuth credentials][oauth] and make note of your client ID and
    client secret.

*   Enable the Drive API.

*   Run `get_google_token.py` with your client ID and client secret as
    environment variables, such as:

        GOOGLE_CLIENT_ID='long-string-of-gibberish' GOOGLE_CLIENT_SECRET='another-gibberish-string' ./get_google_token.py

    and follow its instructions.

    (TODO: Allow these things to be passed as proper command-line arguments in
    case that's easier for people.)

*   Make note of the refresh token it gives you.

*   Save the client ID, client secret and refresh token as the environment
    variables named above.

    I like to use [virtualenvs][virtualenv] for this, but do whatever you want.
    ([Heroku's config vars][heroku-config] work, too, if you're running this on
    that platform.)

[virtualenv]: https://virtualenv.pypa.io/en/latest/
[heroku-config]: https://devcenter.heroku.com/articles/config-vars

## Scheduling ##

TK
