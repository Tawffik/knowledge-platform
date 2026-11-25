"""
اختبارات العقد — حالات رفض سالبة + حالتا نجاح (منهجية التقييم المتفق عليها).

المنطق:
- كل حالة سالبة تمرّ (PASS) فقط إذا رفض الخادم الإدخال غير الصالح فعلًا
  بـ 400/422. قبول الخادم للإدخال الفاسد = فشل حقيقي في الاختبار.
- بدون خادم على BASE_URL تُتخطى كل الاختبارات (SKIP) بسبب مُعلن —
  غياب الخادم حالة تشغيل مُقاسة، وليس نتيجة متوقعة مسبقًا.
- تتحول لبوابة قبول لنسخة الكارِف الأولى: ٨/٨ تمر مع خادم يطبق العقد.

تشغيل قابل للتكرار:
    python -m pytest test_contract_negative.py -v
البيئة: python>=3.11, pytest, httpx. BASE_URL متغير بيئة (افتراضي http://127.0.0.1:8000).
"""
import os
import httpx
import pytest

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:8000")


def _backend_up() -> bool:
    try:
        httpx.get(f"{BASE}/openapi.json", timeout=2.0)
        return True
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(
    not _backend_up(),
    reason=f"لا يوجد خادم على {BASE} — التخطي سلوك مُقاس وليس نتيجة متوقعة",
)

CLIENT = httpx.Client(base_url=BASE, timeout=5.0)

# --- حالات الرفض السالبة (تمر عندما يرفض الخادم بـ 400/422) ---

def test_knowledge_entry_without_source_rejected():
    """إدخال معرفة بلا source_url/checked_at يُرفض — الصدق هيكلي."""
    r = CLIENT.post("/knowledge", json={
        "title": "أداة X", "kind": "tool-note", "verification": "tested"})
    assert r.status_code in (400, 422)


def test_knowledge_entry_invalid_verification_label_rejected():
    """تصنيف تحقق خارج (tested/documented/untested) يُرفض."""
    r = CLIENT.post("/knowledge", json={
        "title": "أداة Y", "kind": "tool-note", "verification": "probably-free",
        "source_url": "https://example.com", "checked_at": "2026-11-25"})
    assert r.status_code in (400, 422)


def test_ledger_entry_without_run_command_rejected():
    """تشغيلة بلا أمر تشغيل تُرفض — لا قابلية تكرار بلا أمر."""
    r = CLIENT.post("/ledger", json={
        "project_slug": "vulnradar", "action": "scan", "result": "pass",
        "ran_at": "2026-11-25T21:00:00Z"})
    assert r.status_code in (400, 422)


def test_review_without_reason_rejected():
    """قرار مراجعة بلا سبب يُرفض — منهجية المراجعة المتبادلة."""
    r = CLIENT.post("/reviews", json={
        "subject": "coordination/platform/design-discussion.md",
        "reviewer": "elkaref", "decision": "accepted",
        "reviewed_at": "2026-11-25T21:00:00Z"})
    assert r.status_code in (400, 422)


def test_review_invalid_decision_rejected():
    """قرار مراجعة خارج (accepted/rejected/accepted-with-notes) يُرفض."""
    r = CLIENT.post("/reviews", json={
        "subject": "coordination/platform/design-discussion.md",
        "reviewer": "elkaref", "decision": "looks-good",
        "reason": "سبب موجود لكن القرار خارج القائمة",
        "reviewed_at": "2026-11-25T21:00:00Z"})
    assert r.status_code in (400, 422)


def test_project_slug_pattern_enforced():
    """سلاج بأحرف غير صالحة لا يطابق النمط ^[a-z0-9-]+$."""
    r = CLIENT.get("/projects/Bad_Slug!")
    assert r.status_code in (400, 404, 422)

# --- حالات نجاح (تمر مع خادم يطبق العقد) ---

def test_projects_list_shape():
    r = CLIENT.get("/projects")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_openapi_docs_exposed():
    """ادعاء API-first قابل للفحص: /openapi.json متاح."""
    assert CLIENT.get("/openapi.json").status_code == 200
