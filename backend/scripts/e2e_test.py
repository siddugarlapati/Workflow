"""
WorkFlow — Automated End-to-End Test Script
===========================================
Simulates the entire user lifecycle, authenticating roles, assigning tasks,
submitting work logs, verifying live AI response, and generating manager summaries.
Run with: uv run python scripts/e2e_test.py
"""
import asyncio
import sys
import httpx
from rich.console import Console
from rich.table import Table

console = Console()
BASE_URL = "http://localhost:8005"

async def run_e2e_test() -> None:
    console.print("[bold purple]⚡ Starting WorkFlow E2E Suite...[/bold purple]\n")
    
    results = []
    manager_token = None
    employee_token = None
    task_id = None
    
    # ── Step 1: Manager Authentication ─────────────────────────────────────────
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": "manager@demo.com", "password": "password123"}
            )
            if resp.status_code == 200:
                manager_token = resp.json()["access_token"]
                results.append(("Manager Authentication", "PASS", "Successfully logged in as manager@demo.com"))
            else:
                results.append(("Manager Authentication", "FAIL", f"Status code: {resp.status_code}"))
    except Exception as e:
        results.append(("Manager Authentication", "FAIL", str(e)))

    # ── Step 2: Employee Authentication ────────────────────────────────────────
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": "employee1@demo.com", "password": "password123"}
            )
            if resp.status_code == 200:
                employee_token = resp.json()["access_token"]
                results.append(("Employee Authentication", "PASS", "Successfully logged in as employee1@demo.com"))
            else:
                results.append(("Employee Authentication", "FAIL", f"Status code: {resp.status_code}"))
    except Exception as e:
        results.append(("Employee Authentication", "FAIL", str(e)))

    # ── Step 3: Manager Assigns Task ───────────────────────────────────────────
    if manager_token:
        try:
            headers = {"Authorization": f"Bearer {manager_token}"}
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Dynamically fetch employee UUID
                emp_resp = await client.get(f"{BASE_URL}/api/auth/employees", headers=headers)
                employee_id = None
                if emp_resp.status_code == 200:
                    for emp in emp_resp.json():
                        if emp["email"] == "employee1@demo.com":
                            employee_id = emp["id"]
                            break
                
                if not employee_id:
                    employee_id = "2b9213bc-3294-4395-8178-0e95c1c0451e" # Fallback

                task_data = {
                    "title": "E2E Automated Task - Logistics Reconciliation",
                    "description": "Cross-reference transit records from yesterday's shipments in warehouse B.",
                    "assigned_to": employee_id,
                    "priority": "high",
                    "deadline": "2026-06-05T17:00:00",
                }
                resp = await client.post(f"{BASE_URL}/api/tasks/", json=task_data, headers=headers)
                if resp.status_code == 201:
                    task_id = resp.json()["id"]
                    results.append(("Manager Create Task", "PASS", f"Created task: {task_id}"))
                else:
                    results.append(("Manager Create Task", "FAIL", f"Status: {resp.status_code} - {resp.text}"))
        except Exception as e:
            results.append(("Manager Create Task", "FAIL", str(e)))
    else:
        results.append(("Manager Create Task", "SKIP", "Missing manager authentication token"))

    # ── Step 4: Employee Fetch Tasks ──────────────────────────────────────────
    if employee_token:
        try:
            headers = {"Authorization": f"Bearer {employee_token}"}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{BASE_URL}/api/tasks/mine", headers=headers)
                if resp.status_code == 200:
                    tasks = resp.json()["tasks"]
                    found = any(t["id"] == task_id for t in tasks)
                    if found:
                        results.append(("Employee Task Verification", "PASS", "Created task appeared in employee dashboard"))
                    else:
                        results.append(("Employee Task Verification", "FAIL", "Task was not found in employee assigned list"))
                else:
                    results.append(("Employee Task Verification", "FAIL", f"Status code: {resp.status_code}"))
        except Exception as e:
            results.append(("Employee Task Verification", "FAIL", str(e)))
    else:
        results.append(("Employee Task Verification", "SKIP", "Missing employee authentication token"))

    # ── Step 5: Employee Submits Work Log ──────────────────────────────────────
    if employee_token and task_id:
        try:
            headers = {"Authorization": f"Bearer {employee_token}"}
            async with httpx.AsyncClient(timeout=15.0) as client:
                log_data = {
                    "log_text": "Completed reconciliation for all 42 shipments in Warehouse B. Discovered 2 minor transit time discrepancies and logged them in sheet. Total time spent was 3 hours."
                }
                resp = await client.post(f"{BASE_URL}/api/logs/{task_id}", json=log_data, headers=headers)
                if resp.status_code == 201:
                    res_json = resp.json()
                    confidence = res_json.get("ai_confidence")
                    feedback = res_json.get("ai_feedback")
                    results.append((
                        "Employee Submit Work Log (AI verify)", 
                        "PASS", 
                        f"Log verified! Confidence: [bold cyan]{confidence}[/bold cyan] | Feedback: {feedback}"
                    ))
                else:
                    results.append(("Employee Submit Work Log (AI verify)", "FAIL", f"Status: {resp.status_code}"))
        except Exception as e:
            results.append(("Employee Submit Work Log (AI verify)", "FAIL", str(e)))
    else:
        results.append(("Employee Submit Work Log (AI verify)", "SKIP", "Missing authentication or task id"))

    # ── Step 6: Manager Requests AI Summary ────────────────────────────────────
    if manager_token:
        try:
            headers = {"Authorization": f"Bearer {manager_token}"}
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(f"{BASE_URL}/api/ai/summary", headers=headers)
                if resp.status_code == 200:
                    summary = resp.json()["summary"]
                    results.append((
                        "Manager AI Summary Briefing",
                        "PASS",
                        f"Briefing generated successfully!\n[dim]'{summary}'[/dim]"
                    ))
                else:
                    results.append(("Manager AI Summary Briefing", "FAIL", f"Status: {resp.status_code}"))
        except Exception as e:
            results.append(("Manager AI Summary Briefing", "FAIL", str(e)))
    else:
        results.append(("Manager AI Summary Briefing", "SKIP", "Missing manager authentication token"))

    # ── Output Results Table ──────────────────────────────────────────────────
    print("")
    table = Table(title="WorkFlow E2E Integration Suite Results")
    table.add_column("Flow Step", style="bold white")
    table.add_column("Verdict", style="bold")
    table.add_column("Details", style="dim")

    for step, verdict, detail in results:
        v_color = "green" if verdict == "PASS" else ("red" if verdict == "FAIL" else "yellow")
        table.add_row(step, f"[{v_color}]{verdict}[/{v_color}]", detail)

    console.print(table)
    
    # Return exit code based on failures
    has_failed = any(verdict == "FAIL" for _, verdict, _ in results)
    if has_failed:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
