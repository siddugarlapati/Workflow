"""
WorkFlow — Streamlit Premium Frontend
======================================
A premium, dark-themed, glassmorphic UI representing the WorkFlow dashboard.
Integrates Manager & Employee dashboards, AI verification badges,
LangGraph team status agent, and RAG task history.
"""
import os
import streamlit as st
import datetime
from utils.api_client import APIClient, init_session_state, logout
from components.ai_badge import render_confidence_badge

# Page configuration
st.set_page_config(
    page_title="WorkFlow | AI Enterprise Accountability Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS for Premium Aesthetics ─────────────────────────────────────────
st.markdown("""
<style>
    /* Premium fonts and background */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Custom cards with subtle borders and deep colors */
    .premium-card {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }
    
    /* Neon glowing badges */
    .glow-purple {
        box-shadow: 0 0 15px rgba(109, 40, 217, 0.4);
    }
    
    /* Heading typography */
    h1, h2, h3 {
        color: #F8FAFC !important;
        font-weight: 700 !important;
    }
    
    .gradient-text {
        background: linear-gradient(to right, #A78BFA, #EC4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
</style>
""", unsafe_allow_html=True)


def main():
    init_session_state()

    # Sidebar Branding
    st.sidebar.markdown(
        "<h1 style='text-align: center;'><span class='gradient-text'>WorkFlow</span> ⚡</h1>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("<p style='text-align: center; color: #94A3B8;'>AI-Powered Accountability</p>", unsafe_allow_html=True)
    st.sidebar.markdown("---")

    # Routing based on Auth state
    if not st.session_state.token:
        render_login_screen()
    else:
        render_app_dashboard()


# ─────────────────────────────────────────────────────────────────────────────
# Login & Register Screen
# ─────────────────────────────────────────────────────────────────────────────
def render_login_screen():
    tab1, tab2 = st.tabs(["🔐 Secure Login", "🚀 Manager / Employee Signup"])

    with tab1:
        st.markdown("<h3 style='margin-bottom: 20px;'>Welcome Back</h3>", unsafe_allow_html=True)
        login_email = st.text_input("Corporate Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Authenticate", use_container_width=True, type="primary"):
            if not login_email or not login_password:
                st.warning("Please fill out all fields.")
                return
                
            response = APIClient.post(
                "/api/auth/login",
                json_data={"email": login_email, "password": login_password},
            )
            
            if response.status_code == 200:
                data = response.json()
                st.session_state.token = data["access_token"]
                st.session_state.user = data["user"]
                st.success(f"Authenticated as {data['user']['full_name']}!")
                st.rerun()
            else:
                st.error("Authentication failed. Invalid email or password.")

    with tab2:
        st.markdown("<h3 style='margin-bottom: 20px;'>Create Enterprise Workspace</h3>", unsafe_allow_html=True)
        reg_name = st.text_input("Full Name")
        reg_email = st.text_input("Business Email")
        reg_password = st.text_input("Choose Password", type="password")
        reg_role = st.selectbox("Role", ["Employee", "Manager"])
        reg_dept = st.text_input("Department (e.g. Sales, Logistics, Engineering)")

        if st.button("Register Account", use_container_width=True):
            if not reg_name or not reg_email or not reg_password:
                st.warning("Please fill out all mandatory fields.")
                return

            response = APIClient.post(
                "/api/auth/register",
                json_data={
                    "email": reg_email,
                    "password": reg_password,
                    "full_name": reg_name,
                    "role": reg_role.lower(),
                    "department": reg_dept if reg_dept else None,
                },
            )

            if response.status_code == 201:
                data = response.json()
                st.session_state.token = data["access_token"]
                st.session_state.user = data["user"]
                st.success("Successfully registered and authenticated!")
                st.rerun()
            else:
                st.error(f"Registration failed: {response.json().get('detail', 'Unknown error')}")


# ─────────────────────────────────────────────────────────────────────────────
# Main App Layout (Authenticated)
# ─────────────────────────────────────────────────────────────────────────────
def render_app_dashboard():
    user = st.session_state.user
    role = user["role"]
    
    st.sidebar.markdown(f"**User**: {user['full_name']}")
    st.sidebar.markdown(f"**Role**: `{role.upper()}`")
    st.sidebar.markdown(f"**Dept**: {user['department'] or 'General'}")
    st.sidebar.markdown("---")

    # Dynamic Navigation Based on Role
    navigation_options = []
    if role == "manager":
        navigation_options = [
            "📋 Task Dashboard",
            "➕ Assign New Task",
            "🤖 'Where's My Team?' AI Summary",
            "🛡️ Immutable Audit Trail",
        ]
    else:  # employee
        navigation_options = [
            "📥 My Assigned Tasks",
            "✍️ Submit Work Log",
        ]

    choice = st.sidebar.radio("Navigation", navigation_options)
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout()

    # Content Area Routing
    if "📋 Task Dashboard" in choice:
        render_manager_dashboard()
    elif "➕ Assign New Task" in choice:
        render_assign_task_screen()
    elif "🤖 'Where's My Team?'" in choice:
        render_ai_summary_screen()
    elif "🛡️ Immutable Audit Trail" in choice:
        render_audit_trail_screen()
    elif "📥 My Assigned Tasks" in choice:
        render_employee_dashboard()
    elif "✍️ Submit Work Log" in choice:
        render_submit_log_screen()


# ─────────────────────────────────────────────────────────────────────────────
# Manager Views
# ─────────────────────────────────────────────────────────────────────────────
def render_manager_dashboard():
    st.markdown("<h2>📋 Enterprise Task & Accountability Center</h2>", unsafe_allow_html=True)
    st.markdown("---")

    # Fetch tasks
    response = APIClient.get("/api/tasks/")
    if response.status_code != 200:
        st.error("Failed to load tasks from backend.")
        return

    data = response.json()
    tasks = data["tasks"]
    overdue_count = data["overdue_count"]

    # Header KPI Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="premium-card">
            <h4 style='color: #94A3B8; margin:0;'>Active Assigned Tasks</h4>
            <h1 style='margin: 10px 0 0 0; color: #6D28D9;'>{len(tasks)}</h1>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="premium-card">
            <h4 style='color: #94A3B8; margin:0;'>Critical Overdue Alert</h4>
            <h1 style='margin: 10px 0 0 0; color: #EF4444;'>{overdue_count}</h1>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        # Check AI health
        ai_resp = APIClient.get("/api/ai/health")
        ai_status = "ONLINE" if ai_resp.status_code == 200 and ai_resp.json().get("data", {}).get("status") == "ok" else "OFFLINE"
        ai_color = "#10B981" if ai_status == "ONLINE" else "#EF4444"
        st.markdown(f"""
        <div class="premium-card">
            <h4 style='color: #94A3B8; margin:0;'>Local AI LLM Verification</h4>
            <h1 style='margin: 10px 0 0 0; color: {ai_color};'>{ai_status}</h1>
        </div>
        """, unsafe_allow_html=True)

    # Main task listing
    st.markdown("### Active Task Matrix")
    if not tasks:
        st.info("No active tasks found in database. Click 'Assign New Task' to begin.")
        return

    # Render Task Cards / Table
    for task in tasks:
        with st.container():
            st.markdown(f"""
            <div style="background-color: #1E293B; border-radius: 8px; padding: 16px; margin-bottom: 12px; border-left: 5px solid {'#EF4444' if task['status'] == 'overdue' else '#6D28D9'};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="margin: 0; color: #F8FAFC;">{task['title']}</h4>
                    <span style="background-color: #334155; color: #A78BFA; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;">{task['status'].upper()}</span>
                </div>
                <p style="color: #94A3B8; font-size: 0.9rem; margin: 8px 0;">{task['description'] or 'No description provided.'}</p>
                <div style="display: flex; gap: 20px; font-size: 0.85rem; color: #64748B;">
                    <span>👤 Assignee: <b>{task['assignee_name'] or 'Unassigned'}</b></span>
                    <span>📅 Deadline: <b>{task['deadline'][:16].replace('T', ' ')}</b></span>
                    <span>🔥 Priority: <b style="color: {'#EF4444' if task['priority'] == 'critical' else '#F59E0B'}">{task['priority'].upper()}</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Interactive Task Actions inside st.expander
            with st.expander("🔍 View Accountability Work Logs & Audit history"):
                log_response = APIClient.get(f"/api/logs/task/{task['id']}")
                if log_response.status_code == 200:
                    logs = log_response.json()["logs"]
                    if not logs:
                        st.write("No work logs submitted yet by employee.")
                    else:
                        for l in logs:
                            st.markdown(f"**Submitted at**: {l['submitted_at'][:16].replace('T', ' ')}")
                            if l.get("file_name"):
                                st.markdown(f"📎 **Attached Document Proof**: `{l['file_name']}`")
                            st.info(l["log_text"])
                            render_confidence_badge(l["ai_confidence"], l["ai_feedback"])
                            st.markdown("---")
                else:
                    st.error("Could not fetch work logs.")

                # Option to delete
                if st.button("Delete Task", key=f"del_{task['id']}"):
                    del_resp = APIClient.delete(f"/api/tasks/{task['id']}")
                    if del_resp.status_code == 204:
                        st.success("Task soft-deleted.")
                        st.rerun()
                    else:
                        st.error("Failed to delete task.")


def render_assign_task_screen():
    st.markdown("<h2>➕ Assign AI-Triaged Enterprise Task</h2>", unsafe_allow_html=True)
    st.markdown("---")

    title = st.text_input("Task Title (e.g. Audit regional warehouse inventory)")
    desc = st.text_area("Detailed Action Description & Required Deliverables")

    # Fetch employees for selection
    # Using profile register endpoint or simple local user fetch. Since we want active employees:
    # We'll fetch all profiles and filter in front end or let backend list active employees.
    # For robust demo: we list standard demo users and also allow typing or pull dynamically.
    # Let's register standard demo assignees.
    # To be extremely robust, we fetch all profiles. Let's do a GET to /api/auth/me to verify backend, 
    # but we will provide manual selection if dynamic user fetch is complex.
    # Let's seed employee IDs.
    # Fetch active employees directory in real-time from the backend
    emp_resp = APIClient.get("/api/auth/employees")
    if emp_resp.status_code == 200:
        employees = emp_resp.json()
        employee_dict = {
            f"{emp['full_name']} ({emp['department'] or 'General'})": emp["id"]
            for emp in employees
        }
    else:
        employee_dict = {}

    if not employee_dict:
        st.warning("⚠️ No active employees found in the workspace directory. Please register employees first.")
        return

    assignee_name = st.selectbox("Assign Responsibility To", list(employee_dict.keys()))
    assigned_to_id = employee_dict[assignee_name]

    # AI Triage Suggestion Button
    if st.button("🪄 Request AI Smart Triage (Priority & Deadline)"):
        if not title:
            st.warning("Please specify a task title first.")
            return

        triage_resp = APIClient.post(
            "/api/ai/suggest-priority",
            params={"title": title, "description": desc},
        )
        if triage_resp.status_code == 200:
            ai_data = triage_resp.json()["data"]
            st.session_state.ai_priority = ai_data["priority"]
            st.session_state.ai_deadline_days = ai_data["deadline_days"]
            st.session_state.ai_reasoning = ai_data["reasoning"]
            st.success("AI Triage Completed!")
        else:
            st.error("Failed to call Ollama AI.")

    # Form defaults
    default_priority = st.session_state.get("ai_priority", "medium")
    default_days = st.session_state.get("ai_deadline_days", 5)
    
    priority = st.selectbox(
        "Priority Level",
        ["low", "medium", "high", "critical"],
        index=["low", "medium", "high", "critical"].index(default_priority),
    )

    deadline_date = st.date_input(
        "Completion Deadline",
        datetime.date.today() + datetime.timedelta(days=int(default_days)),
    )
    
    if st.session_state.get("ai_reasoning"):
        st.info(f"💡 **AI Suggestion Rationale**: {st.session_state.ai_reasoning}")

    if st.button("Confirm and Assign Responsibility", type="primary", use_container_width=True):
        if not title:
            st.error("Task title is required.")
            return

        # Build deadline datetime ISO format
        deadline_dt = datetime.datetime.combine(deadline_date, datetime.time(17, 0)) # 5 PM deadline
        
        response = APIClient.post(
            "/api/tasks/",
            json_data={
                "title": title,
                "description": desc,
                "assigned_to": assigned_to_id,
                "priority": priority,
                "deadline": deadline_dt.isoformat(),
            },
        )

        if response.status_code == 201:
            st.success(f"Successfully assigned task to {assignee_name}!")
            # Reset smart state
            st.session_state.pop("ai_priority", None)
            st.session_state.pop("ai_deadline_days", None)
            st.session_state.pop("ai_reasoning", None)
        else:
            st.error(f"Failed to assign task: {response.json().get('detail', 'Unknown error')}")


def render_ai_summary_screen():
    st.markdown("<h2>🤖 'Where's My Team?' Plain-English briefing</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94A3B8;'>Uses local llama3.2 to compile team risk, delayed milestones, and top accomplishments in 5 concise sentences.</p>", unsafe_allow_html=True)
    st.markdown("---")

    if st.button("📊 Generate Real-time AI Summary", type="primary", use_container_width=True):
        with st.spinner("AI is analyzing recent work logs and compiling briefing..."):
            response = APIClient.get("/api/ai/summary")
            if response.status_code == 200:
                data = response.json()
                st.markdown(f"""
                <div class="premium-card glow-purple">
                    <p style="font-size: 1.15rem; line-height: 1.6; color: #F8FAFC;">{data['summary']}</p>
                    <div style="font-size: 0.8rem; color: #64748B; margin-top: 20px; text-align: right;">
                        Generated on task matrix containing {data['task_count']} items.
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("Failed to generate summary. Ensure Ollama is running and model llama3.2 is loaded.")

    # Show Multi-Step Agent analysis too!
    st.markdown("### 🧬 LangGraph multi-step accountability agent")
    if st.button("🔍 Run Accountability Agent"):
        with st.spinner("Agent routing through analysis nodes..."):
            agent_resp = APIClient.get("/api/ai/agent-analysis")
            if agent_resp.status_code == 200:
                agent_data = agent_resp.json()["data"]
                st.markdown(f"**Risk Level Alert**: `{agent_data['risk_level'].upper()}`")
                st.success(agent_data["analysis"])
                st.write("**Actionable Recommendations:**")
                for rec in agent_data["recommendations"]:
                    st.write(f"- {rec}")
            else:
                st.error("Failed to execute LangGraph agent.")


def render_audit_trail_screen():
    st.markdown("<h2>🛡️ Tamper-Resistant Immutable Audit Trail</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94A3B8;'>Every task action, assignment, priority escalation, and work log is cryptographically sealed in an append-only timeline.</p>", unsafe_allow_html=True)
    st.markdown("---")

    response = APIClient.get("/api/audit/")
    if response.status_code == 200:
        logs = response.json()["data"]
        if not logs:
            st.info("No audit logs recorded yet.")
            return

        for log in logs:
            st.markdown(f"""
            <div style="background-color: #0F172A; border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; padding: 12px; margin-bottom: 8px;">
                <span style="color: #6D28D9; font-weight: 600;">[{log['created_at'][:19].replace('T', ' ')}]</span>
                <b>{log['actor']}</b> performed <code>{log['action'].upper()}</code> on <u>{log['entity_type']}</u> (id: {log['entity_id'][:8]})
                <pre style="background-color: #1E293B; padding: 8px; border-radius: 4px; font-size: 0.8rem; margin: 6px 0;">{log['payload']}</pre>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.error("Failed to load audit logs.")


# ─────────────────────────────────────────────────────────────────────────────
# Employee Views
# ─────────────────────────────────────────────────────────────────────────────
def render_employee_dashboard():
    st.markdown("<h2>📥 My Assigned Accountabilities</h2>", unsafe_allow_html=True)
    st.markdown("---")

    response = APIClient.get("/api/tasks/mine")
    if response.status_code != 200:
        st.error("Failed to fetch assigned tasks.")
        return

    tasks = response.json()["tasks"]
    if not tasks:
        st.info("Clean slate! You have no pending tasks assigned.")
        return

    for task in tasks:
        # Check status color
        color = "#10B981" if task["status"] == "completed" else ("#EF4444" if task["status"] == "overdue" else "#F59E0B")
        with st.container():
            st.markdown(f"""
            <div style="background-color: #1E293B; border-radius: 8px; padding: 16px; margin-bottom: 12px; border-left: 5px solid {color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="margin: 0; color: #F8FAFC;">{task['title']}</h4>
                    <span style="background-color: #0F172A; color: {color}; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;">{task['status'].upper()}</span>
                </div>
                <p style="color: #94A3B8; font-size: 0.9rem; margin: 8px 0;">{task['description'] or 'No description provided.'}</p>
                <div style="display: flex; gap: 20px; font-size: 0.85rem; color: #64748B;">
                    <span>📅 Due: <b>{task['deadline'][:16].replace('T', ' ')}</b></span>
                    <span>🔥 Priority: <b style="color: {'#EF4444' if task['priority'] == 'critical' else '#F59E0B'}">{task['priority'].upper()}</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Option to change status
            col1, col2 = st.columns([3, 1])
            with col2:
                new_status = st.selectbox(
                    "Update Status",
                    ["pending", "in_progress", "completed"],
                    index=["pending", "in_progress", "completed"].index(task["status"]) if task["status"] in ["pending", "in_progress", "completed"] else 0,
                    key=f"status_select_{task['id']}",
                )
                if new_status != task["status"]:
                    status_resp = APIClient.patch(
                        f"/api/tasks/{task['id']}/status",
                        json_data={"status": new_status},
                    )
                    if status_resp.status_code == 200:
                        st.success("Status updated.")
                        st.rerun()
                    else:
                        st.error("Failed to update status.")


def render_submit_log_screen():
    st.markdown("<h2>✍️ Submit Daily Progress Log</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94A3B8;'>Be explicit and detailed. Every progress entry is analyzed in real-time by Ollama AI to score credibility, preventing bluffing and maintaining team integrity.</p>", unsafe_allow_html=True)
    st.markdown("---")

    response = APIClient.get("/api/tasks/mine")
    if response.status_code != 200:
        st.error("Failed to fetch active tasks.")
        return

    tasks = response.json()["tasks"]
    active_tasks = [t for t in tasks if t["status"] != "completed"]

    if not active_tasks:
        st.info("No active tasks to submit logs for. Great job!")
        return

    task_choices = {t["title"]: t["id"] for t in active_tasks}
    selected_task_title = st.selectbox("Select Target Accountability", list(task_choices.keys()))
    selected_task_id = task_choices[selected_task_title]

    log_text = st.text_area(
        "Progress Log Entry",
        placeholder="Provide quantitative details of what you completed today, sections touched, or explicit roadblocks encountered...",
        height=150,
    )

    uploaded_file = st.file_uploader(
        "Upload Proof Document (.pdf, .docx, .xlsx, .txt, .csv)",
        type=["pdf", "docx", "xlsx", "txt", "csv"]
    )

    if st.button("Submit Progress Log", type="primary", use_container_width=True):
        if not log_text.strip() and not uploaded_file:
            st.warning("Please provide a plain-text note OR upload a document proof.")
            return

        if log_text.strip() and len(log_text) < 10 and not uploaded_file:
            st.warning("Progress log must be at least 10 characters long to contain real progress description.")
            return

        with st.spinner("AI is verifying work log entry credibility..."):
            data_payload = {"log_text": log_text}
            files_payload = None
            if uploaded_file is not None:
                files_payload = {
                    "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
                }

            if files_payload:
                log_resp = APIClient.post_multipart(
                    f"/api/logs/{selected_task_id}",
                    data=data_payload,
                    files=files_payload
                )
            else:
                log_resp = APIClient.post(
                    f"/api/logs/{selected_task_id}",
                    json_data=data_payload
                )

            if log_resp.status_code == 201:
                result = log_resp.json()
                st.success("Progress log submitted successfully and recorded in audit trail!")
                
                # Show premium custom AI confidence results instantly!
                st.markdown("### AI Accountability Verdict")
                render_confidence_badge(result["ai_confidence"], result["ai_feedback"])
            else:
                detail_msg = "Failed to submit log."
                try:
                    detail_msg += f" Details: {log_resp.json().get('detail')}"
                except Exception:
                    pass
                st.error(detail_msg)


if __name__ == "__main__":
    main()
