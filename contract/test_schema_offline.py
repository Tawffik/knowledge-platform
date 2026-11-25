"""
اختبارات العقد أوفلاين — التحقق من سكيمات openapi.yaml نفسها (بلا خادم).

الفرق عن test_contract_negative.py:
- ذاك يختبر سلوك الخادم (يتخطى بلا خادم).
- هذا يختبر أن السكيمات نفسها تقبل الحمولات السليمة وترفض الفاسدة —
  أي أن رفض 422 المتوقع من الخادم مشروح فعلًا في العقد، مش مجرد نية.

تشغيل: python -m pytest test_schema_offline.py -v
البيئة: python>=3.11, pytest, jsonschema, PyYAML.
"""
import jsonschema
import pytest
import yaml

with open("openapi.yaml", encoding="utf-8") as f:
    SPEC = yaml.safe_load(f)

SCHEMAS = SPEC["components"]["schemas"]
RESOLVER = jsonschema.RefResolver("", SPEC)


def validator(name):
    return jsonschema.Draft202012Validator(SCHEMAS[name], resolver=RESOLVER)


VALID_KNOWLEDGE = {
    "title": "أداة X", "kind": "tool-note", "verification": "tested",
    "source_url": "https://example.com/tool", "checked_at": "2026-11-25",
    "tags": ["osint"],
}

VALID_METRIC = {
    "name": "H1-H14 gate", "baseline": "0/10", "result": "4/4",
    "method": "هارنس أوفلاين على فيكستشرز ثابتة",
    "run_command": "python -m pytest abh-evals -q",
    "pass_fail_criteria": "كل فيكستشر يعدي بوابته المعلنة",
    "declared_failing_cases": "٤ حالات معلنة في README",
    "run_at": "2026-11-25T21:00:00Z",
}

VALID_PROJECT = {
    "slug": "vulnradar", "title": "VulnRadar", "status": "wip",
    "skills": ["python", "osint"], "attribution": "أصلي",
}


def test_valid_knowledge_entry_accepted():
    validator("KnowledgeEntry").validate(VALID_KNOWLEDGE)


def test_knowledge_entry_missing_source_rejected():
    bad = {k: v for k, v in VALID_KNOWLEDGE.items() if k != "source_url"}
    with pytest.raises(jsonschema.ValidationError):
        validator("KnowledgeEntry").validate(bad)


def test_knowledge_entry_bad_verification_label_rejected():
    bad = dict(VALID_KNOWLEDGE, verification="probably-free")
    with pytest.raises(jsonschema.ValidationError):
        validator("KnowledgeEntry").validate(bad)


def test_valid_metric_run_accepted():
    validator("MetricRun").validate(VALID_METRIC)


def test_metric_run_missing_run_command_rejected():
    bad = {k: v for k, v in VALID_METRIC.items() if k != "run_command"}
    with pytest.raises(jsonschema.ValidationError):
        validator("MetricRun").validate(bad)


def test_review_without_reason_rejected():
    with pytest.raises(jsonschema.ValidationError):
        validator("ReviewRecordIn").validate({
            "subject": "coordination/platform/contract/openapi.yaml",
            "reviewer": "elkaref", "decision": "accepted",
            "reviewed_at": "2026-11-25T21:00:00Z"})


def test_review_bad_decision_rejected():
    with pytest.raises(jsonschema.ValidationError):
        validator("ReviewRecordIn").validate({
            "subject": "x", "reviewer": "elkaref", "decision": "looks-good",
            "reason": "موجود", "reviewed_at": "2026-11-25T21:00:00Z"})


def test_valid_project_accepted():
    validator("Project").validate(VALID_PROJECT)


def test_project_bad_slug_rejected():
    with pytest.raises(jsonschema.ValidationError):
        validator("Project").validate(dict(VALID_PROJECT, slug="Bad_Slug!"))
