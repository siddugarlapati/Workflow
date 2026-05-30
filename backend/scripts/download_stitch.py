import asyncio
import httpx
import os

SCREENS = {
    "screen1_prd_plan.html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzJlOTZlYWNjNWMxMjQ2YjliNTU4ZjQwOTY0NDVhN2NmEgsSBxDq9omiqhEYAZIBJAoKcHJvamVjdF9pZBIWQhQxNDEyNjA5NTEwOTc2OTEzODY2NA&filename=&opi=89354086",
    "screen2_manager_overview.html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sX2VmYmM3YTRiNjkyNDRmMmFhNjJhMzY3MjM2YWNkOTVkEgsSBxDq9omiqhEYAZIBJAoKcHJvamVjdF9pZBIWQhQxNDEyNjA5NTEwOTc2OTEzODY2NA&filename=&opi=89354086",
    "screen4_employee_tasks.html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzdmMWExNWIyN2NiNzQyYjNiOTJhMGFkODBmMmI1M2ZjEgsSBxDq9omiqhEYAZIBJAoKcHJvamVjdF9pZBIWQhQxNDEyNjA5NTEwOTc2OTEzODY2NA&filename=&opi=89354086",
    "screen5_task_control.html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzU3YzQ2NTBjNGNiZjRhMzViZGI4YjllNjEyZjc4NzYwEgsSBxDq9omiqhEYAZIBJAoKcHJvamVjdF9pZBIWQhQxNDEyNjA5NTEwOTc2OTEzODY2NA&filename=&opi=89354086",
    "screen6_ai_verification.html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzhjNWUwYzhlZGUzOTRjMzViN2EyZWEzYTBmNjk1ZmU2EgsSBxDq9omiqhEYAZIBJAoKcHJvamVjdF9pZBIWQhQxNDEyNjA5NTEwOTc2OTEzODY2NA&filename=&opi=89354086"
}

output_dir = "/Users/garlapati/Coding/Workflow/stitch_reference"
os.makedirs(output_dir, exist_ok=True)

async def download_file(name, url):
    print(f"Downloading {name}...")
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(url)
        if resp.status_code == 200:
            dest = os.path.join(output_dir, name)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(resp.text)
            print(f"✅ Saved {name} ({len(resp.text)} chars)")
        else:
            print(f"❌ Failed to download {name}: HTTP {resp.status_code}")

async def main():
    tasks = [download_file(name, url) for name, url in SCREENS.items()]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
