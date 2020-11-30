# the future
from __future__ import annotations

# standard modules
from contextlib import ContextDecorator
import json
import logging
import os
import time
from typing import List


LOGGER = logging.getLogger(__name__)


PageInfo = namedtuple("PageInfo", ["url", "xpath_tests"])


class DeltaRule(object):
    def test(self, params: dict) -> bool:
        raise NotImplementedError("Method 'test' needs implementation in class {}".format(self.__class__.__name__))


RuleSet = List[DeltaRule]


class DeltaJournal(object):
    def put(self, key) -> DeltaJournal:
        raise NotImplementedError("Method 'test' needs implementation in class {}".format(self.__class__.__name__))
    def get(self, key) -> :


class HTMLDeltaJournal(ContextDecorator):
    # Any new structural diff is separately saved, so we can add it to the JSON file
    def __init__(self, journal_pathname, expire_deltas_mins, ruleset: RuleSet):
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

    def put(self, key) -> HTMLDeltaJournal:
        if key not in self._known_deltas and key not in self._new_deltas:
            self._new_deltas[key] = time.time()
            self._session_results.append(key)
            LOGGER.warning(key)
        return self

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


