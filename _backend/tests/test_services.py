import pytest
from app.seed import DEMO_PRODUCTS
from app.security import hash_password, verify_password
from app.services.analysis import analyze_image
from app.services.recommendations import marketplace_links

def test_password_hash_is_salted_and_verifiable():
    first = hash_password("correct horse battery")
    second = hash_password("correct horse battery")
    assert first != second
    assert verify_password("correct horse battery", first)
    assert not verify_password("wrong password", first)

def test_mock_output_is_explicitly_simulated(monkeypatch):
    monkeypatch.setenv("AI_MODE", "mock")
    result = analyze_image(b"demo image bytes")
    assert result["model_mode"] == "mock"
    assert result["skin_type_estimate"] == "unable_to_determine"
    assert "Simulated" in result["disclaimer"]
    assert {"redness", "dryness", "dark_spots"}.issubset(result["observations"])

def test_model_mode_does_not_fall_back_to_mock(monkeypatch):
    monkeypatch.setenv("AI_MODE", "model")
    monkeypatch.setenv("ML_SERVICE_URL", "http://127.0.0.1:1")
    with pytest.raises(RuntimeError):
        analyze_image(b"demo image bytes")

def test_unconfigured_marketplace_links_are_product_searches():
    from types import SimpleNamespace
    product = SimpleNamespace(brand="Demo Brand", name="Gentle Cleanser", amazon_url=None, flipkart_url=None)
    links = marketplace_links(product)
    assert links["amazon_url"].startswith("https://www.amazon.in/s?k=")
    assert links["flipkart_url"].startswith("https://www.flipkart.com/search?q=")

def test_seed_catalog_is_labeled_demo():
    assert all("Demo" in item["name"] for item in DEMO_PRODUCTS)