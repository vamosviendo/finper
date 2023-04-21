import os
import pytest
from pytest_django.live_server_helper import LiveServer
from selenium.webdriver.firefox.options import Options

from pytests.functional.helpers import FinperFirefox


@pytest.fixture(autouse=True, scope='session')
def base_url(live_server: LiveServer) -> str:
    return live_server.url


# Pre sesion

@pytest.fixture(scope='session')
def browser(base_url: str) -> FinperFirefox:
    options = Options()
    options.headless = bool(os.getenv('DOCKERIZED'))  # Usar modo headless si se ejecuta en docker
    driver = FinperFirefox(base_url, options=options)
    yield driver
    driver.close()
