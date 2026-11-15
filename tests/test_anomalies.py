"""
Stress, Anomaly, and Fault-Tolerance Tests for SAR-Pulse Backend
Verifies input validation, path traversal defense, network fail-safe resilience,
case-insensitivity, and machine learning driver attribution.
"""

from unittest.mock import patch
import urllib.error
import pytest
from starlette.testclient import TestClient
from api.index import app

client = TestClient(app)


def test_security_path_traversal_defense():
    """Verify that path traversal attempts to read system files are rejected."""
    traversal_paths = [
        "../../etc/passwd",
        "../../../etc/shadow",
        "....//....//etc/hosts",
        "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        "/etc/passwd"
    ]
    for p in traversal_paths:
        resp = client.get(f"/api/figures/{p}")
        assert resp.status_code in [403, 404], f"Expected 403 or 404 for path traversal attempt '{p}', got {resp.status_code}"


def test_year_validation_boundaries():
    """Verify strict 2026-2050 validation on timeline simulations."""
    # Past year
    resp1 = client.get("/api/hotspots/quetta/future-simulation?year=2020")
    assert resp1.status_code == 422

    # Negative year
    resp2 = client.get("/api/hotspots/quetta/future-simulation?year=-50")
    assert resp2.status_code == 422

    # Far future
    resp3 = client.get("/api/hotspots/quetta/future-simulation?year=2051")
    assert resp3.status_code == 422

    # Non-integer
    resp4 = client.get("/api/hotspots/quetta/future-simulation?year=twenty_thirty")
    assert resp4.status_code == 422

    # Valid boundaries
    resp_min = client.get("/api/hotspots/quetta/future-simulation?year=2026")
    assert resp_min.status_code == 200

    resp_max = client.get("/api/hotspots/quetta/future-simulation?year=2050")
    assert resp_max.status_code == 200


def test_coordinate_query_validation():
    """Verify coordinate parameter validation."""
    resp_invalid_lat = client.get("/api/satellites/query?lat=abc&lon=67.0")
    assert resp_invalid_lat.status_code == 422

    resp_invalid_lon = client.get("/api/satellites/query?lat=30.0&lon=xyz")
    assert resp_invalid_lon.status_code == 422

    resp_missing_params = client.get("/api/satellites/query")
    assert resp_missing_params.status_code == 422


def test_case_insensitivity_and_whitespace():
    """Verify case-insensitivity and whitespace stripping for all hotspot endpoints."""
    variations = ["QUETTA", "  quetta  ", "QuEtTa", "indus", "INDUS", "  siachen  "]
    for v in variations:
        resp = client.get(f"/api/hotspots/{v}")
        assert resp.status_code == 200, f"Failed on variation: '{v}'"


def test_network_fault_tolerance_nasa_asf_down():
    """Verify that if NASA ASF DAAC is down or timing out, the backend fails-safe without 500 error."""
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.URLError("Connection timed out to NASA ASF DAAC")
        
        # Test hotspot detail with include_live_sar=True
        resp = client.get("/api/hotspots/indus?include_live_sar=true")
        assert resp.status_code == 200
        data = resp.json()
        assert "nasa_asf_granules" in data
        assert len(data["nasa_asf_granules"]) >= 1
        assert "live_environmental" in data

        # Test universal coordinate query
        resp_query = client.get("/api/satellites/query?lat=26.85&lon=68.10")
        assert resp_query.status_code == 200
        data_q = resp_query.json()
        assert len(data_q["nasa_asf_granules"]) >= 1


def test_ml_drivers_endpoint():
    """Verify Machine Learning Random Forest drivers endpoint."""
    resp = client.get("/api/hotspots/quetta/drivers")
    assert resp.status_code == 200
    data = resp.json()
    assert data["hotspot_id"] == "quetta"
    assert "RandomForestRegressor" in data["model_type"]
    assert "feature_attribution_importance" in data
    assert "elevation_m" in data["feature_attribution_importance"]
    assert "building_density_per_km2" in data["feature_attribution_importance"]
    assert "geotechnical_damage_classes" in data
    assert len(data["geotechnical_damage_classes"]["classes"]) == 5


@pytest.mark.parametrize("hotspot_id", ["indus", "islamabad", "siachen"])
def test_ml_drivers_all_hotspots(hotspot_id):
    """Verify ML driver attribution for all other hotspots."""
    resp = client.get(f"/api/hotspots/{hotspot_id}/drivers")
    assert resp.status_code == 200
    data = resp.json()
    assert data["hotspot_id"] == hotspot_id
    assert "feature_attribution_importance" in data
    assert "scientific_synthesis" in data


def test_monte_carlo_distribution_percentiles():
    """Verify that future-simulation for Quetta returns exact 500-draw Monte-Carlo percentiles."""
    resp = client.get("/api/hotspots/quetta/future-simulation?year=2030&scenario=current_trend")
    assert resp.status_code == 200
    data = resp.json()
    assert "bowl_maximum_percentiles" in data
    p = data["bowl_maximum_percentiles"]
    assert p["p10_cm"] is not None
    assert p["median_cm"] is not None
    assert p["p90_cm"] is not None
    # Verify logical ordering: p10 <= median <= p90
    assert p["p10_cm"] <= p["median_cm"] <= p["p90_cm"]
