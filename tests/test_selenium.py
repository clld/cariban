import time


def est_ui(selenium):
    selenium.browser.get(selenium.url('/'))
    time.sleep(3)
