from selenium import webdriver

from django.test import LiveServerTestCase


class FunctionalTest(LiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()
        self.browser.get(self.live_server_url)

    def tearDown(self) -> None:
        self.browser.quit()
