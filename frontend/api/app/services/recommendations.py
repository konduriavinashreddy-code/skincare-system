from urllib.parse import quote_plus

def marketplace_links(product) -> dict:
    query = quote_plus(f"{product.brand} {product.name}")
    return {"amazon_url": product.amazon_url or f"https://www.amazon.in/s?k={query}",
            "flipkart_url": product.flipkart_url or f"https://www.flipkart.com/search?q={query}"}

def rank_product(product, skin_type: str, observations: dict, profile) -> dict:
    matched = [name for name, value in observations.items() if value.get("score", 0) >= 0.4 and name in product.concerns]
    skin_match = skin_type in product.skin_types or "all" in product.skin_types
    allergy_terms = {term.strip().lower() for term in (profile.allergies or "").split(",") if term.strip()}
    conflict = any(any(term in ingredient.lower() for term in allergy_terms) for ingredient in product.ingredients)
    ceiling = {"budget": 500, "moderate": 1500, "premium": 10000}.get(profile.budget, 1500)
    sensitivity_match = profile.sensitivity == "not_sensitive" or product.suitable_for_sensitive_skin
    prefs = [p for p in profile.preferences if p in {"fragrance_free", "vegan", "cruelty_free"}]
    preference_match = not prefs or all(getattr(product, preference, False) for preference in prefs)
    score = 0 if conflict else round((0.4 * bool(matched) + 0.2 * skin_match + 0.1 * sensitivity_match +
                                     0.1 * (product.price <= ceiling) + 0.05 * preference_match +
                                     0.15 * bool(product.ingredients)) * 100)
    reasons = []
    if matched:
        reasons.append("Category relates to " + ", ".join(matched).replace("_", " "))
    if skin_match: reasons.append("Listed for this estimated skin type")
    if sensitivity_match: reasons.append("Suitable for your sensitivity preference")
    if product.price <= ceiling: reasons.append("Within your selected budget")
    return {"score": score, "reasons": reasons, "links": marketplace_links(product)}