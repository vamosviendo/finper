import os
from typing import Generator, Any

import pytest
from pytest_django.live_server_helper import LiveServer
from selenium.webdriver.firefox.options import Options

from tests.functional.helpers import FinperFirefox

@pytest.fixture(autouse=True, scope='session')
def base_url(live_server: LiveServer) -> str:
    return live_server.url


# Pre sesion

@pytest.fixture(scope='session')
def browser(base_url: str) -> Generator[FinperFirefox, Any, None]:
    options = Options()
    if bool(os.getenv("DOCKERIZED")) is True:
        options.add_argument("--headless")
    driver = FinperFirefox(base_url, options=options)
    yield driver
    driver.close()
