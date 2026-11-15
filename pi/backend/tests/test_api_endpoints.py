"""
Integration tests for FastAPI endpoints (HL2 control, Hardware, Digital Modes, Audio).
"""
import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from sota_cw.api import app

client = TestClient(app)


def test_health_endpoints():
    r1 = client.get("/health")
    assert r1.status_code == 200
    assert r1.json()["status"] == "ok"

    r2 = client.get("/healthz")
    assert r2.status_code == 200
    assert r2.json()["status"] == "healthy"


def test_frequency_endpoints():
    r_set = client.post("/hl2/frequency", json={"hz": 14074000})
    assert r_set.status_code == 200
    assert r_set.json()["frequency_hz"] == 14074000
    assert "20m" in r_set.json()["band"]

    r_get = client.get("/hl2/frequency")
    assert r_get.status_code == 200
    assert r_get.json()["frequency_hz"] == 14074000


def test_mode_endpoints():
    r_set = client.post("/hl2/mode", json={"mode": "USB"})
    assert r_set.status_code == 200
    assert r_set.json()["mode"] == "USB"

    r_get = client.get("/hl2/mode")
    assert r_get.status_code == 200
    assert r_get.json()["mode"] == "USB"


def test_hardware_status_endpoints():
    r_n2adr = client.get("/hardware/n2adr/status")
    assert r_n2adr.status_code == 200
    assert "band" in r_n2adr.json()

    r_io = client.get("/hardware/ioboard/status")
    assert r_io.status_code == 200


def test_wsjtx_endpoints():
    r_status = client.get("/wsjtx/status")
    assert r_status.status_code == 200
    assert "connected" in r_status.json()

    r_decodes = client.get("/wsjtx/decodes")
    assert r_decodes.status_code == 200
    assert isinstance(r_decodes.json(), list)


def test_fldigi_endpoints():
    r_status = client.get("/fldigi/status")
    assert r_status.status_code == 200
    assert "modem" in r_status.json()
