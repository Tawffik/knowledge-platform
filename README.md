# منصة المعرفة (Knowledge Platform)

عقد API + باك إند مرجعي + اختبارات قبول لمنصة المعرفة. ريبو خاص.

**المنشأ:** نُقل من `security-youtube-channel-plan/coordination/platform/` في 26 نوفمبر 2026 (تصحيح تنظيمي بموافقة المالك). النسخة الأصلية محفوظة هناك كأرشيف تاريخي موسوم «مستبدَل» — هذا الريبو هو الموضع الكنسي.

## البنية
- [contract/openapi.yaml](contract/openapi.yaml) — عقد API: 5 مسارات، 10 schemas (validator PASS)
- [contract/test_schema_offline.py](contract/test_schema_offline.py) — حزمة schemas offline: 9/9 PASS
- [contract/test_contract_negative.py](contract/test_contract_negative.py) — اختبارات سلبية ضد سيرفر حي: 8/8 PASS
- [contract/reference/app.py](contract/reference/app.py) — باك إند مرجعي (FastAPI + SQLite): 8/8 acceptance
- [design-discussion.md](design-discussion.md) — نقاش التصميم والبوابات

## حالة القياس (26 نوفمبر 2026)
كل النتائج أعلاه «توافق أساسي» (🟡) — اختبارات من كاتب الكود (Instinct)، **ليست تقييمًا مستقلًا**. مراجعة Muse المستقلة وحالاتها السلبية معلّقة. بوابة التقييم الكاملة في ريبو project-brain.

## خارج النطاق
- مستورد cveNotify التجريبي ليس جزءًا من هذا الريبو: مكانه الصحيح VulnRadar (قرار المالك). النموذج التجريبي التاريخي بقي في security-youtube-channel-plan.
- لا جلب تلقائي متكرر لمصادر خارجية، لا نشر عام، لا مشاركة رموز دخول.
