#!/usr/bin/env python3

# standard modules
from importlib import import_module, invalidate_caches
import json
import logging
import os
import sys
import time

# requirements
from lxml import etree
import requests
import yagmail

# html.tostring(tree)

page_probs_file = "page_problems_notified.json"


def check_pages(config):
    # We remember when a page went missing or had a structural change that caused a pattern to fail
    # We do this so that we don't end up spamming recipients 1440 times a day
    page_probs_known = {}
    if os.path.exists(page_probs_file):
        with open(page_probs_file, "r") as fh:
            page_probs_known = json.loads(fh.read())

    # Any new structural diff is separately saved, so we can add it to the JSON file
    page_probs_new = {}
    results = []

    # Visit all pages and xpath patterns
    for page in config.PAGES:
        resp = requests.get(page.url)
        if resp.status_code != 200:
            page_prob_key = "Warning: missing page, got HTTP {:d} for {:s}".format(resp.status_code, page.url)
            LOGGER.warning(page_prob_key)
            if page_prob_key not in page_probs_known:
                page_probs_new[page_prob_key] = time.strftime("%D %T")
                results.append(page_prob_key)
            continue

        # Convert response to lxml tree representation, so we can query it
        tree = etree.HTML(resp.content)
        for xpath, have_this_text in page.xpath_tests:
            LOGGER.debug(xpath)

            # Search for the subtree in the page
            res = tree.xpath(xpath)
            if not len(res):
                # If the pattern no longer yields a subtree, record that in the JSON and notify recipients
                page_prob_key = "Warning: page appears to be missing xpath:{:s}, url:{:s}".format(xpath, page.url)
                if page_prob_key not in page_probs_known:
                    page_probs_new[page_prob_key] = time.strftime("%D %T")
                    results.append(page_prob_key)
            else:
                # The subtree still exists, now check if the expected text is still there
                # We do this by turning all subtree text nodes into a single string, then checking it with the "in" op
                found_texts = [" ".join(t.strip() for t in r.itertext()) for r in res]
                for found_text in found_texts:
                    # An expected text is missing, let's notify recipients -- if it's the first time
                    if have_this_text.lower() not in found_text.lower():
                        page_prob_key = "ALERT: expected text not found: \"{:s}\", in: {:s}".format(
                            have_this_text, page.url)
                        if page_prob_key not in page_probs_known:
                            page_probs_new[page_prob_key] = time.strftime("%D %T")
                            results.append(page_prob_key)

    # If page structure changed, or expected text not found, remember that we notified user in this json log
    if page_probs_new:
        for key, ts in page_probs_new.items():
            page_probs_known[key] = ts
        with open(page_probs_file, "w") as fhw:
            fhw.write(json.dumps(page_probs_known))
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
            subject='ALERT: Elegoo Saturn Monitor page change (%d)' % len(results),
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
