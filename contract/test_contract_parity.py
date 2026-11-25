"""
اختبار التطابق بين العقد اليدوي (openapi.yaml) والسكيما المولدة من التطبيق
المرجعي (/openapi.json) — أوفلاين بالكامل عبر TestClient بلا خادم ولا منفذ.

القاعدة: العقد اليدوي هو المرجع. أي مسار/طريقة في العقد اليدوي يجب أن يظهر
في السكيما المولدة، وكيان ProjectDetail يجب أن يحمل evidence وmetrics —
وإلا فالتنفيذ المرجعي انحرف عن العقد.

تشغيل: python -m pytest test_contract_parity.py -v
البيئة: python>=3.11, pytest, fastapi, httpx, PyYAML.
"""
import os
import sys

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "reference"))

from fastapi.testclient import TestClient  # noqa: E402

import app as reference_app  # noqa: E402

with open(os.path.join(os.path.dirname(__file__), "openapi.yaml"),
          encoding="utf-8") as f:
    MANUAL = yaml.safe_load(f)

reference_app.init_db()
reference_app.seed_db()
CLIENT = TestClient(reference_app.app)
GENERATED = CLIENT.get("/openapi.json").json()

METHODS = ("get", "post", "put", "delete", "patch")


def manual_routes():
    return {(p, m) for p, ops in MANUAL["paths"].items()
            for m in ops if m in METHODS}


def generated_routes():
    return {(p, m) for p, ops in GENERATED["paths"].items()
            for m in ops if m in METHODS}


def test_every_manual_route_implemented():
    missing = manual_routes() - generated_routes()
    assert not missing, f"مسارات في العقد بلا تنفيذ مرجعي: {sorted(missing)}"


def test_no_undocumented_routes():
    extra = generated_routes() - manual_routes()
    assert not extra, f"مسارات منفذة غير موثقة في العقد: {sorted(extra)}"


def test_project_detail_carries_evidence_and_metrics():
    schemas = GENERATED["components"]["schemas"]
    assert "ProjectDetail" in schemas, "ProjectDetail غائب عن السكيما المولدة"
    props = schemas["ProjectDetail"].get("properties", {})
    for field in ("evidence", "metrics"):
        assert field in props, f"الحقل {field} غائب عن ProjectDetail"


def test_detail_endpoint_returns_nested_evidence():
    r = CLIENT.get("/projects/vulnradar")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body.get("evidence"), list)
    assert isinstance(body.get("metrics"), list)
    if body["evidence"]:
        ev = body["evidence"][0]
        for key in ("type", "url", "recorded_at"):
            assert key in ev, f"مفتاح {key} غائب عن Evidence"


def test_unknown_project_still_404():
    r = CLIENT.get("/projects/no-such-project")
    assert r.status_code == 404


def test_metric_run_schema_matches_manual_required():
    manual_req = set(MANUAL["components"]["schemas"]["MetricRun"]["required"])
    gen = GENERATED["components"]["schemas"].get("MetricRun", {})
    gen_req = set(gen.get("required", []))
    assert manual_req <= gen_req, (
        f"حقول MetricRun إلزامية في العقد وغير إلزامية في التنفيذ: "
        f"{sorted(manual_req - gen_req)}")
