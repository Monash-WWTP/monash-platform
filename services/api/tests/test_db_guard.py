import pytest

from conftest import validate_test_database_url


SAFE = "postgresql+psycopg://monash_test:monash_test@127.0.0.1:5433/monash_test"


def test_guard_accepts_only_the_disposable_connection():
    validate_test_database_url(SAFE, SAFE)


@pytest.mark.parametrize("url", [
    SAFE + "?host=another-host&dbname=production",
    SAFE + "?service=production",
    "postgresql+psycopg://monash_test:monash_test@127.0.0.1:5432/monash_test",
    "postgresql+psycopg://other:secret@127.0.0.1:5433/monash_test",
])
def test_guard_rejects_alternate_connection_targets(url):
    with pytest.raises(AssertionError):
        validate_test_database_url(url, url)
