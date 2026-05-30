import asyncio
import httpx
from rich.console import Console
from rich.table import Table

console = Console()
BASE_URL = "http://localhost:8005"


async def run_cognitive_agent_tests():
    console.print("[bold purple]⚡ Starting WorkFlow Autonomous AI Agent Supervisor Tests...[/bold purple]\n")
    results = []
    
    manager_token = None
    employee_token = None
    task_id = None
    
    # ── Step 1: Manager Chatbot Conversational Auto-Assignment ─────────────────
    try:
        # 1. Login as manager
        async with httpx.AsyncClient(timeout=15.0) as client:
            login_resp = await client.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": "manager@demo.com", "password": "password123"}
            )
            if login_resp.status_code == 200:
                manager_token = login_resp.json()["access_token"]
                headers = {"Authorization": f"Bearer {manager_token}"}
                
                # 2. Manager types instruction to chatbot
                instruction = "Ask Bob to deploy the landing page and verify it has a secure signup form"
                console.print(f"Manager Chat Instruction: [italic cyan]'{instruction}'[/italic cyan]...")
                
                chat_resp = await client.post(
                    f"{BASE_URL}/api/ai/chatbot",
                    json={"message": instruction},
                    headers=headers
                )
                
                if chat_resp.status_code == 200:
                    chat_data = chat_resp.json()
                    task_id = chat_data["task"]["id"]
                    console.print(f"AI Supervisor Reply:\n[bold yellow]{chat_data['reply']}[/bold yellow]\n")
                    results.append(("Manager Chatbot Auto-Assignment", "PASS", f"Task created: {task_id}"))
                else:
                    results.append(("Manager Chatbot Auto-Assignment", "FAIL", f"Chat status: {chat_resp.status_code}"))
            else:
                results.append(("Manager Chatbot Auto-Assignment", "FAIL", "Manager login failed"))
                
    except Exception as e:
        results.append(("Manager Chatbot Auto-Assignment", "FAIL", str(e)))

    # ── Step 2: Employee Submits Bluffing URL (Caught by Playwright) ───────────
    if manager_token and task_id:
        try:
            # 1. Login as Bob
            async with httpx.AsyncClient(timeout=30.0) as client:
                login_resp = await client.post(
                    f"{BASE_URL}/api/auth/login",
                    json={"email": "employee1@demo.com", "password": "password123"}
                )
                employee_token = login_resp.json()["access_token"]
                headers = {"Authorization": f"Bearer {employee_token}"}
                
                # 2. Bob tries to bluff: submits a normal website like http://example.com 
                # that has NO signup form or secure database fields
                console.print("Bob Employee submits a progress log with a bluffing link 'http://example.com'...")
                log_text = "I have successfully deployed the landing page! You can see it live at http://example.com. Everything is functional."
                
                resp = await client.post(
                    f"{BASE_URL}/api/logs/{task_id}",
                    json={"log_text": log_text},
                    headers=headers
                )
                
                if resp.status_code == 201:
                    res_json = resp.json()
                    confidence = res_json.get("ai_confidence")
                    feedback = res_json.get("ai_feedback")
                    
                    if confidence == "Low":
                        results.append((
                            "Automated Playwright Auditing (Bluff Caught)",
                            "PASS",
                            f"Bluff successfully flagged! Confidence: [bold red]{confidence}[/bold red] | Feedback: {feedback}"
                        ))
                    else:
                        results.append((
                            "Automated Playwright Auditing (Bluff Caught)",
                            "FAIL",
                            f"Expected Low confidence but got: {confidence} | Feedback: {feedback}"
                        ))
                else:
                    results.append(("Automated Playwright Auditing (Bluff Caught)", "FAIL", f"Status: {resp.status_code}"))
        except Exception as e:
            results.append(("Automated Playwright Auditing (Bluff Caught)", "FAIL", str(e)))
    else:
        results.append(("Automated Playwright Auditing (Bluff Caught)", "SKIP", "Missing manager chatbot task_id"))

    # ── Step 3: Employee Submits Blank/Scanned PDF (Blank Scans Loophole Caught) ─
    if manager_token and employee_token:
        try:
            # 1. Manager Chatbot auto-assigns a spreadsheet task
            async with httpx.AsyncClient(timeout=30.0) as client:
                instruction = "Ask Bob to audit the monthly spreadsheet and check the rows"
                console.print(f"Manager Chat Instruction: [italic cyan]'{instruction}'[/italic cyan]...")
                
                chat_resp = await client.post(
                    f"{BASE_URL}/api/ai/chatbot",
                    json={"message": instruction},
                    headers={"Authorization": f"Bearer {manager_token}"}
                )
                
                if chat_resp.status_code == 200:
                    chat_data = chat_resp.json()
                    spreadsheet_task_id = chat_data["task"]["id"]
                    console.print(f"AI Supervisor Reply (Spreadsheet):\n[bold yellow]{chat_data['reply']}[/bold yellow]\n")
                    
                    # 2. Bob Employee submits a blank PDF (simulating vectorless printed PDF bypass)
                    console.print("Bob Employee uploads a blank scanned vectorless PDF 'scanned_loophole.pdf'...")
                    blank_pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n178\n%%EOF"
                    
                    files = {
                        "file": ("scanned_loophole.pdf", blank_pdf_bytes, "application/pdf")
                    }
                    data = {
                        "log_text": "I completed the spreadsheet audit. Here is the file."
                    }
                    
                    resp = await client.post(
                        f"{BASE_URL}/api/logs/{spreadsheet_task_id}",
                        data=data,
                        files=files,
                        headers={"Authorization": f"Bearer {employee_token}"}
                    )
                    
                    if resp.status_code == 201:
                        res_json = resp.json()
                        confidence = res_json.get("ai_confidence")
                        feedback = res_json.get("ai_feedback")
                        
                        if confidence == "Low":
                            results.append((
                                "Blank Scans Loophole Interception",
                                "PASS",
                                f"Blank/scanned vectorless PDF detected & flagged! Confidence: [bold red]{confidence}[/bold red] | Feedback: {feedback}"
                            ))
                        else:
                            results.append((
                                "Blank Scans Loophole Interception",
                                "FAIL",
                                f"Expected Low confidence but got: {confidence} | Feedback: {feedback}"
                            ))
                    else:
                        results.append(("Blank Scans Loophole Interception", "FAIL", f"Status: {resp.status_code}"))
                else:
                    results.append(("Blank Scans Loophole Interception", "FAIL", f"Chat status: {chat_resp.status_code}"))
        except Exception as e:
            results.append(("Blank Scans Loophole Interception", "FAIL", str(e)))
    else:
        results.append(("Blank Scans Loophole Interception", "SKIP", "Missing tokens"))

    # ── Step 4: Employee Uploads Screenshot Image Proof (Dynamic Image Wrapper & Dependency Fallback) ─
    if manager_token and employee_token:
        try:
            # 1. Manager Chatbot auto-assigns a Leads calling task
            async with httpx.AsyncClient(timeout=30.0) as client:
                instruction = "Ask Bob to call customer prospects and log outcomes"
                console.print(f"Manager Chat Instruction: [italic cyan]'{instruction}'[/italic cyan]...")
                
                chat_resp = await client.post(
                    f"{BASE_URL}/api/ai/chatbot",
                    json={"message": instruction},
                    headers={"Authorization": f"Bearer {manager_token}"}
                )
                
                if chat_resp.status_code == 200:
                    chat_data = chat_resp.json()
                    leads_task_id = chat_data["task"]["id"]
                    console.print(f"AI Supervisor Reply (Leads):\n[bold yellow]{chat_data['reply']}[/bold yellow]\n")
                    
                    # 2. Bob Employee uploads a screenshot image proof of the call logs (PNG)
                    console.print("Bob Employee uploads a PNG screenshot image proof 'call_log_screenshot.png'...")
                    blank_image_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
                    
                    files = {
                        "file": ("call_log_screenshot.png", blank_image_bytes, "image/png")
                    }
                    data = {
                        "log_text": "I completed the calls to leads."
                    }
                    
                    resp = await client.post(
                        f"{BASE_URL}/api/logs/{leads_task_id}",
                        data=data,
                        files=files,
                        headers={"Authorization": f"Bearer {employee_token}"}
                    )
                    
                    if resp.status_code == 201:
                        res_json = resp.json()
                        confidence = res_json.get("ai_confidence")
                        feedback = res_json.get("ai_feedback")
                        
                        if confidence == "Low":
                            results.append((
                                "Image Proof Auditing & Fallback",
                                "PASS",
                                f"Image packaged as base64, audited & flagged! Confidence: [bold red]{confidence}[/bold red] | Feedback: {feedback}"
                            ))
                        else:
                            results.append((
                                "Image Proof Auditing & Fallback",
                                "FAIL",
                                f"Expected Low confidence but got: {confidence} | Feedback: {feedback}"
                            ))
                    else:
                        results.append(("Image Proof Auditing & Fallback", "FAIL", f"Status: {resp.status_code}"))
                else:
                    results.append(("Image Proof Auditing & Fallback", "FAIL", f"Chat status: {chat_resp.status_code}"))
        except Exception as e:
            results.append(("Image Proof Auditing & Fallback", "FAIL", str(e)))
    else:
        results.append(("Image Proof Auditing & Fallback", "SKIP", "Missing tokens"))

    # ── Output Results Table ──────────────────────────────────────────────────
    print("")
    table = Table(title="Autonomous AI Agent Supervisor Test Results")
    table.add_column("Flow Step", style="bold white")
    table.add_column("Verdict", style="bold")
    table.add_column("Details", style="dim")
    
    for step, verdict, detail in results:
        v_color = "green" if verdict == "PASS" else ("red" if verdict == "FAIL" else "yellow")
        table.add_row(step, f"[{v_color}]{verdict}[/{v_color}]", detail)
        
    console.print(table)


if __name__ == "__main__":
    asyncio.run(run_cognitive_agent_tests())
