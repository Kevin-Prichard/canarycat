#!/usr/bin/env python3

# standard modules
from contextlib import ContextDecorator
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


class DeltaJournal(ContextDecorator):
    # Any new structural diff is separately saved, so we can add it to the JSON file
    def __init__(self, journal_pathname, expire_deltas_mins):
        self._journal_pathname = journal_pathname
        self._expire_deltas_mins = expire_deltas_mins
        self._known_deltas = {}
        self._new_deltas = {}
        self._session_results = []
        self._fetch_known_deltas()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self._write_known_deltas()
        return False

    def put(self, key):
        if key not in self._known_deltas and key not in self._new_deltas:
            self._new_deltas[key] = time.time()
            self._session_results.append(key)
            LOGGER.warning(key)

    def results(self):
        return self._session_results

    def _fetch_known_deltas(self):
        if os.path.exists(self._journal_pathname):
            with open(self._journal_pathname, "r") as fh:
                self._known_deltas = json.loads(fh.read())
        self._prune_old_deltas()

    def _prune_old_deltas(self):
        new_map = {}
        now = time.time()
        for key, ts in self._known_deltas.items():
            # Preserve an entry if its timestamp + global expiry is still in the future
            if ts + self._expire_deltas_mins * 60 > now:
                new_map[key] = ts
        self._known_deltas = new_map

    def _write_known_deltas(self):
        # If page structure changed, or expected text not found, remember that we notified user in this json log
        if self._new_deltas:
            for key, ts in self._new_deltas.items():
                self._known_deltas[key] = ts
            with open(self._journal_pathname, "w") as fhw:
                fhw.write(json.dumps(self._known_deltas))


def check_pages(config):
    # We remember when a page went missing or had a structural change that caused a pattern to fail
    # We do this so that we don't end up spamming recipients 1440 times a day
    with DeltaJournal(page_probs_file, 12 * 60) as journal:

        # Visit all pages and xpath patterns
        for page in config.PAGES:
            resp = requests.get(page.url)
            if resp.status_code != 200:
                journal.put("Warning: missing page, got HTTP {:d} for {:s}".format(resp.status_code, page.url))
                continue

            # Convert response to lxml tree representation, so we can query it
            tree = etree.HTML(resp.content)
            for xpath, have_this_text in page.xpath_tests:
                LOGGER.debug(xpath)

                # Search for the subtree in the page
                res = tree.xpath(xpath)
                if not len(res):
                    # If the pattern no longer yields a subtree, record that in the JSON and notify recipients
                    journal.put("Warning: page appears to be missing xpath:{:s}, url:{:s}".format(xpath, page.url))
                else:
                    # The subtree still exists, now check if the expected text is still there
                    # We do this by turning all subtree text nodes into a single string, then checking it with the "in" op
                    found_texts = [" ".join(t.strip() for t in r.itertext()) for r in res]
                    for found_text in found_texts:
                        # An expected text is missing, let's notify recipients -- if it's the first time
                        if have_this_text.lower() not in found_text.lower():
                            journal.put("ALERT: expected text not found: \"{:s}\", in: {:s}".format(
                                have_this_text, page.url))

        return journal.results()


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
