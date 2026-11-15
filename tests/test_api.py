"""
Unit and Integration Tests for SAR-Pulse FastAPI Backend
NASA Space Apps Challenge 2026 — "Dancing with the SARs"
"""

import pytest
from starlette.testclient import TestClient
from api.index import app

client = TestClient(app)


def test_health_check():
    """Verify system health, versioning, and supported missions."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "2.1.0"
    assert "indus" in data["active_hotspots"]
    assert "quetta" in data["active_hotspots"]
    assert len(data["supported_missions"]) >= 5


def test_get_all_hotspots():
    """Verify summary list of 4 Pakistan hotspots for the map dots."""
    response = client.get("/api/hotspots")
    assert response.status_code == 200
    hotspots = response.json()
    assert len(hotspots) == 4
    
    ids = {h["id"] for h in hotspots}
    assert ids == {"indus", "quetta", "islamabad", "siachen"}
    
    for h in hotspots:
        assert "lat" in h
        assert "lon" in h
        assert "badge" in h
        assert "color" in h
        assert "severity" in h


@pytest.mark.parametrize("hotspot_id", ["indus", "quetta", "islamabad", "siachen"])
def test_get_hotspot_detail(hotspot_id):
    """Verify 5-chapter presentation dossier, radar context, and live telemetry."""
    response = client.get(f"/api/hotspots/{hotspot_id}?include_live_sar=false")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == hotspot_id
    assert "chapters" in data
    assert len(data["chapters"]) == 5
    
    # Verify each chapter structure
    for ch in data["chapters"]:
        assert "step" in ch
        assert "title" in ch
        assert "body" in ch
        assert "metrics" in ch
        assert len(ch["metrics"]) >= 2
    
    # Verify scientific ground truths & radar HDF5 paths
    assert "scientific_context" in data
    sci = data["scientific_context"]
    assert "hdf5_datasets" in sci
    assert "preprocessing_rule" in sci
    assert "Lee" in sci["preprocessing_rule"] or "InSAR" in sci["satellite_mission"]
    
    # Verify sonification audio synthesis parameters
    assert "sonification" in data
    son = data["sonification"]
    assert "base_frequency_hz" in son
    assert "waveform" in son
    assert len(son["tension_curve"]) == 5
    
    # Verify live environmental data
    assert "live_environmental" in data
    assert "soil_moisture_topsoil_m3m3" in data["live_environmental"]


def test_hotspot_not_found():
    """Verify 404 behavior for unknown hotspot ID."""
    response = client.get("/api/hotspots/unknown_place")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


@pytest.mark.parametrize("hotspot_id", ["indus", "quetta", "islamabad", "siachen"])
def test_get_hotspot_timeline(hotspot_id):
    """Verify sensor time series data for charting."""
    response = client.get(f"/api/hotspots/{hotspot_id}/timeline")
    assert response.status_code == 200
    data = response.json()
    
    assert data["hotspot_id"] == hotspot_id
    assert "series" in data
    assert len(data["series"]) >= 5
    assert "metric_primary" in data
    
    first_epoch = data["series"][0]
    assert "date" in first_epoch
    assert "primary_val" in first_epoch
    assert "epoch" in first_epoch


def test_timeline_not_found():
    """Verify 404 on invalid hotspot timeline request."""
    response = client.get("/api/hotspots/mars_rover/timeline")
    assert response.status_code == 404


@pytest.mark.parametrize("scenario", ["current_trend", "accelerated", "controlled"])
def test_future_simulation_quetta(scenario):
    """Verify dynamic 2026-2050 simulation engine for Quetta."""
    response = client.get(f"/api/hotspots/quetta/future-simulation?year=2040&scenario={scenario}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["hotspot_id"] == "quetta"
    assert data["year"] == 2040
    assert data["scenario"] == scenario
    assert "median_subsidence_cm" in data
    assert "bowl_maximum_sinking_cm" in data
    assert "buildings_in_damage_zone" in data
    assert "population_at_risk" in data
    
    if scenario == "controlled":
        assert data["damage_reduction_pct"] > 80.0
    elif scenario == "accelerated":
        assert data["bowl_maximum_sinking_cm"] > 150.0


def test_future_simulation_year_validation():
    """Verify year range validation (2026-2050)."""
    # Year before 2026
    resp_past = client.get("/api/hotspots/quetta/future-simulation?year=2015")
    assert resp_past.status_code == 422
    
    # Year after 2050
    resp_future = client.get("/api/hotspots/quetta/future-simulation?year=2100")
    assert resp_future.status_code == 422


@pytest.mark.parametrize("hotspot_id", ["indus", "quetta", "islamabad", "siachen"])
def test_get_hotspot_figures(hotspot_id):
    """Verify generated figures catalog."""
    response = client.get(f"/api/hotspots/{hotspot_id}/figures")
    assert response.status_code == 200
    data = response.json()
    assert data["hotspot_id"] == hotspot_id
    assert "figures" in data
    assert len(data["figures"]) >= 1
    
    fig = data["figures"][0]
    assert "id" in fig
    assert "title" in fig
    assert "api_url" in fig


def test_serve_figure_file():
    """Verify streaming generated PNG figures."""
    # Test existing figure
    rel_path = "quetta-check/final/moneyshot/side_by_side_336d_vs_132d.png"
    response = client.get(f"/api/figures/{rel_path}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 10000


def test_serve_figure_not_found():
    """Verify 404 on missing figure."""
    response = client.get("/api/figures/non_existent_image.png")
    assert response.status_code == 404


def test_universal_satellite_query():
    """Verify universal lat/lon coordinate query."""
    response = client.get("/api/satellites/query?lat=30.175&lon=66.984")
    assert response.status_code == 200
    data = response.json()
    assert data["coordinates"]["lat"] == 30.175
    assert data["coordinates"]["lon"] == 66.984
    assert "environmental_telemetry" in data
    assert "nisar_hdf5_structure" in data
    assert "nasa_asf_granules" in data


def test_satellite_layers():
    """Verify tile layers configuration."""
    response = client.get("/api/satellites/layers")
    assert response.status_code == 200
    data = response.json()
    assert "satellite_basemap" in data
    assert "tactical_dark" in data
    assert "nasa_gibs_optical" in data
