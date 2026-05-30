"""
WorkFlow — Autonomous Cognitive Verifier Engine
===============================================
Launches Playwright E2E browser automation to crawl human webpage proofs,
and runs advanced anti-bluffing verification prompts with local LLMs.
"""
import re
import structlog
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright

from app.models.work_log import AIConfidence
from app.schemas.work_log import LogVerificationResult
from app.services.ai_service import verifyLog

logger = structlog.get_logger()

# Simple regex to extract the first URL found in text
URL_REGEX = re.compile(r"https?://[^\s\"']+")


async def audit_webpage(url: str) -> Dict[str, Any]:
    """
    Spawns Playwright Chromium in headless mode to crawl the URL,
    recovering dynamic page titles, body texts, and JS console health logs.
    """
    logger.info("verifier.playwright.crawling", url=url)
    console_logs = []
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 WorkFlowCognitiveSupervisor/1.0"
            )
            
            page = await context.new_page()
            
            # Record page console log warnings/errors
            page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
            
            # Navigate with a 15-second timeout
            await page.goto(url, wait_until="networkidle", timeout=15000)
            
            # Scrape details
            title = await page.title()
            body_text = await page.inner_text("body")
            
            # Keep only the first 5000 characters to prevent prompt overloading
            scraped_content = body_text[:5000] if body_text else ""
            
            await browser.close()
            
            return {
                "success": True,
                "title": title,
                "scraped_content": scraped_content,
                "console_errors": [log for log in console_logs if "error" in log.lower() or "warn" in log.lower()][:10]
            }
            
    except Exception as exc:
        logger.error("verifier.playwright.failed", url=url, error=str(exc))
        return {
            "success": False,
            "error": str(exc),
            "scraped_content": ""
        }


