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

    If you want to save your patterns to a local directory as well as to Google
    Drive, just add the path to that directory as an argument:

        ./stitchbot.py my_patterns

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
    environment variables, with the Google Drive API scope
    `https://www.googleapis.com/auth/drive.file` as an argument at the end,
    such as:

        GOOGLE_CLIENT_ID='long-string-of-gibberish' GOOGLE_CLIENT_SECRET='another-gibberish-string' ./get_google_token.py https://www.googleapis.com/auth/drive.file

    and follow its instructions.

    (TODO: Allow more of these things to be passed as proper command-line
    arguments in case that's easier for people.)

*   Make note of the refresh token it gives you.

*   Save the client ID, client secret and refresh token as the environment
    variables named above.

    I like to use [virtualenvs][virtualenv] for this, but do whatever you want.
    ([Heroku's config vars][heroku-config] work, too, if you're running this on
    that platform.)

[virtualenv]: https://virtualenv.pypa.io/en/latest/
[heroku-config]: https://devcenter.heroku.com/articles/config-vars

## Scheduling ##

You just have to run `./stitchbot.py` once for each day on which you want to
download the free pattern. [cron][cron] is handy for this, but I designed it
for use with [Heroku Scheduler][scheduler].

Because of that, there's a little [Flask][flask] app in here that'll work just
fine on Heroku. (It basically just says hi and points visitors to this repo.)

Here's how to do that:

*   **Push Stitchbot to Heroku**

    Basically, just follow the first few steps of
    [this Heroku tutorial][heroku-python].

    In "Prepare the app", clone this repo
    (`https://github.com/myersjustinc/stitchbot.git`) instead of the one they
    tell you to.

    After "Deploy the app", you can stop and keep following this README
    instead.

*   **Set config vars**

    In our case, that'll mean running:

        heroku config:set STITCHBOT_USERNAME='your_daily_cross_stitch_username' STITCHBOT_PASSWORD='your_daily_cross_stitch_password' GOOGLE_CLIENT_ID='your_client_id' GOOGLE_CLIENT_SECRET='your_client_secret' GOOGLE_REFRESH_TOKEN='your_refresh_token'

    See the "Configuration" section above for more on obtaining those.

*   **Schedule Stitchbot to run**

    *   Add Scheduler to your app:

            heroku addons:create scheduler:standard

    *   Open the Scheduler dashboard:

            heroku addons:open scheduler

    *   Add a new job that runs daily (pick your favorite time). It should run
        `./stitchbot.py`.

    *   Sit back and collect patterns!

[cron]: https://en.wikipedia.org/wiki/Cron
[scheduler]: https://devcenter.heroku.com/articles/scheduler
[flask]: http://flask.pocoo.org/
[heroku-python]: https://devcenter.heroku.com/articles/getting-started-with-python
