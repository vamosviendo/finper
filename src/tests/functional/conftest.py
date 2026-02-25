import os
from typing import Generator, Any

import pytest
from pytest_django.live_server_helper import LiveServer
from selenium.webdriver.firefox.options import Options

from tests.functional.helpers import FinperFirefox

@pytest.fixture(autouse=True, scope='session')
def base_url(live_server: LiveServer) -> str:
    if test_server := os.environ.get("TEST_SERVER"):
        return f"http://{test_server}"
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


def pytest_collection_modifyitems(items):
    for item in items:
        item.add_marker(pytest.mark.django_db(transaction=True))


@pytest.fixture(scope="session", autouse=True)
def django_db_setup(django_test_environment, django_db_blocker):
    if os.environ.get("TEST_SERVER"):
        with django_db_blocker.unblock():
            from django.conf import settings
            settings.DATABASES['default']['NAME'] = os.environ.get("DJANGO_DB_PATH", "container.db.sqlite3")
