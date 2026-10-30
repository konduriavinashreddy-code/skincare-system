def test_auth_register_me_and_profile(client):
    created = client.post("/api/auth/register", json={"full_name": "Ada Example", "email": "ada@example.com", "password": "a-secure-password"})
    assert created.status_code == 200
    token = created.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/auth/me", headers=headers).json()["data"]["email"] == "ada@example.com"
    assert client.get("/api/profile", headers=headers).status_code == 200
    result = client.put("/api/profile", headers=headers, json={"sensitivity": "very_sensitive", "allergies": "fragrance"})
    assert result.json()["data"]["sensitivity"] == "very_sensitive"

def test_password_policy_and_duplicate_email(client):
    payload = {"full_name": "Test User", "email": "same@example.com", "password": "short"}
    assert client.post("/api/auth/register", json=payload).status_code == 422
    payload["password"] = "long-enough-password"
    assert client.post("/api/auth/register", json=payload).status_code == 200
    assert client.post("/api/auth/register", json=payload).status_code == 409

def test_protected_endpoints_reject_anonymous_users(client):
    assert client.get("/api/skin/history").status_code == 401
    assert client.get("/api/products").status_code == 401

def test_products_can_be_searched_and_saved(client, account):
    products = client.get("/api/products", headers=account)
    assert products.status_code == 200
    item = products.json()["data"][0]
    assert item["is_demo"] is True
    assert "amazon.in/s?k=" in item["amazon_url"]
    assert client.post(f"/api/products/{item['id']}/save", headers=account).status_code == 200
    assert len(client.get("/api/products/saved", headers=account).json()["data"]) == 1