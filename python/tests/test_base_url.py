"""
The API host comes from REPUWAVE_API_URL when the caller does not pass one.

Every constructor defaulted to the planned public host, which does not answer
yet, so code that followed the README failed on its first call.
"""

from repuwave_sdk import RepuwaveClient, RepuwaveService, generate_keypair
from repuwave_sdk._config import FALLBACK_BASE_URL


def _key():
    return generate_keypair()[0]


def test_the_environment_variable_is_used(monkeypatch):
    monkeypatch.setenv("REPUWAVE_API_URL", "http://repuwave.test/v1")
    assert str(RepuwaveService(api_key="k")._client.base_url) == "http://repuwave.test/v1/"
    assert str(RepuwaveClient(private_key=_key(), uaid="u")._client.base_url) == "http://repuwave.test/v1/"


def test_an_explicit_base_url_wins(monkeypatch):
    monkeypatch.setenv("REPUWAVE_API_URL", "http://repuwave.test/v1")
    service = RepuwaveService(api_key="k", base_url="http://other.test/v1")
    assert str(service._client.base_url) == "http://other.test/v1/"


def test_without_either_the_planned_host_is_the_fallback(monkeypatch):
    monkeypatch.delenv("REPUWAVE_API_URL", raising=False)
    assert str(RepuwaveService(api_key="k")._client.base_url).rstrip("/") == FALLBACK_BASE_URL
