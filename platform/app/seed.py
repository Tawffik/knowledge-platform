"""Seed the Nx01 Platform DB from the owner's real local source files.

Rebuilds data/platform.db from:
  - a curated project list grounded in
    ~/workspace/your_files/projects-and-portfolio-plan.md
  - ~/workspace/bug-bounty-intel-vault/  (verified payouts, writeups, tips, research)
  - ~/workspace/zero-track-lab/ledger/ledger-template.jsonl (flagged examples)

Run:  python -m app.seed
Nothing here invents data: every vault row carries the source URL from the
vault files, and only the *verified* payouts file is parsed.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db import connect, init_schema  # noqa: E402

HOME = os.path.expanduser("~")
VAULT = os.path.join(HOME, "workspace", "bug-bounty-intel-vault")
LAB_LEDGER = os.path.join(
    HOME, "workspace", "zero-track-lab", "ledger", "ledger-template.jsonl"
)
GH = "https://github.com/Tawffik"

# ---------------------------------------------------------------- projects
# Grounded in projects-and-portfolio-plan.md (audit of the owner's GitHub).
PROJECTS = [
    dict(slug="bugbountyci", name="BugBountyCI — Zero Track",
         tagline="Security recon & signal-triage pipeline on GitHub Actions",
         summary="Pipeline of ~75 named steps: deterministic tooling, ranking and "
                 "review queues, with an Engineering Ledger documented up to PR #96. "
                 "The owner's most mature automation-engineering work.",
         skills="security automation,CI/CD,triage engineering,Python,GitHub Actions",
         status="live", is_hero=1, visibility="private", repo_url=f"{GH}/BugBountyCI",
         note="Private repo — public sanitised mirror planned (zero-track-showcase)."),
    dict(slug="vulnradar", name="VulnRadar",
         tagline="CVE intelligence merged from 5 sources, prioritised and target-linked",
         summary="Merges CVE.org, GitHub Advisories, NVD, Nuclei templates and CISA KEV "
                 "into one prioritised feed tied to hunt targets, with tests, hunt "
                 "workflows and live outputs published in the repo.",
         skills="threat intelligence,data engineering,Python,GitHub Actions",
         status="live", is_hero=1, visibility="public", repo_url=f"{GH}/VulnRadar",
         note="Strongest public project; feeds the Zero Track Lab intel stage."),
    dict(slug="cyberos", name="CyberOS (My-app-)",
         tagline="Offline-first Android security-research workstation",
         summary="Kotlin + Jetpack Compose app (v1.1.0): security curriculum, notes "
                 "vault with wiki-links and graph view, spaced repetition, a bug "
                 "bounty workspace (programs/findings/reports) and AI tutors with "
                 "human-in-the-loop rules. Android CI, SECURITY.md, CONTRIBUTING.md.",
         skills="Kotlin,Jetpack Compose,Android,product engineering,offline-first",
         status="live", is_hero=1, visibility="public", repo_url=f"{GH}/My-app-",
         note="Portfolio Release v1.2.0 planned (see CyberOS plan in the audit)."),
    dict(slug="security-research-agent", name="security-research-agent",
         tagline="Control plane for a security research agent",
         summary="Authorization enforcement, resumable state, hash-chained evidence, "
                 "adversarial self-verification and a skills system. README reports "
                 "341 passing tests with CI.",
         skills="AI agent architecture,evidence integrity,Python,testing",
         status="live", is_hero=0, visibility="public",
         repo_url=f"{GH}/security-research-agent", note=None),
    dict(slug="agentic-bug-hunter", name="Agentic-Bug-Hunter",
         tagline="Agentic bug-hunting framework (hunting engine of Zero Track Lab)",
         summary="Agent-driven bug hunting framework used as the finder stage of the "
                 "Zero Track Lab pipeline.",
         skills="AI agents,bug bounty automation,Python",
         status="live", is_hero=0, visibility="public",
         repo_url=f"{GH}/Agentic-Bug-Hunter",
         attribution="Fork of AwareXone/Agentic-Bug-Hunter (the repo is "
              "officially marked as a fork). README, license and links still "
              "belong to the upstream project — branding cleanup pending; "
              "the owner's own contribution is his fork work on top of "
              "upstream.",
         note="Attribution under clarification: the repo README/branding currently "
              "belong to the upstream third-party project AwareXone; the owner's own "
              "contribution must be documented precisely before portfolio use."),
    dict(slug="llm-security-guard", name="llm-security-guard",
         tagline="LLM guardrails mini-project mapped to OWASP LLM Top 10",
         summary="Normalization + token-smuggling detection, PII redaction, output "
                 "guardrail, rate limiter, circuit breaker and human-in-the-loop — "
                 "each component mapped to the OWASP LLM Top 10, with tests and an "
                 "honest limitations section.",
         skills="LLM security,guardrails,Python,OWASP LLM Top 10",
         status="live", is_hero=0, visibility="public",
         repo_url=f"{GH}/llm-security-guard",
         note="Becomes the defence-under-test of the proposed Red-Team Harness."),
    dict(slug="security-research-agent-lite", name="security-research-agent-lite",
         tagline="Runnable vertical slice of the research-agent pipeline",
         summary="Recon → Normalize → Scope → Hypothesis → BOLA skill → Evidence → "
                 "FP gate → Researcher/Skeptic/Referee → Report, with runnable "
                 "positive/secure/public scenarios.",
         skills="AI agents,pipeline design,Python",
         status="live", is_hero=0, visibility="public",
         repo_url=f"{GH}/security-research-agent-lite", note=None),
    dict(slug="web-api-pentest-portfolio", name="web-api-pentest-portfolio",
         tagline="Professional portfolio repo: capability matrix backed by evidence",
         summary="Junior Web/API Pentester identity, a capability matrix with the "
                 "status and evidence type of each skill, and an explicit statement "
                 "of what the portfolio is not. BOLA/IDOR/BFLA, Burp Suite.",
         skills="web/API pentesting,reporting,Burp Suite",
         status="live", is_hero=0, visibility="public",
         repo_url=f"{GH}/web-api-pentest-portfolio", note=None),
    dict(slug="ai-agent-security-study", name="ai-agent-security-study",
         tagline="6-week Markdown-first study lab: from web bounty to LLM/agent security",
         summary="Study plan, lab journal, writeup templates and a verified source "
                 "index for moving from web bug bounty into LLM and agent security.",
         skills="LLM security,agent security,study system",
         status="live", is_hero=0, visibility="public",
         repo_url=f"{GH}/ai-agent-security-study", note=None),
    dict(slug="exposure-intelligence", name="exposure-intelligence",
         tagline="Passive exposure research over public indexes, human-queued",
         summary="Searches public indexes (GitHub code, URLScan, archives) for "
                 "leak/exposure signals about an authorised target; output goes to a "
                 "HUMAN_QUEUE for human review.",
         skills="OSINT,passive recon,ethics of scope",
         status="live", is_hero=0, visibility="public",
         repo_url=f"{GH}/exposure-intelligence", note=None),
    dict(slug="zero-track-showcase", name="zero-track-showcase",
         tagline="Public runnable skeleton of the Zero Track pipeline",
         summary="Recon → exposure classification → triage skeleton, designed so "
                 "another engineer can clone and extend it. Candidate public mirror "
                 "of BugBountyCI.",
         skills="pipeline design,documentation,Python",
         status="live", is_hero=0, visibility="public",
         repo_url=f"{GH}/zero-track-showcase", note=None),
    dict(slug="methodology-os", name="Bug Bounty Methodology OS (bb-* family)",
         tagline="333 classified agent skills + executable hunting playbooks",
         summary="bug-bounty-tips-skills (333 skills: Recon 175, API Hacking 97, ...) "
                 "plus the bb-* playbook family (recon-exposure, ssrf-hunting, "
                 "scan-playbook, info-disclosure, report-template, "
                 "chatbot-support-hunting, universal-hunting-methodology).",
         skills="knowledge engineering,methodology,bug bounty",
         status="live", is_hero=0, visibility="public",
         repo_url=f"{GH}/bug-bounty-tips-skills",
         note="Plan: consolidate the scattered bb-* repos into one Methodology OS story."),
    dict(slug="bug-bounty-intel-vault", name="Bug Bounty Intel Vault",
         tagline="Verified payouts, real writeups, attributed tips — no invented numbers",
         summary="Aggregation project (built Nov 2026): notable documented payouts "
                 "verified on opened sources, 30 real writeups indexed by vuln class, "
                 "16 attributed techniques, 13 research pieces. Unverified figures are "
                 "quarantined in a separate leads file. This platform's Vault is "
                 "seeded from it.",
         skills="research,knowledge engineering,bug bounty intel",
         status="live", is_hero=0, visibility="public", repo_url=None,
         note="Local project; source of the Vault section of this platform."),
    dict(slug="furniture-commerce-os", name="furniture-commerce-os",
         tagline="Arabic RTL furniture commerce demo (catalogue, orders, ops board)",
         summary="Interactive full-stack product demo with mock data — side evidence "
                 "of product-building ability, outside the security front page.",
         skills="full-stack,RTL UI,product demo",
         status="live", is_hero=0, visibility="public",
         repo_url=f"{GH}/furniture-commerce-os", note="Listed under 'Also built'."),
    # ---- proposed (from the audit's section 3 + the flagship research) ----
    dict(slug="zero-track-lab", name="Zero Track Lab",
         tagline="Open, continuously operating autonomous bug bounty lab — public results ledger",
         summary="Flagship proposal (novelty-researched Nov 2026): VulnRadar intel → "
                 "in-scope target selection → agent hunting (ABH + BugBountyCI) → an "
                 "independent verification gate with deterministic replay → "
                 "human-accountable submission → LLM ASR measurement wing → an "
                 "append-only public ledger of ALL outcomes, rejects included.",
         skills="AI agents,verification,bug bounty,LLM red-teaming,measurement",
         status="proposed", is_hero=1, visibility="public", repo_url=None,
         note="Design package exists locally (zero-track-lab/); public claim gated on "
              "≥1 quarter, ≥30 program-verdict submissions, ≥100 gated candidates."),
    dict(slug="llm-red-team-harness", name="LLM Red-Team Evaluation Harness",
         tagline="Measure LLM app defences: attack library scored as ASR, before/after",
         summary="Python tool that runs an OWASP-LLM-classified attack library "
                 "(prompt injection, jailbreak, data exfiltration) against an endpoint "
                 "or demo app and reports Attack Success Rate before/after a defence. "
                 "Turns llm-security-guard from rules into measurement.",
         skills="AI security evaluation,Python,metrics,CI",
         status="proposed", is_hero=0, visibility="public", repo_url=None,
         note="Priority #1 of the new-projects plan."),
    dict(slug="api-authorization-lab", name="API Authorization Testing Lab",
         tagline="Intentionally vulnerable API + automated BOLA/BFLA test suite + patched version",
         summary="A small fake shop/bank API with documented planted BOLA/BFLA/broken-"
                 "auth flaws, a pytest suite that detects each one, and a patched "
                 "version the tests pass against.",
         skills="API security,pytest,secure coding",
         status="proposed", is_hero=0, visibility="public", repo_url=None, note=None),
    dict(slug="vulnradar-live", name="VulnRadar Live Dashboard",
         tagline="Live CVE-to-target correlation dashboard for VulnRadar output",
         summary="Publishes VulnRadar output as a live dashboard: newest CVEs crossed "
                 "with demo targets, plus a methodology page explaining the 5-source "
                 "merge and prioritisation.",
         skills="data visualisation,threat intel,product",
         status="proposed", is_hero=0, visibility="public", repo_url=None, note=None),
    dict(slug="detection-as-code", name="Detection-as-Code Pack",
         tagline="Sigma detections for the web/API attack patterns actually hunted",
         summary="Sigma rules (YARA where needed) detecting BOLA probing, SSRF "
                 "attempts and injection patterns in logs, with sigma-cli tests and "
                 "clean/attacked sample logs, mapped to MITRE ATT&CK.",
         skills="detection engineering,Sigma,blue team,MITRE ATT&CK",
         status="proposed", is_hero=0, visibility="public", repo_url=None, note=None),
    dict(slug="cyberos-masvs", name="CyberOS MASVS Self-Assessment",
         tagline="Published OWASP MASVS assessment of CyberOS, fixes included",
         summary="A public checklist of every MASVS control against CyberOS "
                 "(pass/fail/N/A + evidence), fixes for the fails, published as a "
                 "case study.",
         skills="mobile security,OWASP MASVS,Android",
         status="proposed", is_hero=0, visibility="public", repo_url=None, note=None),
]

# ------------------------------------------------------------------ helpers
URL_RE = re.compile(r"https?://[^\s)\]]+")

# curated-index shorthands used inside the vault writeups file
INDEX_URLS = {
    "BB157": "https://www.intigriti.com/researchers/blog/bug-bytes/bug-bytes-157-daily-bug-bounty-recaps-reading-other-bug-hunters-reports-hacking-google-drive-integrations",
    "BB133": "https://www.intigriti.com/researchers/blog/bug-bytes/bug-bytes-133-its-still-dns-a-50k-stray-token-path-traversal-in-microservices",
    "BB131": "https://www.intigriti.com/researchers/blog/bug-bytes/bug-bytes-131-credential-stuffing-in-bug-bounty-hijacking-shortlinks-hacker-shows",
    "TOP10-2025": "https://portswigger.net/research/top-10-web-hacking-techniques-of-2025",
    "HACKTIVITY": "https://hackerone.com/hacktivity/overview",
}


def first_url(text):
    m = URL_RE.search(text or "")
    return m.group(0).rstrip(".,") if m else None


def via_url(text):
    text = text or ""
    m = re.search(r"via (BB\d+|TOP10-2025|HACKTIVITY)", text)
    if m:
        return INDEX_URLS.get(m.group(1))
    if "Hacktivity" in text:
        return INDEX_URLS["HACKTIVITY"]
    if "HackerNoon analysis" in text or "hackernoon" in text.lower():
        return ("https://hackernoon.com/why-ai-agent-security-starts-"
                "with-permissions-not-prompts")
    return None


def bb_url(text):
    m = re.search(r"Bug Bytes #(\d+)", text or "")
    return INDEX_URLS.get(f"BB{m.group(1)}") if m else None


def clean(text):
    text = (text or "").replace("**", "").replace("*", "")
    return re.sub(r"\s+", " ", text).strip(" —-")


# ------------------------------------------------------------------ parsers
def parse_payouts(path):
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line.startswith("| $"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 5:
            continue
        amount = float(cells[0].replace("$", "").replace(",", ""))
        program, finding, vclass, verified_on = cells[1], cells[2], cells[3], cells[4]
        url = first_url(verified_on) or first_url(finding)
        if not url:  # e.g. "Bug Bytes #131" cited without a link in the cell
            m = re.search(r"Bug Bytes #(\d+)", verified_on)
            if m:
                url = INDEX_URLS.get(f"BB{m.group(1)}")
        out.append(dict(kind="payout", title=f"{program} — {finding[:90]}",
                        category=vclass, program=program,
                        summary=clean(finding), amount_usd=amount,
                        source_url=url, verified=1))
    return out


def parse_numbered(path, kind, with_lesson=True):
    """Parse '## Category' sections with 'N. **Title** ...' entries."""
    out, category, buf = [], None, []

    def flush():
        if not buf:
            return
        text = " ".join(buf)
        m = re.match(r"\d+\.\s+\*\*(.+?)\*\*", text)
        if not m:
            return
        title = clean(m.group(1))
        rest = text[m.end():]
        lesson = None
        lm = re.search(r"\*Lesson: (.+?)\*", rest)
        if lm:
            lesson = clean(lm.group(1))
        url = first_url(rest) or via_url(rest)
        summary = clean(re.sub(r"\*Lesson: .+?\*", "", rest))
        summary = re.sub(r"— (via .+|https?://\S+.*)$", "", summary).strip(" —-")
        out.append(dict(kind=kind, title=title, category=category,
                        program=None, summary=lesson or summary,
                        amount_usd=None, source_url=url, verified=1))

    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line.startswith("## "):
            flush(); buf = []
            category = clean(line[3:])
        elif re.match(r"\d+\.\s+\*\*", line):
            flush(); buf = [line]
        elif buf and line:
            buf.append(line)
    flush()
    return out


def parse_tips(path):
    out, category, buf = [], None, []

    def flush():
        if not buf:
            return
        text = " ".join(buf)
        m = re.match(r"\*\*(\d+)\.\s+(.+?)\*\*", text)
        if not m:
            return
        title = clean(m.group(2))
        rest = text[m.end():]
        url = first_url(rest) or via_url(rest) or bb_url(rest)
        body = re.split(r"— \*Source:", rest)[0]
        out.append(dict(kind="tip", title=title, category=category, program=None,
                        summary=clean(body), amount_usd=None,
                        source_url=url, verified=1))

    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line.startswith("## "):
            flush(); buf = []
            category = clean(line[3:])
        elif re.match(r"\*\*\d+\.\s", line):
            flush(); buf = [line]
        elif buf and line:
            buf.append(line)
    flush()
    return out


def parse_research(path):
    out, category, buf = [], None, []

    def flush():
        if not buf:
            return
        text = " ".join(buf)
        m = re.match(r"\d+\.\s+\*\*(.+?)\*\*", text)
        if not m:
            return
        title = clean(m.group(1))
        rest = text[m.end():]
        url = first_url(rest) or via_url(rest) or bb_url(rest)
        if not url and "Top 10 page above" in rest:
            url = INDEX_URLS["TOP10-2025"]
        summary = re.sub(r"— (via .+|https?://\S+.*)$", "", clean(rest)).strip(" —-")
        out.append(dict(kind="research", title=title, category=category,
                        program=None, summary=summary, amount_usd=None,
                        source_url=url, verified=1))

    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line.startswith("## "):
            flush(); buf = []
            category = clean(line[3:])
        elif re.match(r"\d+\.\s+\*\*", line):
            flush(); buf = [line]
        elif buf and line:
            buf.append(line)
    flush()
    return out


def parse_ledger(path):
    out = []
    if not os.path.exists(path):
        return out
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        e = json.loads(line)
        out.append(dict(
            candidate_id=e.get("candidate_id"), recorded_at=e.get("recorded_at"),
            run_id=e.get("run_id"), program_platform=e.get("program_platform"),
            program_handle=e.get("program_handle"), asset=e.get("asset"),
            vuln_class=e.get("vuln_class_claimed"), wing=e.get("wing"),
            gate_verdict=e.get("gate_verdict"),
            gate_reject_reason=e.get("gate_reject_reason"),
            verifier_type=e.get("verifier_type"),
            human_review_action=e.get("human_review_action"),
            program_verdict=e.get("program_verdict"),
            program_severity=e.get("program_severity"),
            bounty_usd=e.get("bounty_usd"), cost_infra_usd=e.get("cost_infra_usd"),
            is_example=1 if "EXAMPLE" in (e.get("candidate_id") or "") else 0,
            notes=e.get("notes")))
    return out


# --------------------------------------------------------------------- main
def main():
    conn = connect()
    init_schema(conn)
    for t in ("projects", "vault_entries", "ledger_entries", "metrics",
              "evidence"):
        conn.execute(f"DELETE FROM {t}")

    conn.executemany(
        "INSERT INTO projects (slug,name,tagline,summary,skills,status,is_hero,"
        "visibility,repo_url,note,attribution) VALUES (:slug,:name,:tagline,"
        ":summary,:skills,:status,:is_hero,:visibility,:repo_url,:note,"
        ":attribution)",
        [dict(p, attribution=p.get("attribution")) for p in PROJECTS])

    # v1.1: one `doc` Evidence row per project with a repository — the repo
    # itself, whose existence the 2026-11-25 project audit verified.
    conn.executemany(
        "INSERT INTO evidence (project_slug,type,url,note,recorded_at) "
        "VALUES (:slug,'doc',:repo_url,:note,'2026-11-25')",
        [dict(slug=p["slug"], repo_url=p["repo_url"],
              note="GitHub repository — existence verified in the "
                   "2026-11-25 project audit")
         for p in PROJECTS if p.get("repo_url")])

    vault = []
    vault += parse_payouts(os.path.join(VAULT, "payouts", "notable-payouts.md"))
    vault += parse_numbered(os.path.join(VAULT, "writeups", "INDEX.md"), "writeup")
    vault += parse_tips(os.path.join(VAULT, "tips", "TIPS-AND-TRICKS.md"))
    vault += parse_research(os.path.join(VAULT, "research", "INDEX.md"))
    # v1.1 contract fields: every vault row was verified against its source
    # on 2026-11-25 (checked_at); verification label = documented (source-
    # verified, not hands-on tested); tags seed from the entry's category.
    conn.executemany(
        "INSERT INTO vault_entries (kind,title,category,program,summary,amount_usd,"
        "source_url,verified,checked_at,verification,tags) VALUES (:kind,:title,"
        ":category,:program,:summary,:amount_usd,:source_url,:verified,"
        "'2026-11-25','documented',:tags)",
        [dict(v, tags=json.dumps([v["category"]] if v.get("category") else []))
         for v in vault])

    ledger = parse_ledger(LAB_LEDGER)
    if ledger:
        conn.executemany(
            "INSERT INTO ledger_entries (candidate_id,recorded_at,run_id,"
            "program_platform,program_handle,asset,vuln_class,wing,gate_verdict,"
            "gate_reject_reason,verifier_type,human_review_action,program_verdict,"
            "program_severity,bounty_usd,cost_infra_usd,is_example,notes) VALUES "
            "(:candidate_id,:recorded_at,:run_id,:program_platform,:program_handle,"
            ":asset,:vuln_class,:wing,:gate_verdict,:gate_reject_reason,"
            ":verifier_type,:human_review_action,:program_verdict,:program_severity,"
            ":bounty_usd,:cost_infra_usd,:is_example,:notes)", ledger)

    conn.commit()
    by_kind = {}
    for v in vault:
        by_kind[v["kind"]] = by_kind.get(v["kind"], 0) + 1
    total_payouts = sum(v["amount_usd"] or 0 for v in vault if v["kind"] == "payout")
    print(f"projects: {len(PROJECTS)}")
    print(f"vault_entries: {len(vault)} by kind: {by_kind}")
    print(f"verified payouts total: ${total_payouts:,.0f}")
    print(f"ledger_entries: {len(ledger)} (examples flagged)")
    conn.close()


if __name__ == "__main__":
    main()
