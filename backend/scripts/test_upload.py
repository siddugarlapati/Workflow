import asyncio
import io
import httpx
from rich.console import Console

console = Console()
BASE_URL = "http://localhost:8005"

async def test_uploads():
    console.print("[bold purple]⚡ Starting Work-Log Document Upload Verification...[/bold purple]\n")
    
    # 1. Login as Employee
    async with httpx.AsyncClient(timeout=10.0) as client:
        login_resp = await client.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "employee1@demo.com", "password": "password123"}
        )
        if login_resp.status_code != 200:
            console.print("[red]❌ Employee login failed[/red]")
            return
        
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Fetch employee's tasks to get an active task ID
        tasks_resp = await client.get(f"{BASE_URL}/api/tasks/mine", headers=headers)
        tasks = tasks_resp.json()["tasks"]
        active_tasks = [t for t in tasks if t["status"] != "completed"]
        
        if not active_tasks:
            console.print("[yellow]⚠️ No active tasks found for employee. Please seed database first.[/yellow]")
            return
            
        task = active_tasks[0]
        task_id = task["id"]
        console.print(f"Using active task: [cyan]{task['title']}[/cyan] ({task_id})")

        # 3. Simulate file uploading (Excel file)
        # Create a mock spreadsheet in memory using openpyxl
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Transit Discrepancies"
        ws.append(["ShipmentID", "Carrier", "DiscrepancyHours", "Notes"])
        ws.append(["SH-1001", "FedEx", "1.5", "Late departure"])
        ws.append(["SH-1002", "UPS", "2.0", "Weather delay"])
        
        excel_bytes = io.BytesIO()
        wb.save(excel_bytes)
        excel_data = excel_bytes.getvalue()
        
        console.print("Uploading mock excel document proof 'discrepancies.xlsx'...")
        files = {
            "file": ("discrepancies.xlsx", excel_data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }
        data = {
            "log_text": "Completed the reconciliation audit sheet for Warehouse B. Attached document has transit logs."
        }
        
        # We must post as multipart form data
        resp = await client.post(
            f"{BASE_URL}/api/logs/{task_id}",
            data=data,
            files=files,
            headers=headers
        )
        
        if resp.status_code == 201:
            res_json = resp.json()
            console.print("[green]✅ Document Upload and Verification Success![/green]")
            console.print(f"Uploaded Filename: [bold yellow]{res_json.get('file_name')}[/bold yellow]")
            console.print(f"Log text saved in DB preview:\n[dim]{res_json.get('log_text')[:400]}...[/dim]")
            console.print(f"AI Verdict: [bold cyan]{res_json.get('ai_confidence')}[/bold cyan] | Feedback: {res_json.get('ai_feedback')}")
        else:
            console.print(f"[red]❌ Upload submission failed: {resp.status_code} - {resp.text}[/red]")

if __name__ == "__main__":
    asyncio.run(test_uploads())
