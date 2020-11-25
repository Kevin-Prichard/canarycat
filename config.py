from collections import namedtuple

PageInfo = namedtuple("PageInfo", ["url", "xpath_tests"])

MONITOR_NAME = "name me"
SENDER_EMAIL = "your_email@gmail.com"
TARGET_EMAILS = ["..."]
GMAIL_PASSWORD = "change me"

PAGES = [
    PageInfo("https://surfshark.com/warrant-canary",
             [
                 ("//div[contains(@class, 'container-lgc')]", "0 National Security letters;"),
                 ("//div[contains(@class, 'container-lgc')]", "0 Gag orders;"),
                 ("//div[contains(@class, 'container-lgc')]", "0 Warrants from a government organization."),
             ]),
]