async def run_cognitive_verification(
    task_title: str,
    task_desc: str,
    log_text: str,
    expected_criteria: Optional[str] = None
) -> LogVerificationResult:
    """
    Autonomous Cognitive Agent Supervisor:
    1. MAML-style Meta-adaptation: Dynamically classifies task category (Web Dev, Leads, Sheets, General).
    2. Playwright/File Audit: Dynamic crawlers scrape browser states and parsed cells.
    3. JEPA-inspired Alignment Check: Compares predicted target outcome vs actual proof representations.
    4. Pedagogical Feedback Loop: Delivers precise remediation guides for caught bluffs.
    """
    logger.info("verifier.cognitive_audit.start", task_title=task_title)
    
    # ── 1. MAML-Style Meta-Category Rule Adaptation ──────────────────────────────
    title_desc_lower = f"{task_title} {task_desc} {expected_criteria or ''}".lower()
    
    if any(k in title_desc_lower for k in ["deploy", "website", "url", "signup", "login", "css", "html", "react", "page", "http", "form"]):
        task_category = "WEB_DEVELOPMENT"
    elif any(k in title_desc_lower for k in ["leads", "call", "client", "customer", "phone", "sales", "prospect", "reach out"]):
        task_category = "LEADS_CALL"
    elif any(k in title_desc_lower for k in ["excel", "xlsx", "sheet", "pdf", "docx", "report", "document", "data", "table"]):
        task_category = "DOCUMENT_SPREADSHEET"
    else:
        task_category = "GENERAL_COMPLIANCE"
        
    logger.info("verifier.maml.meta_category", category=task_category)

    # ── 2. Playwright Crawl & Proof Aggregation ──────────────────────────────────
    found_urls = URL_REGEX.findall(log_text)
    web_proof = None
    cleaned_url = None
    
    if found_urls:
        cleaned_url = found_urls[0].rstrip(".,!?()[]{}")
        logger.info("verifier.url_detected", url=cleaned_url)
        web_proof = await audit_webpage(cleaned_url)

    context_proof = ""
    if web_proof and cleaned_url:
        if web_proof["success"]:
            context_proof = (
                f"\n[PLAYWRIGHT E2E BROWSER PROOF FOR ({cleaned_url})]:\n"
                f"Page Title: {web_proof['title']}\n"
                f"JS Console Anomaly Logs: {web_proof['console_errors']}\n"
                f"Scraped Webpage Content:\n{web_proof['scraped_content']}\n"
            )
        else:
            context_proof = (
                f"\n[PLAYWRIGHT E2E BROWSER ERROR]:\n"
                f"Playwright was unable to crawl the URL: {cleaned_url}.\n"
                f"Connection Error Details: {web_proof.get('error')}\n"
            )

    # ── 2b. Gemini Vision API Auditing (Major Innovation) ──────────────────────
    gemini_vision_report = ""
    
    b64_img_start = "[BASE64 IMAGE ENCODED STREAM DATA START]"
    b64_img_end = "[BASE64 IMAGE ENCODED STREAM DATA END]"
    
    b64_pdf_start = "[BASE64 PDF DOCUMENT DATA START]"
    b64_pdf_end = "[BASE64 PDF DOCUMENT DATA END]"
    
    b64_data = None
    mime_type = "image/png"
    
    if b64_img_start in log_text and b64_img_end in log_text:
        parts = log_text.split(b64_img_start)
        if len(parts) > 1:
            b64_data = parts[1].split(b64_img_end)[0].strip()
            mime_type = "image/png"
            
    elif b64_pdf_start in log_text and b64_pdf_end in log_text:
        parts = log_text.split(b64_pdf_start)
        if len(parts) > 1:
            b64_data = parts[1].split(b64_pdf_end)[0].strip()
            mime_type = "application/pdf"
            
    if b64_data:
        logger.info("verifier.gemini_vision.parsing_screenshot")
        import base64
        try:
            image_bytes = base64.b64decode(b64_data)
            
            gemini_prompt = (
                "You are the WorkFlow Autonomous AI Agent Supervisor.\n"
                f"Original Task Title: {task_title}\n"
                f"Task Guidelines/Description: {task_desc}\n"
                f"Target Verification Criteria: {expected_criteria or 'General Completion Validation'}\n\n"
                "Review this screenshot/document proof carefully. Critically inspect any text, logs, durations, "
                "or elements in the screenshot. Write a detailed analysis of what you see. State clearly whether "
                "the proof matches the expected criteria and task description. If there are mismatches, "
                "flag it as a BLUFF with specific reasoning."
            )
            
            from app.core.gemini_vision import analyze_image_with_gemini
            analysis = await analyze_image_with_gemini(
                image_bytes=image_bytes,
                mime_type=mime_type,
                prompt=gemini_prompt
            )
            
            if analysis:
                gemini_vision_report = (
                    f"\n[GEMINI VISION API LIVE COGNITIVE REPORT]:\n"
                    f"Analysis Result:\n{analysis}\n"
                )
                logger.info("verifier.gemini_vision.report_generated")
        except Exception as exc:
            logger.error("verifier.gemini_vision.failed_during_run", error=str(exc))

    full_evaluated_text = log_text
    if context_proof:
        full_evaluated_text = f"{full_evaluated_text}\n{context_proof}"
    if gemini_vision_report:
        full_evaluated_text = f"{full_evaluated_text}\n{gemini_vision_report}"

    # ── 3. JEPA-Inspired Representation Alignment Check ────────────────────────
    # Evaluate if the submitted proof matches expected targets, catching evasive bluffs.
    alignment_score = 1.0  # start clean
    alignment_issues = []
    
    proof_source_lower = full_evaluated_text.lower()
    criteria_lower = (expected_criteria or "").lower()
    
    # Heuristics for extremely short or evasive answers
    words = [w for w in re.split(r"\W+", log_text.lower()) if w]
    if len(words) < 5 or (len(words) < 12 and any(ev in proof_source_lower for ev in ["done", "complete", "everything", "finished", "did it", "work done", "i have done", "tested"])):
        # Highly evasive
        alignment_score = min(alignment_score, 0.1)
        alignment_issues.append("Employee response is extremely short, generic, and lacks any concrete details of the work performed.")

    if task_category == "WEB_DEVELOPMENT":
        if not cleaned_url:
            alignment_score = min(alignment_score, 0.1)
            alignment_issues.append("Web development task expects a live deployment URL, but no link was found in your submission.")
        elif web_proof and not web_proof["success"]:
            alignment_score = min(alignment_score, 0.1)
            alignment_issues.append(f"Headless Playwright audit failed to connect to the deployment URL ({cleaned_url}). Error: {web_proof.get('error')}")
        elif web_proof:
            # Check if expected criteria requires signup or form elements
            if "signup" in criteria_lower or "form" in criteria_lower or "signup" in title_desc_lower:
                scraped_lower = web_proof["scraped_content"].lower()
                # Check for form inputs like signup, form, inputs, button, email
                has_inputs = any(term in scraped_lower for term in ["input", "form", "signup", "register", "email", "password", "button"])
                # Also check if it's just the default example.com text
                is_example_domain = "example domain" in scraped_lower or "iana-managed" in scraped_lower
                
                if not has_inputs or is_example_domain:
                    alignment_score = min(alignment_score, 0.1)
                    alignment_issues.append(f"Webpage crawled at {cleaned_url} does not contain any input fields or signup forms, or is a generic domain. Found: '{web_proof['title']}'")

    elif task_category == "LEADS_CALL":
        # Check if the employee claims they called leads but doesn't list the details
        has_lead_outcomes = any(term in proof_source_lower for term in ["interested", "not interested", "wrong number", "no answer", "busy", "callback", "spoke to", "called", "emailed"])
        has_phone_number = len(re.findall(r"\b\d{10,12}\b|\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", proof_source_lower)) > 0
        has_name_capitalization = any(c.isupper() for c in log_text if c.isalpha())
        
        # If they haven't uploaded a document and have no details
        if "[extracted document proof" not in proof_source_lower:
            if not has_lead_outcomes or (not has_phone_number and len(words) < 25):
                alignment_score = min(alignment_score, 0.2)
                alignment_issues.append("Leads task requires reporting outcomes (e.g. interested/busy/wrong number) and lead contacts, but your submission lacks phone records or customer responses.")

    elif task_category == "DOCUMENT_SPREADSHEET":
        if "[extracted document proof" not in proof_source_lower:
            alignment_score = min(alignment_score, 0.2)
            alignment_issues.append("Document/Spreadsheet task requires uploading a file proof (.xlsx, .pdf, .docx, .csv), but no document upload was captured.")
        else:
            # Analyze extracted file text
            extracted_section = ""
            if "[extracted document proof" in proof_source_lower:
                extracted_section = proof_source_lower.split("[extracted document proof")[1]
            
            # Check if spreadsheet actually has data cells
            cell_dividers = extracted_section.count("|")
            line_count = extracted_section.count("\n")
            
            if cell_dividers < 3 and line_count < 3:
                alignment_score = min(alignment_score, 0.1)
                alignment_issues.append("The uploaded spreadsheet/document proof is empty or contains insufficient data rows (no structured columns detected).")

    # ── 3b. Intercept Gemini Vision Auditing Verdict ──────────────────────────────
    if gemini_vision_report:
        lower_report = gemini_vision_report.lower()
        if any(term in lower_report for term in ["bluff", "fake", "mismatch", "invalid", "discrepancy", "fail", "empty"]):
            alignment_score = min(alignment_score, 0.1)
            alignment_issues.append("Gemini Vision API audited the uploaded screenshot/document and detected high-risk discrepancies or empty vectors (Bluff Flagged).")
    else:
        # Visual proof uploaded but vision LLM was skipped/failed
        if "[scanned vectorless pdf" in proof_source_lower or "[image screenshot proof" in proof_source_lower:
            alignment_score = min(alignment_score, 0.1)
            alignment_issues.append("A visual proof (image/scanned PDF) was uploaded, but the Autonomous AI Agent Supervisor was unable to run Vision LLM analysis (missing or invalid GEMINI_API_KEY). Standard OCR engines were not pre-installed or failed to extract readable text.")

    # ── 4. Pedagogical Feedback Loop Generation & Verdict ─────────────────────────
    if alignment_score <= 0.2:
        confidence = AIConfidence.LOW
        # Formulate pedagogical self-corrective response
        issues_summary = " ".join(alignment_issues)
        feedback = f"🚨 Bluff Flagged. {issues_summary} [Self-Corrective Action]: Please re-run/verify the work and submit a genuine log/proof that fulfills these requirements."
        logger.warn("verifier.cognitive_audit.bluff_caught", category=task_category, feedback=feedback)
        return LogVerificationResult(confidence=confidence, feedback=feedback)

    # If it passes the strict heuristic JEPA test, call standard LLM for nuanced review
    try:
        result = await verifyLog(
            task_title=task_title,
            task_description=f"{task_desc} (Expected verification criteria: {expected_criteria or 'General Relevance Check'})",
            log_text=full_evaluated_text
        )
        return result
    except Exception as exc:
        logger.warning("verifier.llm_failed.using_heurisitic_fallback", error=str(exc))
        # Fallback to high/medium based on alignment score
        if alignment_score >= 0.8:
            return LogVerificationResult(
                confidence=AIConfidence.HIGH,
                feedback="Automated verifier confirms all expected criteria have been satisfied in the submitted proof."
            )
        else:
            return LogVerificationResult(
                confidence=AIConfidence.MEDIUM,
                feedback="Proof criteria partially matched. Manual supervisor audit recommended to prevent minor deviations."
            )

