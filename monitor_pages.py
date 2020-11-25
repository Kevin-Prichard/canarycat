#!/usr/bin/env python3

# standard modules
from importlib import import_module, invalidate_caches
import logging
import os
import sys

# requirements
from lxml import etree
import requests
import yagmail


def check_pages(config):
    results = []
    for page in config.PAGES:
        resp = requests.get(page.url)
        if resp.status_code != 200:
            LOGGER.warning("Got HTTP {:d} for {:s}".format(resp.status_code, page.url))
            continue
        tree = etree.HTML(resp.content)
        for xpath, have_this_text in page.xpath_tests:
            LOGGER.debug(xpath)
            res = tree.xpath(xpath)
            if len(res):
                found_texts = [" ".join(t.strip() for t in r.itertext()) for r in res]
                for found_text in found_texts:
                    if have_this_text.lower() not in found_text.lower():
                        results.append(
                            "Page does not have expected text \"{:s}\", in: {:s}".format(have_this_text, page.url))
    return results


def email_it(results, config):
    # You might need to set up your gmail account for password-based sending-
    #     https://realpython.com/python-send-email/#option-1-setting-up-a-gmail-account-for-development
    yag = yagmail.SMTP(user=config.SENDER_EMAIL, password=config.GMAIL_PASSWORD)
    results_text = "\n\n".join(results) + "\n\n\n\nSincerely,\n\nelegoo.saturn.monitor"
    for target in config.TARGET_EMAILS:
        LOGGER.warning("Sending email to {:s}".format(target))
        yag.send(
            to=target,
            subject='Testing testing',
            contents=results_text)


if __name__ == '__main__':
    if len(sys.argv) < 2 or not os.path.exists(sys.argv[1] + ".py"):
        raise IOError("\n\nUsage:\n$ {} path/to/your/config.py".format(sys.argv[0]))
    invalidate_caches()
    config = import_module(sys.argv[1])
    LOGGER = logging.getLogger(config.MONITOR_NAME)

    results = check_pages(config)
    if results:
        email_it(results, config)
