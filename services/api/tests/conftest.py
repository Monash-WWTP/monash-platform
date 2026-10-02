import os
import pytest

DISPOSABLE_URL = "postgresql+psycopg://monash_test:monash_test@127.0.0.1:5433/monash_test"


@pytest.fixture(scope="session", autouse=True)
def ensure_disposable_database():
    test_url = os.environ.get("TEST_DATABASE_URL")
    validate_test_database_url(test_url, os.environ.get("DATABASE_URL"))


def validate_test_database_url(test_url: str | None, database_url: str | None):
    assert test_url == DISPOSABLE_URL, "TEST_DATABASE_URL must be the disposable local database"
    assert database_url == test_url
