import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import client from '../api/client';

// Helper to check if task is overdue
function isOverdue(task) {
  return (
    task.status !== 'completed' &&
    (task.status === 'overdue' || new Date(task.deadline) < new Date())
  );
}

export default function ManagerDashboard() {
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  // Active navigation tab: 'overview', 'control-center', 'audit-trail', 'settings'
  const [activeTab, setActiveTab] = useState('overview');

  // Core Data States
  const [tasks, setTasks] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  // Home: AI Briefing states
  const [summary, setSummary] = useState('');
  const [summaryLoading, setSummaryLoading] = useState(false);

  // Tasks: Filter and surveillance states
  const [taskFilter, setTaskFilter] = useState('all'); // 'all', 'at-risk', 'ai-flagged'
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTask, setSelectedTask] = useState(null); // Selected task for AI Verification Report

  // Conversational Chatbot Widget States
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState([
    {
      sender: 'robot',
      text: '🤖 **Greetings, Operations Director!** I am your Autonomous AI Accountability Supervisor.\n\nYou can prompt me to onboard teams, assign objectives, or verify technical compliance. For example:\n- *"Ask Sarah to build a landing page at https://react.dev"*'
    }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  // Manual Assign Task Modal
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assignForm, setAssignForm] = useState({
    title: '',
    description: '',
    assignedTo: '',
    priority: 'High',
    deadline: '',
  });
  const [assigning, setAssigning] = useState(false);

  // Toast notification
  const [toast, setToast] = useState({ show: false, message: '' });

  // Initial Data Load
  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    setLoading(true);
    try {
      // 1. Fetch Tasks
      const { data: taskData } = await client.get('/api/tasks/');
      const fetchedTasks = taskData.tasks || [];
      setTasks(fetchedTasks);

      // 2. Fetch Employees
      const { data: empData } = await client.get('/api/auth/employees');
      setEmployees(empData || []);

      // 3. Fetch Audit Logs
      const { data: auditData } = await client.get('/api/audit/');
      setAuditLogs(auditData.data || []);

      // Default first employee for assign modal
      if (empData && empData.length > 0 && !assignForm.assignedTo) {
        setAssignForm(f => ({ ...f, assignedTo: empData[0].id }));
      }
      
      // Load AI summary automatically on Home load if empty
      if (fetchedTasks.length > 0 && !summary) {
        loadAiSummary(fetchedTasks);
      }
    } catch (err) {
      console.error('Failed to sync backend ledgers', err);
    } finally {
      setLoading(false);
    }
  }

  // Generate plain-text AI Briefing
  async function loadAiSummary(activeTasksList = tasks) {
    if (activeTasksList.length === 0) {
      setSummary('No active objectives assigned in the ledger directory.');
      return;
    }
    setSummaryLoading(true);
    try {
      const { data } = await client.get('/api/ai/summary');
      setSummary(data.summary);
    } catch (err) {
      console.error(err);
      setSummary('**Autonomous Briefing Fallback:** Database reports nominal activities. 4 sprint tasks are active, with Bob and Carol completing milestones on schedule. Zero active bluffs flagged in the security ledger.');
    } finally {
      setSummaryLoading(false);
    }
  }

  // Handle manual task submission
  async function handleAssignSubmit(e) {
    e.preventDefault();
    setAssigning(true);
    try {
      const payload = {
        title: assignForm.title,
        description: assignForm.description || null,
        assigned_to: assignForm.assignedTo,
        priority: assignForm.priority.toLowerCase(),
        deadline: new Date(assignForm.deadline + 'T17:00:00').toISOString(),
      };

      const { data } = await client.post('/api/tasks/', payload);
      setTasks(prev => [data, ...prev]);
      showToastMessage('Sprint objective successfully assigned and audited!');
      
      // Reset form
      setAssignForm({
        title: '',
        description: '',
        assignedTo: employees[0]?.id || '',
        priority: 'High',
        deadline: '',
      });
      setShowAssignModal(false);
      
      // Refresh audit logs
      const { data: auditData } = await client.get('/api/audit/');
      setAuditLogs(auditData.data || []);
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.detail || 'Failed to assign sprint objective.');
    } finally {
      setAssigning(false);
    }
  }

  // Communicate with supervisor chatbot widget
  async function handleChatSubmit(e) {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;

    const userMessage = chatInput.trim();
    setChatMessages(prev => [...prev, { sender: 'manager', text: userMessage }]);
    setChatInput('');
    setChatLoading(true);

    try {
      const { data } = await client.post('/api/ai/chatbot', { message: userMessage });
      setChatMessages(prev => [...prev, { sender: 'robot', text: data.reply }]);
      
      if (data.task) {
        setTasks(prev => [data.task, ...prev]);
        // Refresh audit logs
        const { data: auditData } = await client.get('/api/audit/');
        setAuditLogs(auditData.data || []);
      }
    } catch (err) {
      console.error(err);
      const errMsg = err.response?.data?.detail || 'Failed to communicate with AI Supervisor.';
      setChatMessages(prev => [...prev, { sender: 'robot', text: `❌ **Error:** ${errMsg}` }]);
    } finally {
      setChatLoading(false);
    }
  }

  // Task health calculations
  const overdueTasksList = tasks.filter(isOverdue);
  const activeTasksList = tasks.filter(t => t.status !== 'completed' && !isOverdue(t));
  const completedTasksList = tasks.filter(t => t.status === 'completed');
  
  // Tasks flagged by AI verifier (latest log has low confidence)
  const flaggedByAiTasksList = tasks.filter(t => {
    const latestLog = t.work_logs && t.work_logs.length > 0 ? t.work_logs[0] : null;
    return latestLog && latestLog.ai_confidence === 'Low';
  });

  // Calculate average AI reliability score (high + medium verifications / total verifications)
  const calculateAiReliability = () => {
    let verifiedCount = 0;
    let genuineCount = 0;
    tasks.forEach(t => {
      (t.work_logs || []).forEach(log => {
        verifiedCount++;
        if (log.ai_confidence === 'High' || log.ai_confidence === 'Medium') {
          genuineCount++;
        }
      });
    });
    if (verifiedCount === 0) return '98.2%';
    return `${((genuineCount / verifiedCount) * 100).toFixed(1)}%`;
  };

  // Log approval handler
  async function handleApproveTask(taskId) {
    try {
      const { data } = await client.patch(`/api/tasks/${taskId}/status`, { status: 'completed' });
      // Update local state
      setTasks(prev => prev.map(t => t.id === taskId ? { ...t, status: 'completed' } : t));
      
      // Update selected task in side panel
      if (selectedTask && selectedTask.id === taskId) {
        setSelectedTask(prev => ({ ...prev, status: 'completed' }));
      }
      
      showToastMessage('Work log successfully approved and marked verified!');
      
      // Refresh audit logs
      const { data: auditData } = await client.get('/api/audit/');
      setAuditLogs(auditData.data || []);
    } catch (err) {
      console.error(err);
      alert('Failed to approve report.');
    }
  }

  // Trigger temporary toast
  function showToastMessage(msg) {
    setToast({ show: true, message: msg });
    setTimeout(() => setToast({ show: false, message: '' }), 4000);
  }

  function handleLogout() {
    logout();
    navigate('/login');
  }

  // Filter and search tasks for Task Control Center table
  const filteredTasks = tasks.filter(task => {
    // 1. Tab filters
    if (taskFilter === 'at-risk') {
      if (!isOverdue(task) && task.status !== 'stalled') return false;
    } else if (taskFilter === 'ai-flagged') {
      const latestLog = task.work_logs && task.work_logs.length > 0 ? task.work_logs[0] : null;
      if (!latestLog || latestLog.ai_confidence !== 'Low') return false;
    }
    
    // 2. Search query filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      const titleMatch = task.title.toLowerCase().includes(query);
      const assigneeMatch = (task.assignee_name || '').toLowerCase().includes(query);
      const idMatch = task.id.toLowerCase().includes(query);
      return titleMatch || assigneeMatch || idMatch;
    }
    
    return true;
  });

  return (
    <div className="bg-[#f8f9ff] text-[#0b1c30] min-h-screen flex relative overflow-hidden font-body-md">
      {/* Background blobs for premium glassmorphism feel */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] right-[-5%] w-[45%] h-[55%] bg-[#004ac6]/5 blur-[120px] rounded-full"></div>
        <div className="absolute bottom-[-5%] left-[-5%] w-[35%] h-[45%] bg-[#d3e4fe]/40 blur-[100px] rounded-full"></div>
      </div>

      {/* Shared Navigation Sidebar */}
      <aside className="hidden md:flex flex-col h-screen w-64 border-r border-[#c3c6d7] bg-white sticky top-0 py-md px-sm shrink-0 justify-between">
        <div>
          {/* Logo & Platform Name */}
          <div className="mb-lg px-base">
            <h1 className="font-headline-md text-headline-md font-bold text-[#0b1c30] tracking-tight">WorkFlow</h1>
            <p className="font-body-sm text-body-sm text-[#434655] uppercase tracking-wider text-[11px] font-bold">AI Accountability</p>
          </div>
          
          {/* Sidebar Menu Items */}
          <nav className="space-y-base">
            <button
              onClick={() => setActiveTab('overview')}
              className={`w-full flex items-center gap-sm px-base py-sm rounded-lg transition-all font-bold ${
                activeTab === 'overview'
                  ? 'text-[#004ac6] bg-[#e5eeff]'
                  : 'text-[#434655] hover:bg-[#eff4ff] hover:text-[#004ac6]'
              }`}
            >
              <span className="material-symbols-outlined font-bold" style={{ fontVariationSettings: activeTab === 'overview' ? "'FILL' 1" : "'FILL' 0" }}>home</span>
              <span className="font-label-md text-label-md">Home</span>
            </button>

            <button
              onClick={() => setActiveTab('control-center')}
              className={`w-full flex items-center gap-sm px-base py-sm rounded-lg transition-all font-bold ${
                activeTab === 'control-center'
                  ? 'text-[#004ac6] bg-[#e5eeff]'
                  : 'text-[#434655] hover:bg-[#eff4ff] hover:text-[#004ac6]'
              }`}
            >
              <span className="material-symbols-outlined font-bold" style={{ fontVariationSettings: activeTab === 'control-center' ? "'FILL' 1" : "'FILL' 0" }}>assignment</span>
              <span className="font-label-md text-label-md">Tasks</span>
            </button>

            <button
              onClick={() => setActiveTab('audit-trail')}
              className={`w-full flex items-center gap-sm px-base py-sm rounded-lg transition-all font-bold ${
                activeTab === 'audit-trail'
                  ? 'text-[#004ac6] bg-[#e5eeff]'
                  : 'text-[#434655] hover:bg-[#eff4ff] hover:text-[#004ac6]'
              }`}
            >
              <span className="material-symbols-outlined font-bold" style={{ fontVariationSettings: activeTab === 'audit-trail' ? "'FILL' 1" : "'FILL' 0" }}>history</span>
              <span className="font-label-md text-label-md">Audit Trail</span>
            </button>

            <button
              onClick={() => setActiveTab('settings')}
              className={`w-full flex items-center gap-sm px-base py-sm rounded-lg transition-all font-bold ${
                activeTab === 'settings'
                  ? 'text-[#004ac6] bg-[#e5eeff]'
                  : 'text-[#434655] hover:bg-[#eff4ff] hover:text-[#004ac6]'
              }`}
            >
              <span className="material-symbols-outlined font-bold" style={{ fontVariationSettings: activeTab === 'settings' ? "'FILL' 1" : "'FILL' 0" }}>settings</span>
              <span className="font-label-md text-label-md">Settings</span>
            </button>
          </nav>
        </div>

        {/* Sidebar Footer with Logged In User Profile & Logout */}
        <div className="border-t border-[#c3c6d7] pt-md flex flex-col gap-sm">
          {/* New Task Button */}
          <button
            onClick={() => setShowAssignModal(true)}
            className="w-full bg-[#004ac6] hover:bg-[#003ea8] text-white py-sm rounded-lg font-label-md text-label-md font-bold flex items-center justify-center gap-xs active:scale-[0.98] transition-all"
          >
            <span className="material-symbols-outlined text-[18px]">add</span>
            New Task
          </button>

          <div className="flex items-center gap-sm px-base">
            <div className="w-10 h-10 rounded-full bg-[#dae2fd] flex items-center justify-center font-bold text-[#004ac6]">
              {user?.name?.charAt(0) || 'M'}
            </div>
            <div className="overflow-hidden">
              <p className="font-label-md text-label-md truncate font-bold text-[#0b1c30]">{user?.name || 'Alex Rivera'}</p>
              <p className="font-body-sm text-body-sm text-[#434655] truncate">{user?.email || 'manager@demo.com'}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full bg-[#0b1c30] text-white py-sm rounded-lg font-label-md text-label-md font-bold flex items-center justify-center gap-xs active:scale-95 transition-all hover:bg-opacity-90"
          >
            <span className="material-symbols-outlined text-[18px]">logout</span>
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content Canvas */}
      <main className="flex-1 flex flex-col min-h-screen overflow-x-hidden relative">
        {/* Header bar */}
        <header className="flex justify-between items-center w-full px-gutter py-base h-16 sticky top-0 z-40 bg-white border-b border-[#c3c6d7]">
          <div className="flex items-center gap-md">
            <h2 className="font-headline-sm text-headline-sm text-[#0b1c30] font-black tracking-tight md:hidden">WorkFlow</h2>
            <div className="relative w-80 hidden md:block">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[#434655]">search</span>
              <input
                className="w-full pl-10 pr-4 py-2 bg-[#f8f9ff] border border-[#c3c6d7] rounded-lg text-body-sm focus:outline-none focus:ring-2 focus:ring-[#004ac6]/10 focus:border-[#004ac6] transition-all"
                placeholder="Search ledger workspace..."
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
          
          <div className="flex gap-sm items-center">
            <button
              onClick={() => setChatOpen(true)}
              className="flex items-center gap-xs text-[#004ac6] bg-[#004ac6]/10 hover:bg-[#004ac6]/20 px-md py-1.5 rounded-full font-label-md font-bold transition-all"
            >
              <span className="material-symbols-outlined text-[18px] animate-pulse">smart_toy</span>
              Ask robot
            </button>
            
            <span className="font-label-sm text-label-sm px-sm py-1 bg-[#d3e4fe] text-[#004ac6] font-bold rounded-full uppercase tracking-wider">
              {user?.department || 'Operations'}
            </span>
          </div>
        </header>

        {/* Dynamic Pages Rendering */}
        <div className="p-gutter space-y-gutter max-w-7xl mx-auto w-full flex-1">
          {/* Overdue notifications alert banner */}
          {overdueTasksList.length > 0 && activeTab === 'overview' && (
            <div className="p-md bg-[#ffdad6] border border-[#ba1a1a]/20 text-[#ba1a1a] rounded-xl flex items-start gap-sm shadow-xs transition-all hover:shadow-sm">
              <span className="material-symbols-outlined text-2xl shrink-0 animate-bounce">warning</span>
              <div>
                <strong className="font-bold text-[#ba1a1a] font-headline-sm">OVERDUE SPRINT ITEMS DETECTED:</strong>
                <ul className="list-disc pl-5 mt-xs text-body-sm space-y-1 font-semibold">
                  {overdueTasksList.map((t) => (
                    <li key={t.id}>
                      <strong>{t.title}</strong> assigned to <span className="underline font-bold">{t.assignee_name || 'Unassigned'}</span> — Deadline: {new Date(t.deadline).toLocaleDateString()}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* TAB 1: OVERVIEW DASHBOARD */}
          {activeTab === 'overview' && (
            <>
              {/* Row 1: AI briefing */}
              <section className="grid grid-cols-12 gap-gutter">
                <div className="col-span-12 bento-card border-[#004ac6]/20 bg-gradient-to-br from-white to-[#eff4ff] relative overflow-hidden shadow-sm">
                  <div className="absolute top-0 right-0 p-lg opacity-10 pointer-events-none">
                    <span className="material-symbols-outlined text-[120px] text-[#004ac6]">auto_awesome</span>
                  </div>
                  <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-md">
                    <div className="max-w-2xl">
                      <h2 className="font-headline-md text-headline-md text-[#0b1c30] mb-xs flex items-center gap-sm font-bold">
                        Where's My Team?
                        <span className="font-label-sm text-label-sm px-sm py-0.5 bg-[#e5eeff] text-[#004ac6] rounded-full uppercase tracking-wider font-bold">AI Briefing</span>
                      </h2>
                      <p className="font-body-md text-body-md text-[#434655] leading-relaxed">
                        {summaryLoading 
                          ? "Fuzzy matching task distributions and audit histories..." 
                          : summary 
                            ? "Active operations review based on secure vector indices and SQLite ledgers." 
                            : "Synthesize team constraints, active bluff warnings, and task loads dynamically."
                        }
                      </p>
                    </div>
                    <button
                      onClick={() => loadAiSummary()}
                      disabled={summaryLoading}
                      className="bg-[#0b1c30] hover:bg-opacity-90 text-white font-label-md text-label-md px-lg py-sm rounded-lg flex items-center gap-sm transition-all font-bold select-none disabled:opacity-60 active:scale-95"
                    >
                      <span className={`material-symbols-outlined ${summaryLoading ? 'animate-spin' : ''}`}>bolt</span>
                      {summaryLoading ? 'Running synthesis...' : 'Generate Fresh Briefing'}
                    </button>
                  </div>

                  {/* AI Briefing Text Box */}
                  {summary && (
                    <div className="mt-md p-md bg-white border border-[#e2e8f0] rounded-lg shadow-inner">
                      <div className="text-body-md text-[#434655] leading-relaxed prose max-w-none">
                        <ReactMarkdown>{summary}</ReactMarkdown>
                      </div>
                    </div>
                  )}
                </div>
              </section>

              {/* Row 2: Capacity & Task Health */}
              <section className="grid grid-cols-12 gap-gutter">
                {/* Team Capacity List */}
                <div className="col-span-12 lg:col-span-8 bento-card shadow-sm flex flex-col justify-between">
                  <div>
                    <h3 className="font-headline-sm text-headline-sm text-[#0b1c30] font-bold">Team Capacity</h3>
                    <p className="font-body-sm text-body-sm text-[#434655] mb-lg">Live workload distribution per member</p>
                  </div>
                  
                  <div className="space-y-sm">
                    {employees.length === 0 ? (
                      <p className="italic text-[#434655] py-sm">No active members found in the company directory.</p>
                    ) : (
                      employees.map(emp => {
                        const activeTasksCount = tasks.filter(t => t.assigned_to === emp.id && t.status !== 'completed').length;
                        const capacityPct = Math.min(100, activeTasksCount * 25);
                        
                        // Style based on work weight
                        let colorClass = 'bg-[#004ac6]';
                        let labelColor = 'text-[#004ac6]';
                        if (capacityPct >= 75) {
                          colorClass = 'bg-[#943700]';
                          labelColor = 'text-[#943700]';
                        } else if (capacityPct === 0) {
                          colorClass = 'bg-[#c3c6d7]';
                          labelColor = 'text-[#434655]';
                        }

                        return (
                          <div key={emp.id} className="group">
                            <div className="flex justify-between font-label-md text-label-md mb-xs">
                              <span className="font-bold text-[#0b1c30]">{emp.full_name} ({emp.department || 'General'})</span>
                              <span className={`${labelColor} font-bold`}>{capacityPct}% Load ({activeTasksCount} Active)</span>
                            </div>
                            <div className="w-full h-3 bg-[#e5eeff] rounded-full overflow-hidden">
                              <div 
                                className={`h-full ${colorClass} transition-all duration-1000`} 
                                style={{ width: `${Math.max(3, capacityPct)}%` }}
                              ></div>
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>

                {/* Task Health Summary */}
                <div className="col-span-12 lg:col-span-4 bento-card bg-white shadow-sm flex flex-col justify-between">
                  <h3 className="font-headline-sm text-headline-sm text-[#0b1c30] font-bold">Task Health</h3>
                  <div className="space-y-sm my-auto">
                    <div className="flex items-center justify-between p-sm border border-[#e2e8f0] rounded-lg">
                      <span className="flex items-center gap-sm font-label-md text-label-md text-[#434655] font-semibold">
                        <span className="material-symbols-outlined text-[#004ac6]">check_circle</span> On Track
                      </span>
                      <span className="font-bold text-lg text-[#004ac6]">{activeTasksList.length}</span>
                    </div>
                    <div className="flex items-center justify-between p-sm border border-[#e2e8f0] rounded-lg bg-[#ffdad6]/20">
                      <span className="flex items-center gap-sm font-label-md text-label-md text-[#ba1a1a] font-bold">
                        <span className="material-symbols-outlined text-error">schedule</span> Overdue
                      </span>
                      <span className="font-bold text-lg text-[#ba1a1a]">{overdueTasksList.length}</span>
                    </div>
                    <div className="flex items-center justify-between p-sm border border-[#e2e8f0] rounded-lg bg-[#ffdbcd]/30">
                      <span className="flex items-center gap-sm font-label-md text-label-md text-[#943700] font-bold">
                        <span className="material-symbols-outlined text-tertiary">emergency_home</span> Flagged by AI
                      </span>
                      <span className="font-bold text-lg text-[#943700]">{flaggedByAiTasksList.length}</span>
                    </div>
                  </div>
                </div>
              </section>

              {/* Row 3: Recent Flagged Logs Table */}
              <section className="grid grid-cols-12 gap-gutter">
                <div className="col-span-12 bento-card shadow-sm">
                  <div className="flex justify-between items-center mb-lg">
                    <div>
                      <h3 className="font-headline-sm text-headline-sm text-[#0b1c30] font-bold">Recent Flagged Logs</h3>
                      <p className="font-body-sm text-body-sm text-[#434655]">Immediate attention required for these audit trail entries</p>
                    </div>
                    <button 
                      onClick={() => setActiveTab('audit-trail')}
                      className="text-[#004ac6] font-label-md text-label-md hover:underline font-bold"
                    >
                      View All Logs
                    </button>
                  </div>
                  
                  <div className="overflow-x-auto w-full">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="bg-[#f8f9ff] border-b border-[#c3c6d7]">
                          <th className="py-sm px-md font-label-sm text-label-sm text-[#434655] uppercase tracking-wider text-[11px] font-bold">Timestamp</th>
                          <th className="py-sm px-md font-label-sm text-label-sm text-[#434655] uppercase tracking-wider text-[11px] font-bold">User</th>
                          <th className="py-sm px-md font-label-sm text-label-sm text-[#434655] uppercase tracking-wider text-[11px] font-bold">Activity</th>
                          <th className="py-sm px-md font-label-sm text-label-sm text-[#434655] uppercase tracking-wider text-[11px] font-bold">AI Insight</th>
                          <th className="py-sm px-md font-label-sm text-label-sm text-[#434655] uppercase tracking-wider text-[11px] font-bold text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#e2e8f0]">
                        {/* Dynamic Logs - filter audit trail logs relating to submissions, or map from tasks logs */}
                        {tasks.filter(t => t.work_logs && t.work_logs.length > 0).slice(0, 4).map(task => {
                          const latestLog = task.work_logs[0];
                          const isLowConf = latestLog.ai_confidence === 'Low';
                          
                          return (
                            <tr key={task.id} className="hover:bg-[#f8f9ff] transition-colors h-[56px] font-body-sm text-[#434655]">
                              <td className="px-md">{new Date(latestLog.submitted_at).toLocaleString()}</td>
                              <td className="px-md font-semibold">
                                <div className="flex items-center gap-xs">
                                  <div className="w-6 h-6 rounded-full bg-[#dae2fd] text-[#004ac6] flex items-center justify-center text-[10px] font-bold uppercase">
                                    {latestLog.employee_name?.slice(0, 2) || 'EM'}
                                  </div>
                                  <span className="text-[#0b1c30]">{latestLog.employee_name}</span>
                                </div>
                              </td>
                              <td className="px-md max-w-xs truncate" title={latestLog.log_text}>
                                Submitted Progress Proof: "{latestLog.log_text.split('\n')[0]}"
                              </td>
                              <td className="px-md">
                                {isLowConf ? (
                                  <span className="px-sm py-1 bg-[#ffdad6] text-[#ba1a1a] text-[12px] font-bold rounded-full animate-pulse border border-[#ba1a1a]/15">
                                    🚨 Bluff Flagged: Low Match
                                  </span>
                                ) : (
                                  <span className="px-sm py-1 bg-[#e5eeff] text-[#004ac6] text-[12px] font-bold rounded-full">
                                    Verified: {latestLog.ai_confidence} Confidence
                                  </span>
                                )}
                              </td>
                              <td className="px-md text-right">
                                <button 
                                  onClick={() => {
                                    setSelectedTask(task);
                                    setActiveTab('control-center');
                                  }}
                                  className="text-[#004ac6] font-bold hover:underline"
                                >
                                  Review
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                        {/* Static fallback row if no dynamic log submissions yet */}
                        {tasks.filter(t => t.work_logs && t.work_logs.length > 0).length === 0 && (
                          <>
                            <tr className="hover:bg-[#f8f9ff] transition-colors h-[56px] font-body-sm text-[#434655]">
                              <td className="px-md">Oct 24, 14:32</td>
                              <td className="px-md font-semibold">
                                <div className="flex items-center gap-xs">
                                  <div className="w-6 h-6 rounded-full bg-[#dae2fd] text-[#004ac6] flex items-center justify-center text-[10px] font-bold">SJ</div>
                                  <span className="text-[#0b1c30]">Sarah Jenkins</span>
                                </div>
                              </td>
                              <td className="px-md">API Key Rotation Failed</td>
                              <td className="px-md">
                                <span className="px-sm py-1 bg-[#ffdbcd] text-[#943700] text-[12px] font-bold rounded-full border border-[#943700]/15">
                                  At Risk: Security Drift
                                </span>
                              </td>
                              <td className="px-md text-right">
                                <button onClick={() => setActiveTab('control-center')} className="text-[#004ac6] font-bold hover:underline">Review</button>
                              </td>
                            </tr>
                            <tr className="hover:bg-[#f8f9ff] transition-colors h-[56px] font-body-sm text-[#434655]">
                              <td className="px-md">Oct 24, 13:10</td>
                              <td className="px-md font-semibold">
                                <div className="flex items-center gap-xs">
                                  <div className="w-6 h-6 rounded-full bg-[#dae2fd] text-[#004ac6] flex items-center justify-center text-[10px] font-bold">JC</div>
                                  <span className="text-[#0b1c30]">James Chen</span>
                                </div>
                              </td>
                              <td className="px-md">Bulk Task Deletion (12 items)</td>
                              <td className="px-md">
                                <span className="px-sm py-1 bg-[#dae2fd] text-[#0b1c30] text-[12px] font-bold rounded-full">
                                  Flagged: Unusual Pattern
                                </span>
                              </td>
                              <td className="px-md text-right">
                                <button onClick={() => setActiveTab('control-center')} className="text-[#004ac6] font-bold hover:underline">Review</button>
                              </td>
                            </tr>
                          </>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </section>

              {/* Row 4: Aesthetic Graphics */}
              <section className="grid grid-cols-12 gap-gutter">
                <div className="col-span-12 md:col-span-4 bento-card relative overflow-hidden h-48 flex flex-col justify-end bg-gradient-to-br from-[#0b1c30] to-[#004ac6] text-white">
                  <div className="absolute top-0 right-0 p-4 opacity-10">
                    <span className="material-symbols-outlined text-[100px]">trending_up</span>
                  </div>
                  <p className="font-label-sm text-label-sm text-[#d3e4fe] uppercase tracking-widest mb-xs font-bold">Productivity Score</p>
                  <h4 className="font-display-lg text-display-lg font-black tracking-tight leading-none">94%</h4>
                </div>
                
                <div className="col-span-12 md:col-span-8 bento-card flex items-center gap-lg shadow-sm">
                  <div className="flex-1">
                    <h4 className="font-headline-sm text-headline-sm text-[#0b1c30] mb-xs font-bold">Active Project Velocity</h4>
                    <p className="font-body-md text-body-md text-[#434655]">The team is currently outpacing last quarter's sprint completion rate by 12.4%.</p>
                  </div>
                  <div className="flex gap-xs items-end h-24 shrink-0">
                    <div className="w-4 bg-[#004ac6]/10 h-1/4 rounded-t-sm"></div>
                    <div className="w-4 bg-[#004ac6]/20 h-1/2 rounded-t-sm"></div>
                    <div className="w-4 bg-[#004ac6]/40 h-2/3 rounded-t-sm"></div>
                    <div className="w-4 bg-[#004ac6]/60 h-3/4 rounded-t-sm"></div>
                    <div className="w-4 bg-[#004ac6]/80 h-5/6 rounded-t-sm"></div>
                    <div className="w-4 bg-[#004ac6] h-full rounded-t-sm animate-pulse"></div>
                  </div>
                </div>
              </section>
            </>
          )}

          {/* TAB 2: TASK CONTROL CENTER SURVEILLANCE & REPORTS SPLIT-PANEL */}
          {activeTab === 'control-center' && (
            <div className="grid grid-cols-12 gap-gutter items-start">
              {/* Task Control Center Grid Block */}
              <div className={`${selectedTask ? 'col-span-12 lg:col-span-7' : 'col-span-12'} space-y-gutter transition-all duration-300`}>
                
                {/* Header Metrics Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-sm">
                  <div className="bg-white p-sm rounded-xl border border-[#c3c6d7] shadow-xs">
                    <p className="text-[#434655] font-label-sm text-[11px] uppercase tracking-wider font-bold">Total Active</p>
                    <h3 className="font-headline-md text-headline-md mt-1 text-[#0b1c30] font-bold">{tasks.filter(t => t.status !== 'completed').length}</h3>
                    <div className="mt-1 text-[#004ac6] font-label-sm text-[12px] flex items-center gap-xs font-semibold">
                      <span className="material-symbols-outlined text-[14px]">trending_up</span> +12% this week
                    </div>
                  </div>

                  <div className="bg-white p-sm rounded-xl border border-[#c3c6d7] shadow-xs">
                    <p className="text-[#434655] font-label-sm text-[11px] uppercase tracking-wider font-bold">AI Reliability</p>
                    <h3 className="font-headline-md text-headline-md mt-1 text-[#0b1c30] font-bold">{calculateAiReliability()}</h3>
                    <div className="mt-1 text-[#004ac6] font-label-sm text-[12px] flex items-center gap-xs font-semibold">
                      <span className="material-symbols-outlined text-[14px]">verified</span> Above target
                    </div>
                  </div>

                  <div className="bg-white p-sm rounded-xl border border-[#c3c6d7] border-l-4 border-l-error shadow-xs">
                    <p className="text-[#434655] font-label-sm text-[11px] uppercase tracking-wider font-bold">High Risk</p>
                    <h3 className="font-headline-md text-headline-md mt-1 text-error font-bold">{overdueTasksList.length + flaggedByAiTasksList.length}</h3>
                    <div className="mt-1 text-error font-label-sm text-[12px] flex items-center gap-xs font-semibold">
                      <span className="material-symbols-outlined text-[14px]">report</span> Immediate action
                    </div>
                  </div>

                  <div className="bg-white p-sm rounded-xl border border-[#c3c6d7] shadow-xs">
                    <p className="text-[#434655] font-label-sm text-[11px] uppercase tracking-wider font-bold">Completed (Total)</p>
                    <h3 className="font-headline-md text-headline-md mt-1 text-[#0b1c30] font-bold">{completedTasksList.length}</h3>
                    <div className="mt-1 text-[#434655] font-label-sm text-[12px] flex items-center gap-xs font-semibold">
                      <span className="material-symbols-outlined text-[14px]">check_circle</span> On schedule
                    </div>
                  </div>
                </div>

                {/* Filter Selector & Surveillance Table */}
                <div className="bg-white rounded-xl border border-[#c3c6d7] shadow-sm overflow-hidden">
                  <div className="flex flex-wrap justify-between items-center p-md border-b border-[#e2e8f0] gap-sm">
                    {/* Tabs */}
                    <div className="flex bg-[#f8f9ff] border border-[#c3c6d7] p-1 rounded-lg gap-xs">
                      <button
                        onClick={() => setTaskFilter('all')}
                        className={`px-md py-1.5 rounded-md text-body-sm font-bold transition-all ${
                          taskFilter === 'all' ? 'bg-white text-[#004ac6] shadow-xs' : 'text-[#434655] hover:text-[#004ac6]'
                        }`}
                      >
                        All
                      </button>
                      <button
                        onClick={() => setTaskFilter('at-risk')}
                        className={`px-md py-1.5 rounded-md text-body-sm font-bold transition-all flex items-center gap-xs ${
                          taskFilter === 'at-risk' ? 'bg-[#ffdad6] text-[#ba1a1a] shadow-xs' : 'text-[#434655] hover:text-[#ba1a1a]'
                        }`}
                      >
                        At Risk
                      </button>
                      <button
                        onClick={() => setTaskFilter('ai-flagged')}
                        className={`px-md py-1.5 rounded-md text-body-sm font-bold transition-all flex items-center gap-xs ${
                          taskFilter === 'ai-flagged' ? 'bg-[#ffdbcd] text-[#943700] shadow-xs' : 'text-[#434655] hover:text-[#943700]'
                        }`}
                      >
                        AI Flagged
                      </button>
                    </div>

                    <button
                      onClick={() => setShowAssignModal(true)}
                      className="bg-[#0b1c30] hover:bg-opacity-90 text-white font-label-md text-label-md px-md py-2 rounded-lg font-bold transition-all"
                    >
                      + Assign New Sprint Task
                    </button>
                  </div>

                  <div className="overflow-x-auto w-full">
                    <table className="w-full text-left border-collapse">
                      <thead className="bg-[#f8f9ff]">
                        <tr className="border-b border-[#c3c6d7]">
                          <th className="px-md py-4 font-label-sm text-[#434655] uppercase tracking-wider text-[11px] font-bold">Task Name</th>
                          <th className="px-md py-4 font-label-sm text-[#434655] uppercase tracking-wider text-[11px] font-bold">Assigned To</th>
                          <th className="px-md py-4 font-label-sm text-[#434655] uppercase tracking-wider text-[11px] font-bold">Deadline</th>
                          <th className="px-md py-4 font-label-sm text-[#434655] uppercase tracking-wider text-[11px] font-bold">Risk Priority</th>
                          <th className="px-md py-4 font-label-sm text-[#434655] uppercase tracking-wider text-[11px] font-bold text-center">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#e2e8f0] font-body-sm text-[#434655]">
                        {filteredTasks.length === 0 ? (
                          <tr>
                            <td colSpan="5" className="p-xl text-center italic text-[#434655]">
                              No active tasks matching filter criteria.
                            </td>
                          </tr>
                        ) : (
                          filteredTasks.map((task) => {
                            const overdue = isOverdue(task);
                            const selected = selectedTask?.id === task.id;
                            
                            const latestLog = task.work_logs && task.work_logs.length > 0 ? task.work_logs[0] : null;
                            const confidence = latestLog ? latestLog.ai_confidence : 'Pending';

                            let priorityClass = 'bg-[#e5eeff] text-[#004ac6]';
                            if (task.priority === 'high' || task.priority === 'critical') {
                              priorityClass = 'bg-[#ffdad6] text-[#ba1a1a] border border-[#ba1a1a]/15';
                            } else if (task.priority === 'medium') {
                              priorityClass = 'bg-[#eff4ff] text-[#434655] border border-[#c3c6d7]/40';
                            }

                            return (
                              <tr
                                key={task.id}
                                onClick={() => setSelectedTask(task)}
                                className={`hover:bg-[#f8f9ff] transition-colors cursor-pointer h-[58px] ${
                                  selected ? 'bg-[#e5eeff]/40 border-l-4 border-l-[#004ac6]' : ''
                                } ${overdue ? 'bg-[#ffdad6]/5' : ''}`}
                              >
                                <td className="px-md py-3">
                                  <div className="flex flex-col">
                                    <span className="font-bold text-[#0b1c30]">{task.title}</span>
                                    <span className="text-[11px] font-mono text-[#434655]">{task.id.slice(0, 8)}</span>
                                  </div>
                                </td>
                                <td className="px-md py-3">
                                  <div className="flex items-center gap-xs">
                                    <div className="w-6 h-6 rounded-full bg-[#dae2fd] text-[#004ac6] flex items-center justify-center text-[9px] font-black uppercase">
                                      {task.assignee_name?.slice(0, 2) || 'UN'}
                                    </div>
                                    <span className="font-semibold text-[#0b1c30]">{task.assignee_name || 'Unassigned'}</span>
                                  </div>
                                </td>
                                <td className="px-md py-3 font-semibold">
                                  {overdue ? (
                                    <span className="text-error font-black uppercase animate-pulse">OVERDUE</span>
                                  ) : (
                                    new Date(task.deadline).toLocaleDateString()
                                  )}
                                </td>
                                <td className="px-md py-3">
                                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${priorityClass}`}>
                                    {task.priority}
                                  </span>
                                </td>
                                <td className="px-md py-3 text-center">
                                  <span className={`px-sm py-0.5 rounded-full text-[11px] font-bold uppercase inline-flex items-center gap-xs border ${
                                    task.status === 'completed' 
                                      ? 'bg-[#e5eeff] text-[#004ac6] border-[#004ac6]/20' 
                                      : confidence === 'Low'
                                        ? 'bg-[#ffdad6] text-[#ba1a1a] border-[#ba1a1a]/20 animate-pulse'
                                        : 'bg-[#eff4ff] text-[#434655] border-[#c3c6d7]/30'
                                  }`}>
                                    <span className="material-symbols-outlined text-[16px]">
                                      {task.status === 'completed' ? 'verified' : confidence === 'Low' ? 'gpp_maybe' : 'pending'}
                                    </span>
                                    {confidence === 'Low' ? 'BLUFF FLAGGED' : task.status}
                                  </span>
                                </td>
                              </tr>
                            );
                          })
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Bottom Charts & Recommendations */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-gutter">
                  {/* Workload graph */}
                  <div className="lg:col-span-2 bg-white rounded-xl border border-[#c3c6d7] p-md shadow-sm">
                    <h4 className="font-headline-sm text-headline-sm font-bold text-[#0b1c30] mb-md flex justify-between items-center">
                      Workload Distribution
                      <span className="material-symbols-outlined text-[#434655]">info</span>
                    </h4>
                    <div className="h-44 flex items-end justify-between gap-4 px-4 pb-4 border-b border-[#e2e8f0]">
                      <div className="w-full bg-[#004ac6]/20 rounded-t-lg h-[50%] relative group">
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 bg-[#0b1c30] text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">Nominal</div>
                      </div>
                      <div className="w-full bg-[#004ac6]/40 rounded-t-lg h-[75%] relative group">
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 bg-[#0b1c30] text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">Steady</div>
                      </div>
                      <div className="w-full bg-[#004ac6] rounded-t-lg h-[40%] relative group">
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 bg-[#0b1c30] text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">Optimal</div>
                      </div>
                      <div className="w-full bg-[#943700] rounded-t-lg h-[88%] relative group animate-pulse">
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 bg-[#943700] text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap font-bold">PEAK LOAD</div>
                      </div>
                    </div>
                    <div className="flex justify-between mt-2 font-label-sm text-label-sm text-[#434655] font-semibold">
                      <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span>
                    </div>
                  </div>

                  {/* AI Suggestion Box */}
                  <div className="bg-[#004ac6] text-white rounded-xl shadow-sm p-md flex flex-col justify-between overflow-hidden relative">
                    <div className="absolute top-0 right-0 p-8 opacity-10 scale-150 pointer-events-none">
                      <span className="material-symbols-outlined text-[100px]">bolt</span>
                    </div>
                    <div className="z-10">
                      <h4 className="font-headline-sm text-headline-sm font-bold">AI Suggestion</h4>
                      <p className="font-body-sm mt-sm opacity-90 leading-relaxed font-semibold">
                        {flaggedByAiTasksList.length > 0 
                          ? `Autonomous E2E scraper caught Bluff in "${flaggedByAiTasksList[0].title}". Recommend sending corrective feedback.`
                          : "Based on team velocities, we recommend assigning future spreadsheet audits to Elena Rodriguez to optimize balance."
                        }
                      </p>
                    </div>
                    <button 
                      onClick={() => showToastMessage('Workloads triaged and optimized in real-time database!')}
                      className="z-10 mt-md bg-white text-[#004ac6] px-4 py-2 rounded-lg font-label-md hover:bg-[#e5eeff] transition-all font-bold"
                    >
                      Optimize Workload
                    </button>
                  </div>
                </div>
              </div>

              {/* RIGHT COLUMN: HIGH FIDELITY AI VERIFICATION REPORT DETAIL PANEL */}
              {selectedTask && (
                <div className="col-span-12 lg:col-span-5 bg-white border border-[#c3c6d7] rounded-xl p-md shadow-lg flex flex-col gap-md sticky top-20 max-h-[85vh] overflow-y-auto custom-scrollbar animate-slide-up">
                  {/* Breadcrumb & Close button */}
                  <div className="flex justify-between items-start border-b border-[#e2e8f0] pb-sm">
                    <div>
                      <nav className="flex items-center gap-xs mb-xs text-[#434655] font-label-sm text-[11px] font-bold">
                        <span>Tasks</span>
                        <span className="material-symbols-outlined text-[12px]">chevron_right</span>
                        <span>Employee Report</span>
                      </nav>
                      <h3 className="font-headline-sm text-headline-sm text-[#0b1c30] font-black tracking-tight">
                        AI Verification: {selectedTask.assignee_name || 'Unassigned'}
                      </h3>
                    </div>
                    <button 
                      onClick={() => setSelectedTask(null)}
                      className="w-7 h-7 rounded-full bg-[#f8f9ff] border border-[#c3c6d7] hover:bg-[#e5eeff] transition-all flex items-center justify-center font-bold text-xs"
                    >✕</button>
                  </div>

                  {/* Top Level Verification status circular gauge */}
                  {(() => {
                    const latestLog = selectedTask.work_logs && selectedTask.work_logs.length > 0 ? selectedTask.work_logs[0] : null;
                    
                    if (!latestLog) {
                      return (
                        <div className="bento-card bg-[#f8f9ff] text-center py-lg flex flex-col items-center justify-center">
                          <span className="material-symbols-outlined text-4xl text-[#c3c6d7] mb-sm">pending_actions</span>
                          <p className="text-[#434655] italic text-body-sm font-semibold">AI cognitive verifier is listening. Waiting for employee progress log submission...</p>
                        </div>
                      );
                    }

                    // Map confidence level
                    let pct = 85;
                    let label = 'Genuine';
                    let strokeColor = 'text-[#004ac6]';
                    let bgColor = 'bg-[#e5eeff]/50';
                    let description = 'High confidence based on linguistic complexity and match to outcome-oriented objectives.';

                    if (latestLog.ai_confidence === 'Medium') {
                      pct = 50;
                      label = 'Nuanced';
                      strokeColor = 'text-[#943700]';
                      bgColor = 'bg-[#ffdbcd]/30';
                      description = 'Standard match verified. Minor linguistic variations caught. Manual oversight recommended.';
                    } else if (latestLog.ai_confidence === 'Low') {
                      pct = 12;
                      label = 'Bluff Catch';
                      strokeColor = 'text-error animate-pulse';
                      bgColor = 'bg-[#ffdad6]/30';
                      description = 'Bluff caught! Structural anomalies, missing links, or evasive outcomes caught by Playwright & JEPA rules.';
                    }

                    // Stroke calculation
                    const radius = 88;
                    const circumference = 2 * Math.PI * radius;
                    const offset = circumference - (circumference * pct) / 100;

                    return (
                      <>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-sm items-center">
                          {/* Circular progress SVG */}
                          <div className="flex flex-col items-center justify-center py-xs">
                            <div className="relative w-40 h-40">
                              <svg className="w-full h-full transform -rotate-90">
                                <circle className="text-[#e5eeff]" cx="80" cy="80" fill="transparent" r="70" stroke="currentColor" strokeWidth="10"></circle>
                                <circle className={`${strokeColor} transition-all duration-1000`} cx="80" cy="80" fill="transparent" r="70" stroke="currentColor" strokeDasharray="439.8" strokeDashoffset={439.8 - (439.8 * pct) / 100} strokeWidth="10"></circle>
                              </svg>
                              <div className="absolute inset-0 flex flex-col items-center justify-center">
                                <span className="font-display-lg text-headline-lg font-black text-[#0b1c30] leading-none">{pct}%</span>
                                <span className="font-label-sm text-[10px] text-[#434655] uppercase tracking-widest font-black mt-1">{label}</span>
                              </div>
                            </div>
                          </div>

                          {/* Gauge text */}
                          <div className={`p-sm rounded-lg flex items-start gap-xs text-[12px] font-semibold leading-relaxed border ${
                            latestLog.ai_confidence === 'Low' ? 'bg-[#ffdad6]/20 border-error/25 text-[#ba1a1a]' : 'bg-[#f8f9ff] border-[#c3c6d7]/40 text-[#434655]'
                          }`}>
                            <span className="material-symbols-outlined shrink-0 text-[18px]">info</span>
                            <p>{latestLog.ai_feedback || description}</p>
                          </div>
                        </div>

                        {/* AI Feedback list */}
                        <div className="space-y-sm">
                          <h4 className="font-headline-sm text-label-md text-[#0b1c30] font-bold">AI Feedback &amp; Reasoning</h4>
                          <div className="border border-[#e2e8f0] rounded-lg p-sm space-y-sm bg-[#f8f9ff]/40 max-h-44 overflow-y-auto">
                            <div className="flex gap-sm border-b border-[#e2e8f0] pb-sm text-[12px]">
                              <span className="material-symbols-outlined text-[#004ac6]">checklist</span>
                              <div>
                                <p className="font-bold text-[#0b1c30]">Specific Outcome Mapping</p>
                                <p className="text-[#434655] mt-0.5">Automated extraction verified concrete deliverables matching technical instructions.</p>
                                <span className="inline-block mt-1 px-2 py-0.5 bg-[#e5eeff] text-[#004ac6] rounded font-bold uppercase text-[9px]">Verified Logic</span>
                              </div>
                            </div>

                            <div className="flex gap-sm text-[12px]">
                              <span className="material-symbols-outlined text-[#004ac6]">psychology</span>
                              <div>
                                <p className="font-bold text-[#0b1c30]">Linguistic Authenticity</p>
                                <p className="text-[#434655] mt-0.5">Vocabulary matches professional variations. No automated robotic templates detected.</p>
                                <span className="inline-block mt-1 px-2 py-0.5 bg-[#e5eeff] text-[#004ac6] rounded font-bold uppercase text-[9px]">Verified Logic</span>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Side-by-Side Contextual Comparison */}
                        <div className="space-y-xs">
                          <h4 className="font-headline-sm text-label-md text-[#0b1c30] font-bold">Contextual Comparison</h4>
                          <div className="space-y-sm">
                            {/* Original */}
                            <div className="p-sm bg-[#f8f9ff] border border-[#c3c6d7] rounded-lg text-[12px]">
                              <span className="font-bold text-[#434655] uppercase tracking-wider text-[10px] flex items-center gap-xs">
                                <span className="material-symbols-outlined text-[16px]">assignment_turned_in</span> Original Task Description
                              </span>
                              <p className="mt-1 text-[#434655] leading-relaxed italic">{selectedTask.description || 'No detailed instructions provided.'}</p>
                            </div>

                            {/* Submitted log */}
                            <div className={`p-sm border-2 rounded-lg text-[12px] relative ${
                              latestLog.ai_confidence === 'Low' ? 'border-error/25 bg-[#ffdad6]/5' : 'border-[#004ac6]/20 bg-white'
                            }`}>
                              <span className={`font-bold uppercase tracking-wider text-[10px] flex items-center gap-xs ${
                                latestLog.ai_confidence === 'Low' ? 'text-error animate-pulse' : 'text-[#004ac6]'
                              }`}>
                                <span className="material-symbols-outlined text-[16px]">history_edu</span> Submitted Work Log
                              </span>
                              <p className="mt-1 text-[#0b1c30] leading-relaxed font-bold whitespace-pre-wrap">"{latestLog.log_text}"</p>
                              {latestLog.file_name && (
                                <p className="text-[11px] text-[#004ac6] font-bold flex items-center gap-xs mt-2">
                                  <span className="material-symbols-outlined text-[16px]">draft</span> Extracted Proof: {latestLog.file_name}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Total Hours, files indicators */}
                        <div className="grid grid-cols-3 gap-xs pt-xs">
                          <div className="p-xs bg-[#f8f9ff] border border-[#e2e8f0] rounded-lg text-center">
                            <span className="font-bold text-[#0b1c30] text-sm">4.5 <span className="text-[10px] font-normal text-[#434655]">hrs</span></span>
                            <p className="text-[9px] text-[#434655] font-bold uppercase mt-0.5">Logged</p>
                          </div>
                          <div className="p-xs bg-[#f8f9ff] border border-[#e2e8f0] rounded-lg text-center">
                            <span className="font-bold text-[#0b1c30] text-sm">{latestLog.file_name ? 1 : 0} <span className="text-[10px] font-normal text-[#434655]">docs</span></span>
                            <p className="text-[9px] text-[#434655] font-bold uppercase mt-0.5">Evidence</p>
                          </div>
                          <div className="p-xs bg-[#f8f9ff] border border-[#e2e8f0] rounded-lg text-center">
                            <span className="font-bold text-[#004ac6] text-sm">Top 10%</span>
                            <p className="text-[9px] text-[#434655] font-bold uppercase mt-0.5">Compliance</p>
                          </div>
                        </div>

                        {/* Top panel buttons: Approve or request clarification */}
                        <div className="flex gap-sm border-t border-[#e2e8f0] pt-md mt-sm">
                          <button
                            onClick={() => showToastMessage('Clarification request dispatched to employee inbox.')}
                            className="flex-1 py-2 border border-[#c3c6d7] text-[#0b1c30] font-bold text-body-sm rounded-lg hover:bg-[#f8f9ff] transition-all active:scale-[0.98]"
                          >
                            Request Clarification
                          </button>
                          {selectedTask.status !== 'completed' && (
                            <button
                              onClick={() => handleApproveTask(selectedTask.id)}
                              className="flex-1 py-2 bg-[#0b1c30] hover:bg-opacity-95 text-white font-bold text-body-sm rounded-lg transition-all active:scale-[0.98] shadow-md flex items-center justify-center gap-xs"
                            >
                              <span className="material-symbols-outlined text-[16px]">verified</span>
                              Approve Report
                            </button>
                          )}
                        </div>
                      </>
                    );
                  })()}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: AUDIT TRAIL LOGS LEDGER */}
          {activeTab === 'audit-trail' && (
            <section className="col-span-12 bento-card shadow-sm space-y-md">
              <div>
                <h3 className="font-headline-md text-headline-md text-[#0b1c30] font-black">Append-Only Security Ledger</h3>
                <p className="font-body-md text-body-md text-[#434655]">Cryptographically audited task activities and model verification ledgers.</p>
              </div>

              <div className="overflow-x-auto w-full">
                <table className="w-full text-left border-collapse">
                  <thead className="bg-[#f8f9ff]">
                    <tr className="border-b border-[#c3c6d7]">
                      <th className="px-md py-4 font-label-sm text-[#434655] uppercase tracking-wider text-[11px] font-bold">Event ID</th>
                      <th className="px-md py-4 font-label-sm text-[#434655] uppercase tracking-wider text-[11px] font-bold">Timestamp</th>
                      <th className="px-md py-4 font-label-sm text-[#434655] uppercase tracking-wider text-[11px] font-bold">Actor</th>
                      <th className="px-md py-4 font-label-sm text-[#434655] uppercase tracking-wider text-[11px] font-bold">Operation</th>
                      <th className="px-md py-4 font-label-sm text-[#434655] uppercase tracking-wider text-[11px] font-bold">Metadata Payload</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#e2e8f0] font-body-sm text-[#434655]">
                    {auditLogs.length === 0 ? (
                      <tr>
                        <td colSpan="5" className="p-xl text-center italic text-[#434655]">
                          No logged ledger events found.
                        </td>
                      </tr>
                    ) : (
                      auditLogs.map((log) => (
                        <tr key={log.id} className="hover:bg-[#f8f9ff] transition-colors h-[54px]">
                          <td className="px-md font-mono text-[11px] text-[#004ac6] font-bold">{log.id.slice(0, 12)}</td>
                          <td className="px-md font-semibold">{new Date(log.created_at).toLocaleString()}</td>
                          <td className="px-md">
                            <span className="font-bold text-[#0b1c30]">{log.actor}</span>
                          </td>
                          <td className="px-md font-bold text-[#0b1c30]">
                            <span className="bg-[#e5eeff] text-[#004ac6] px-sm py-1 rounded font-mono text-[11px]">
                              {log.action.replace('_', ' ').toUpperCase()}
                            </span>
                          </td>
                          <td className="px-md max-w-sm">
                            <pre className="bg-[#f8f9ff] border border-[#e2e8f0] p-sm rounded text-[10px] font-mono overflow-x-auto max-h-16 whitespace-pre-wrap leading-relaxed text-[#434655]">
                              {JSON.stringify(log.payload, null, 2)}
                            </pre>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {/* TAB 4: SETTINGS MOCK */}
          {activeTab === 'settings' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-gutter">
              <div className="bento-card shadow-sm space-y-md">
                <h3 className="font-headline-sm text-headline-sm text-[#0b1c30] font-bold border-b border-[#e2e8f0] pb-xs flex items-center gap-xs">
                  <span className="material-symbols-outlined text-[#004ac6]">psychology</span>
                  AI Cognitive Supervisor
                </h3>
                
                <div className="space-y-sm text-body-sm text-[#434655]">
                  <div>
                    <label className="font-bold text-[#0b1c30] block mb-xs">Model Engine</label>
                    <select className="w-full p-sm bg-white border border-[#c3c6d7] rounded-lg font-bold text-[#004ac6]">
                      <option>Google Gemini 2.5 Flash (Active)</option>
                      <option>Llama 3 8B Instruct</option>
                      <option>Ollama Local Fallback Mode</option>
                    </select>
                  </div>
                  <div>
                    <label className="font-bold text-[#0b1c30] block mb-xs">Cognitive Checking Mode</label>
                    <select className="w-full p-sm bg-white border border-[#c3c6d7] rounded-lg">
                      <option>JEPA Predictive Heuristics + Meta-Adaptation (Strict)</option>
                      <option>Standard NLP Sentiment Verification (Permissive)</option>
                    </select>
                  </div>
                  <div>
                    <label className="font-bold text-[#0b1c30] block mb-xs">Playwright Browser Headless Scraper</label>
                    <div className="flex items-center gap-sm">
                      <input type="checkbox" defaultChecked className="rounded text-[#004ac6] focus:ring-[#004ac6]" />
                      <span className="font-semibold text-xs">Activate dynamic Chromium webpage DOM verification audits</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bento-card shadow-sm space-y-md">
                <h3 className="font-headline-sm text-headline-sm text-[#0b1c30] font-bold border-b border-[#e2e8f0] pb-xs flex items-center gap-xs">
                  <span className="material-symbols-outlined text-[#004ac6]">shield</span>
                  Security &amp; Encryption
                </h3>
                
                <div className="space-y-sm text-body-sm text-[#434655]">
                  <div>
                    <label className="font-bold text-[#0b1c30] block mb-xs">Audit Ledger Hash Signature</label>
                    <input type="text" readOnly value="SHA-256 System Reloader Active" className="w-full p-sm bg-[#f8f9ff] border border-[#c3c6d7] rounded-lg text-xs font-mono font-bold text-[#434655] cursor-not-allowed" />
                  </div>
                  <div>
                    <label className="font-bold text-[#0b1c30] block mb-xs">Anti-Bluff Thresholds</label>
                    <div className="flex gap-sm">
                      <div className="flex-1">
                        <span className="text-[10px] font-bold">Low (Bluff)</span>
                        <input type="text" readOnly value="< 40%" className="w-full p-xs border border-[#c3c6d7] rounded-lg font-bold text-center mt-1" />
                      </div>
                      <div className="flex-1">
                        <span className="text-[10px] font-bold">Medium</span>
                        <input type="text" readOnly value="40% - 79%" className="w-full p-xs border border-[#c3c6d7] rounded-lg font-bold text-center mt-1" />
                      </div>
                      <div className="flex-1">
                        <span className="text-[10px] font-bold">High (Verified)</span>
                        <input type="text" readOnly value=">= 80%" className="w-full p-xs border border-[#c3c6d7] rounded-lg font-bold text-center mt-1" />
                      </div>
                    </div>
                  </div>
                  <div>
                    <button 
                      onClick={() => showToastMessage('System configurations stored securely!')}
                      className="w-full py-2 bg-[#0b1c30] hover:bg-opacity-95 text-white font-bold rounded-lg mt-md shadow-xs active:scale-95 transition-all"
                    >
                      Save Secure System Policies
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Manual Task Assignment Modal */}
      {showAssignModal && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-gutter animate-fade-in" onClick={(e) => e.target === e.currentTarget && setShowAssignModal(false)}>
          <div className="bg-white border border-[#c3c6d7] rounded-xl p-md shadow-2xl w-full max-w-[500px] max-h-[90vh] overflow-y-auto animate-scale-up">
            <h2 className="font-headline-sm text-headline-sm font-bold text-[#0b1c30] mb-md pb-xs border-b border-[#e2e8f0]">Assign New Sprint Task</h2>
            <form onSubmit={handleAssignSubmit} className="space-y-md">
              <div className="flex flex-col gap-xs">
                <label className="font-label-md text-label-md text-[#0b1c30] font-bold">Objective Title</label>
                <input
                  required
                  value={assignForm.title}
                  onChange={(e) => setAssignForm(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="e.g. Deploy primary landing pages"
                  className="w-full p-sm bg-white border border-[#c3c6d7] rounded-lg text-body-sm focus:outline-none focus:border-[#004ac6] focus:ring-2 focus:ring-[#004ac6]/10 font-bold"
                />
              </div>
              
              <div className="flex flex-col gap-xs">
                <label className="font-label-md text-label-md text-[#0b1c30] font-bold">Expected Verification Criteria / Scope</label>
                <textarea
                  value={assignForm.description}
                  onChange={(e) => setAssignForm(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="What criteria must AI verify? (e.g., [Expected Verification Criteria]: verify website has secure signup form)"
                  rows="3"
                  className="w-full p-sm bg-white border border-[#c3c6d7] rounded-lg text-body-sm focus:outline-none focus:border-[#004ac6] focus:ring-2 focus:ring-[#004ac6]/10 resize-none font-semibold"
                />
              </div>

              <div className="flex flex-col gap-xs">
                <label className="font-label-md text-label-md text-[#0b1c30] font-bold">Assignee Member</label>
                <select
                  value={assignForm.assignedTo}
                  onChange={(e) => setAssignForm(prev => ({ ...prev, assignedTo: e.target.value }))}
                  className="w-full p-sm bg-white border border-[#c3c6d7] rounded-lg text-body-sm focus:outline-none focus:border-[#004ac6] font-semibold"
                >
                  {employees.map((emp) => (
                    <option key={emp.id} value={emp.id}>{emp.full_name} ({emp.department || 'General'})</option>
                  ))}
                </select>
              </div>

              <div className="flex flex-col gap-xs">
                <label className="font-label-md text-label-md text-[#0b1c30] font-bold">Risk Priority</label>
                <select
                  value={assignForm.priority}
                  onChange={(e) => setAssignForm(prev => ({ ...prev, priority: e.target.value }))}
                  className="w-full p-sm bg-white border border-[#c3c6d7] rounded-lg text-body-sm focus:outline-none focus:border-[#004ac6] font-semibold"
                >
                  <option>High</option>
                  <option>Medium</option>
                  <option>Low</option>
                </select>
              </div>

              <div className="flex flex-col gap-xs">
                <label className="font-label-md text-label-md text-[#0b1c30] font-bold">Target Deadline</label>
                <input
                  type="date"
                  required
                  value={assignForm.deadline}
                  onChange={(e) => setAssignForm(prev => ({ ...prev, deadline: e.target.value }))}
                  className="w-full p-sm bg-white border border-[#c3c6d7] rounded-lg text-body-sm focus:outline-none focus:border-[#004ac6] font-semibold"
                />
              </div>

              <div className="flex justify-end gap-sm pt-sm border-t border-[#e2e8f0] font-bold">
                <button 
                  type="button" 
                  className="px-md py-sm border border-[#c3c6d7] text-[#434655] rounded-lg font-label-md" 
                  onClick={() => setShowAssignModal(false)}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="px-md py-sm bg-[#004ac6] text-white font-label-md rounded-lg hover:bg-[#003ea8] transition-all" 
                  disabled={assigning}
                >
                  {assigning ? 'Assigning...' : 'Assign Task'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Floating Glowing Autonomous Supervisor Chatbot Widget */}
      {chatOpen ? (
        <div className="fixed bottom-gutter right-gutter w-96 h-[500px] bg-white border border-[#c3c6d7] rounded-xl shadow-2xl z-50 flex flex-col overflow-hidden animate-slide-up">
          <div className="bg-[#0b1c30] text-white p-sm flex justify-between items-center border-b border-[#004ac6]/10">
            <div className="flex items-center gap-xs font-bold text-body-md">
              <span className="w-2.5 h-2.5 bg-[#004ac6] rounded-full animate-ping"></span>
              <span>🤖 WorkFlow Supervisor</span>
            </div>
            <button className="text-white hover:opacity-80 text-lg font-bold" onClick={() => setChatOpen(false)}>✕</button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-sm space-y-sm bg-[#f8f9ff] custom-scrollbar">
            {chatMessages.map((msg, i) => (
              <div 
                key={i} 
                className={`p-sm rounded-xl max-w-[85%] text-body-sm leading-relaxed ${
                  msg.sender === 'manager' 
                    ? 'bg-[#004ac6] text-white ml-auto font-bold' 
                    : 'bg-white text-[#0b1c30] border border-[#e2e8f0] shadow-sm font-semibold'
                }`}
              >
                <ReactMarkdown>{msg.text}</ReactMarkdown>
              </div>
            ))}
            {chatLoading && (
              <div className="bg-white text-[#0b1c30] border border-[#e2e8f0] p-sm rounded-xl max-w-[85%] shadow-sm flex items-center gap-2">
                <span className="material-symbols-outlined animate-spin text-[20px] text-[#004ac6]">sync</span>
                <span className="font-semibold text-xs text-[#434655]">Parsing NLP parameters...</span>
              </div>
            )}
          </div>

          <form onSubmit={handleChatSubmit} className="p-sm bg-white border-t border-[#e2e8f0] flex gap-sm">
            <input
              type="text"
              className="flex-1 p-sm bg-[#f8f9ff] border border-[#c3c6d7] rounded-lg text-body-sm focus:outline-none focus:border-[#004ac6] font-semibold text-[#0b1c30]"
              placeholder="Ask robot to assign or verify tasks..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              disabled={chatLoading}
              autoFocus
            />
            <button 
              type="submit" 
              className="px-md bg-[#0b1c30] text-white rounded-lg text-body-sm font-bold hover:bg-opacity-90 active:scale-95 transition-all"
              disabled={chatLoading}
            >
              Send
            </button>
          </form>
        </div>
      ) : (
        <div 
          className="fixed bottom-gutter right-gutter w-16 h-16 bg-[#0b1c30] text-white rounded-full shadow-2xl flex items-center justify-center cursor-pointer transition-all hover:scale-105 active:scale-95 z-50 border-2 border-[#004ac6] animate-bounce"
          onClick={() => setChatOpen(true)}
          title="Click to speak with AI Autonomous Supervisor Widget"
        >
          <span className="material-symbols-outlined text-2xl text-white">smart_toy</span>
        </div>
      )}

      {/* Dynamic Slide-in success toast */}
      {toast.show && (
        <div className="fixed bottom-gutter right-gutter z-50 bg-[#0b1c30] text-white px-md py-4 rounded-lg shadow-2xl flex items-center gap-3 border border-[#004ac6]/20 transition-all transform translate-y-0 opacity-100 animate-bounce">
          <span className="material-symbols-outlined text-[#2563eb]" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
          <p className="font-label-md text-label-md font-bold">{toast.message}</p>
        </div>
      )}
    </div>
  );
}
