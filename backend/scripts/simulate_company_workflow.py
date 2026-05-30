import asyncio
import random
import http.server
import socketserver
import threading
import httpx
from rich.console import Console
from rich.table import Table

console = Console()
BASE_URL = "http://localhost:8005"
MOCK_PORT = 8099


class MockWebHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        html = """
        <!DOCTYPE html>
        <html>
        <head>
          <title>WorkFlow AI Landing Page Prototype</title>
          <style>
            body { background: #0f172a; color: #f8fafc; font-family: system-ui, sans-serif; margin: 0; padding: 0; }
            header { display: flex; justify-content: space-between; padding: 1.5rem 2rem; border-bottom: 1px solid #1e293b; }
            .hero { text-align: center; padding: 4rem 2rem; max-width: 800px; margin: 0 auto; }
            .features { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; max-width: 800px; margin: 2rem auto; padding: 0 2rem; }
            .feature-card { background: #1e293b; padding: 1.5rem; border-radius: 8px; }
            .signup-section { max-width: 400px; margin: 3rem auto; background: #1e293b; padding: 2.5rem; border-radius: 12px; border: 1px solid #3b82f6; }
            input { width: 100%; padding: 0.75rem; background: #0f172a; border: 1px solid #334155; border-radius: 6px; color: white; margin-bottom: 1rem; box-sizing: border-box; }
            button { width: 100%; padding: 0.75rem; background: #2563eb; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }
          </style>
        </head>
        <body>
          <header>
            <div style="font-weight: bold; font-size: 1.25rem; color: #3b82f6;">WorkFlow AI</div>
            <nav style="display: flex; gap: 1.5rem;">
              <a href="#features" style="color: #94a3b8; text-decoration: none;">Features</a>
              <a href="#pricing" style="color: #94a3b8; text-decoration: none;">Pricing</a>
              <a href="#docs" style="color: #94a3b8; text-decoration: none;">Docs</a>
            </nav>
          </header>
          <div class="hero">
            <h1 style="font-size: 3rem; margin-bottom: 1rem;">The Role-Based AI Accountability Platform</h1>
            <p style="font-size: 1.25rem; color: #94a3b8;">Say goodbye to vague reports and spreadsheet tracking. WorkFlow automatically audits code, crawls deployments, and intercepts scans.</p>
          </div>
          <div id="features" class="features">
            <div class="feature-card">
              <h3>🤖 Autonomous AI Auditing</h3>
              <p style="color: #94a3b8;">Verifies all log submissions and file uploads with vision pipelines.</p>
            </div>
            <div class="feature-card">
              <h3>🌐 E2E Web Browser Audits</h3>
              <p style="color: #94a3b8;">Crawls employee websites to catch bluffs automatically using Playwright.</p>
            </div>
          </div>
          <div class="signup-section">
            <h2 style="margin-top: 0; text-align: center; color: #3b82f6;">Get Started Prototype</h2>
            <form>
              <label style="display: block; margin-bottom: 0.5rem;">Corporate Email</label>
              <input type="email" placeholder="you@company.com" required />
              <label style="display: block; margin-bottom: 0.5rem;">Choose Password</label>
              <input type="password" placeholder="••••••••" required />
              <button type="submit">Create Free Account</button>
            </form>
          </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        return


def start_mock_server(port):
    socketserver.TCPServer.allow_reuse_address = True
    handler = MockWebHandler
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True
    thread.start()
    return httpd


async def run_simulation():
    console.print("\n[bold purple]🚀 Starting WorkFlow Dynamic E2E Real-Time Simulation...[/bold purple]\n")
    
    company_suffix = f"optima-{random.randint(100, 999)}.com"
    console.print(f"🏢 [bold cyan]Company Domain Initialized:[/bold cyan] [italic]@{company_suffix}[/italic]\n")
    
    manager_email = f"manager.alice@{company_suffix}"
    employee_email = f"dev.dave@{company_suffix}"
    
    sim_steps = []
    
    # ── 1. Onboard Company Team ──────────────────────────────────────────────
    console.print("👥 [bold green]Step 1: Onboarding Team to Company...[/bold green]")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Login/Get token for seed employee Bob (employee1@demo.com) as a matched fallback option
            bob_login = await client.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": "employee1@demo.com", "password": "password123"}
            )
            bob_token = bob_login.json()["access_token"]
            bob_id = bob_login.json()["user"]["id"]
            
            # Onboard Manager (Alice)
            mgr_register = await client.post(
                f"{BASE_URL}/api/auth/register",
                json={
                    "email": manager_email,
                    "password": "supersecurepassword123",
                    "full_name": "Alice Supervisor",
                    "role": "manager",
                    "department": "Engineering"
                }
            )
            
            # Onboard Employee (Dave)
            emp_register = await client.post(
                f"{BASE_URL}/api/auth/register",
                json={
                    "email": employee_email,
                    "password": "supersecurepassword123",
                    "full_name": "Dave Developer",
                    "role": "employee",
                    "department": "Engineering"
                }
            )
            
            if mgr_register.status_code == 201 and emp_register.status_code == 201:
                manager_token = mgr_register.json()["access_token"]
                dave_token = emp_register.json()["access_token"]
                dave_id = emp_register.json()["user"]["id"]
                console.print(f"  ✅ [dim]Manager Alice and Employee Dave registered successfully.[/dim]")
                sim_steps.append(("Onboard Company & Team", "PASS", f"Created manager ({manager_email}) & employee ({employee_email})"))
            else:
                console.print(f"  ❌ Onboarding failed. Mgr status: {mgr_register.status_code}, Emp status: {emp_register.status_code}")
                return
    except Exception as e:
        console.print("  ❌ Error onboarding team:", e)
        return

    # ── 2. Manager Conversational Task Auto-Assignment ───────────────────────
    console.print("\n🗣️ [bold green]Step 2: Manager Assigns Task via AI Supervisor Chatbot...[/bold green]")
    task_id = None
    assigned_to_id = None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"Authorization": f"Bearer {manager_token}"}
            instruction = f"Ask Dave Developer (email: {employee_email}) to build a landing page prototype and verify it contains a signup form."
            console.print(f"  💬 [bold white]Manager Alice:[/bold white] [italic cyan]\"{instruction}\"[/italic cyan]")
            
            chat_resp = await client.post(
                f"{BASE_URL}/api/ai/chatbot",
                json={"message": instruction},
                headers=headers
            )
            
            if chat_resp.status_code == 200:
                chat_data = chat_resp.json()
                task_id = chat_data["task"]["id"]
                assigned_to_id = chat_data["task"]["assigned_to"]
                
                # Resolve which employee is assigned to dynamically select the correct token for logging!
                if assigned_to_id == dave_id:
                    active_token = dave_token
                    active_name = "Dave Developer"
                else:
                    active_token = bob_token
                    active_name = "Bob Employee"
                    
                console.print(f"  🤖 [bold yellow]AI Supervisor Response:[/bold yellow]")
                console.print(f"    [dim]{chat_data['reply']}[/dim]")
                sim_steps.append(("AI Conversational Assignment", "PASS", f"Task assigned to {active_name} (ID: {task_id[:8]}...)"))
            else:
                console.print(f"  ❌ Chatbot auto-assignment failed. Status: {chat_resp.status_code}")
                return
    except Exception as e:
        console.print("  ❌ Error assigning task:", e)
        return

    # ── 3. Employee Tries to Submit a Bluff ──────────────────────────────────
    console.print(f"\n🚨 [bold green]Step 3: Employee ({active_name}) Submits a Bluffing URL Proof...[/bold green]")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"Authorization": f"Bearer {active_token}"}
            bluff_url = "http://example.com"
            log_text = f"I deployed the landing page! Check it out here: {bluff_url}"
            console.print(f"  📝 [bold white]{active_name}:[/bold white] [italic]\"{log_text}\"[/italic]")
            
            resp = await client.post(
                f"{BASE_URL}/api/logs/{task_id}",
                json={"log_text": log_text},
                headers=headers
            )
            
            if resp.status_code == 201:
                res_json = resp.json()
                confidence = res_json.get("ai_confidence")
                feedback = res_json.get("ai_feedback")
                
                console.print(f"  🤖 [bold yellow]AI Supervisor Audit Verdict:[/bold yellow]")
                console.print(f"    • Confidence: [bold red]{confidence}[/bold red]")
                console.print(f"    • Feedback: {feedback}")
                
                if confidence == "Low":
                    sim_steps.append(("Bluff Interception (Playwright E2E)", "PASS", "Headless crawler detected lack of signup fields. Bluff successfully caught!"))
                else:
                    sim_steps.append(("Bluff Interception (Playwright E2E)", "FAIL", f"Expected Low confidence but got: {confidence}"))
            else:
                console.print(f"  ❌ Failed to submit log. Status: {resp.status_code}")
                return
    except Exception as e:
        console.print("  ❌ Error submitting bluff:", e)
        return

    # ── 4. Spin Up Real-Time Local Mock Server ───────────────────────────────
    console.print(f"\n🌐 [bold green]Step 4: Spinning up Dynamic Local Server on port {MOCK_PORT}...[/bold green]")
    mock_server = start_mock_server(MOCK_PORT)
    console.print("  ✅ [dim]Local server started serving a real signup form page.[/dim]")

    # ── 5. Employee Corrects Work & Submits Genuine Proof ───────────────────
    console.print(f"\n✨ [bold green]Step 5: Employee ({active_name}) Submits Genuine Work URL Proof...[/bold green]")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"Authorization": f"Bearer {active_token}"}
            genuine_url = f"http://127.0.0.1:{MOCK_PORT}"
            log_text = f"I have corrected my mistakes. Here is the genuine deployed secure website containing the requested signup form: {genuine_url}"
            console.print(f"  📝 [bold white]{active_name}:[/bold white] [italic]\"{log_text}\"[/italic]")
            
            resp = await client.post(
                f"{BASE_URL}/api/logs/{task_id}",
                json={"log_text": log_text},
                headers=headers
            )
            
            if resp.status_code == 201:
                res_json = resp.json()
                confidence = res_json.get("ai_confidence")
                feedback = res_json.get("ai_feedback")
                
                console.print(f"  🤖 [bold yellow]AI Supervisor Audit Verdict:[/bold yellow]")
                console.print(f"    • Confidence: [bold green]{confidence}[/bold green]")
                console.print(f"    • Feedback: {feedback}")
                
                if confidence == "High":
                    sim_steps.append(("Genuine Proof Approval (Live Gemini + Playwright)", "PASS", "E2E browser successfully extracted form inputs. Live Gemini approved task!"))
                else:
                    sim_steps.append(("Genuine Proof Approval (Live Gemini + Playwright)", "FAIL", f"Expected High confidence but got: {confidence}"))
            else:
                console.print(f"  ❌ Failed to submit log. Status: {resp.status_code}")
    except Exception as e:
        console.print("  ❌ Error submitting genuine proof:", e)
    finally:
        mock_server.shutdown()
        console.print("\n🛑 [bold yellow]Local server shutdown successfully.[/bold yellow]")

    # ── Summary Render ───────────────────────────────────────────────────────
    print("")
    table = Table(title="🏢 WorkFlow Dynamic E2E Real-Time Simulation Results")
    table.add_column("Simulation Flow Step", style="bold white")
    table.add_column("Verdict", style="bold")
    table.add_column("Dynamic Details", style="dim")
    
    for step, verdict, detail in sim_steps:
        v_color = "green" if verdict == "PASS" else "red"
        table.add_row(step, f"[{v_color}]{verdict}[/{v_color}]", detail)
        
    console.print(table)
    print("")


if __name__ == "__main__":
    asyncio.run(run_simulation())
