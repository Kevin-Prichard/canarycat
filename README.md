## Introduction

The script in this repo monitors certain pages for the disappearance of certain text

Periodically invoke this as a cron job and, upon detecting that an expected text snippet on a page & xpath deviates from an expected string, it will send a notification email.

Only when that occurs will it sends an email.


### Installation
Create and activate a virtual Python 3 environment. For example-
```shell script
$ python3 -m venv .venv
$ . .venv/bin/activate
$ pip install -r requirements.txt
```


### Email credentials
This script currently relies upon having a `Gmail app password` for a Gmail account.

This is not ideal, as it means the `Gmail app password` will at some point be in plaintext during program execution.

I am working on a better way of doing this, where the `Gmail app password` is only encrypted at rest, and temporarily held decrypted in memory. 

Therefore, you probably need to set up your gmail account for password-based access-
    https://support.google.com/accounts/answer/185833?hl=en

And you might need to enable this-
    https://realpython.com/python-send-email/#option-1-setting-up-a-gmail-account-for-development


### Execution
This script currently expects as first and only parameter the name of a config module, relative to the repo root. This is not very sophisticated,  but it works for now.

Ideally, run `cp config.py my_config.py` and make all further edits to `my_config.py`.

Execute this script, in shell or via cron, as-
```shell script
$ ./monitor_pages my_config
```

Once the script discovers a missing expected text, it sends an email about it to every address in TARGET_EMAILS.

### Nota bene
Make a PR if you fix something. While this project is in use, it has not been tested extensively. Just a casual project, so expect some breakage to occur. Do not rely on it for monitoring production systems! Use at your own risk.