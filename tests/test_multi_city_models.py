"""
Tests for 4-City Multi-Model Feature Parity:
Verifies that Indus, Quetta, Islamabad, and Siachen all deliver calibrated
Machine Learning driver attributions and 2026-2050 Monte Carlo future percentiles.
"""

import pytest
from starlette.testclient import TestClient
from api.index import app

client = TestClient(app)

CITIES = ["indus", "quetta", "islamabad", "siachen"]
SCENARIOS = ["current_trend", "accelerated", "controlled"]


@pytest.mark.parametrize("city", CITIES)
def test_city_driver_model_richness(city):
    """Verify each city has a full ML driver model with 5 features and damage classes."""
    resp = client.get(f"/api/hotspots/{city}/drivers")
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["hotspot_id"] == city
    assert "model_type" in data
    assert "training_samples" in data and data["training_samples"] >= 10000
    assert "spatial_block_cv_r2" in data and data["spatial_block_cv_r2"] > 0.30
    
    feat_imp = data["feature_attribution_importance"]
    assert len(feat_imp) >= 5, f"Expected 5 features for {city}, got {len(feat_imp)}"
    
    for feat_name, feat_meta in feat_imp.items():
        assert "importance_score" in feat_meta
        assert "percentage" in feat_meta
        assert "description" in feat_meta

    assert "geotechnical_damage_classes" in data
    classes = data["geotechnical_damage_classes"]["classes"]
    assert len(classes) == 5, f"Expected 5 hazard classes for {city}, got {len(classes)}"
    assert data["scientific_synthesis"]


@pytest.mark.parametrize("city", CITIES)
@pytest.mark.parametrize("scenario", SCENARIOS)
def test_city_future_simulation_percentiles(city, scenario):
    """Verify that every city and every scenario outputs Monte-Carlo percentiles (p10, median, p90)."""
    resp = client.get(f"/api/hotspots/{city}/future-simulation?year=2035&scenario={scenario}")
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["hotspot_id"] == city
    assert data["year"] == 2035
    assert data["scenario"] == scenario
    assert data["scenario_code"] in ["S1", "S2", "S3"]
    assert data["monte_carlo_draws"] == 500
    assert "population_at_risk" in data and data["population_at_risk"] > 0
    assert "buildings_in_damage_zone" in data and data["buildings_in_damage_zone"] > 0
    assert "risk_level" in data
    assert "policy_summary" in data

    # Verify percentiles existence and logic: p10 <= median <= p90
    if city == "quetta":
        assert "bowl_maximum_percentiles" in data
        p = data["bowl_maximum_percentiles"]
        assert p["p10_cm"] <= p["median_cm"] <= p["p90_cm"]
    else:
        assert "percentiles" in data
        p = data["percentiles"]
        vals = list(p.values())
        assert len(vals) == 3
        assert vals[0] <= vals[1] <= vals[2], f"Percentiles not ordered: {vals}"


def test_controlled_scenario_effectiveness():
    """Verify that S3 (controlled) reduces damage across all 4 regions significantly (> 60%)."""
    for city in CITIES:
        resp = client.get(f"/api/hotspots/{city}/future-simulation?year=2050&scenario=controlled")
        assert resp.status_code == 200
        data = resp.json()
        assert data["damage_reduction_pct"] >= 60.0, f"Expected >= 60% damage reduction for {city}, got {data['damage_reduction_pct']}%"
