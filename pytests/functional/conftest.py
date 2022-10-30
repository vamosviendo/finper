import pytest
from pytest_django.live_server_helper import LiveServer

from pytests.functional.helpers import FinperFirefox


@pytest.fixture(autouse=True, scope='session')
def base_url(live_server: LiveServer) -> str:
    return live_server.url


# Pre sesion

@pytest.fixture(scope='session')
def browser(base_url: str) -> FinperFirefox:
    driver = FinperFirefox(base_url)
    yield driver
    driver.close()
