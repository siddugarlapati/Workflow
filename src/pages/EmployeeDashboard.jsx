import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import client from '../api/client';

export default function EmployeeDashboard() {
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  const [tasks, setTasks] = useState([]);
  const [activeTask, setActiveTask] = useState(null);
  
  // Submit Log form states
  const [logText, setLogText] = useState('');
  const [logStatus, setLogStatus] = useState('In Progress');
  const [file, setFile] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  
  // Toast notifications
  const [toast, setToast] = useState({ show: false, message: '' });

  // Fetch tasks on load
  useEffect(() => {
    fetchTasks();
  }, []);

  async function fetchTasks() {
    try {
      const { data } = await client.get('/api/tasks/mine');
      const sorted = (data.tasks || []).sort(
        (a, b) => new Date(a.deadline) - new Date(b.deadline)
      );
      setTasks(sorted);
      
      // Auto-select first active or pending task if none selected
      if (sorted.length > 0) {
        const firstActive = sorted.find(t => t.status !== 'completed') || sorted[0];
        setActiveTask(firstActive);
      }
    } catch (err) {
      console.error("Failed to fetch assigned tasks", err);
    }
  }

  function handleLogout() {
    logout();
    navigate('/login');
  }

  function isOverdue(task) {
    return (
      task.status !== 'completed' &&
      new Date(task.deadline) < new Date()
    );
  }

  async function handleLogSubmit(e) {
    e.preventDefault();
    if (!activeTask) return;
    setSubmitting(true);

    try {
      let responseData;
      
      // 1. Submit progress log and check anti-bluff verification
      if (file) {
        const formData = new FormData();
        formData.append('log_text', logText);
        formData.append('file', file);
        const { data } = await client.post(`/api/logs/${activeTask.id}`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        responseData = data;
      } else {
        const { data } = await client.post(`/api/logs/${activeTask.id}`, { log_text: logText });
        responseData = data;
      }

      // 2. Update task status if changed
      const apiStatus = logStatus === 'Completed' ? 'completed' : 'in_progress';
      if (activeTask.status !== apiStatus) {
        await client.patch(`/api/tasks/${activeTask.id}/status`, { status: apiStatus });
      }

      // 3. Trigger toast notification
      showToast(`Log submitted! AI Confidence: ${responseData.ai_confidence}`);

      // 4. Reset form & refresh tasks
      setLogText('');
      setFile(null);
      await fetchTasks();
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.detail || 'Failed to submit work log.');
    } finally {
      setSubmitting(false);
    }
  }

  function showToast(msg) {
    setToast({ show: true, message: msg });
    setTimeout(() => {
      setToast({ show: false, message: '' });
    }, 4000);
  }

  return (
    <div className="bg-[#f8f9ff] text-[#0b1c30] font-body-md min-h-screen flex relative overflow-hidden">
      {/* Background Atmospheric Effect */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] right-[-5%] w-[40%] h-[50%] bg-[#004ac6]/5 blur-[120px] rounded-full"></div>
        <div className="absolute bottom-[-5%] left-[-5%] w-[30%] h-[40%] bg-[#e5eeff]/40 blur-[100px] rounded-full"></div>
      </div>

      {/* SideNavBar */}
      <aside className="hidden md:flex flex-col h-screen w-64 border-r border-[#e2e8f0] bg-white/90 backdrop-blur-xl sticky top-0 py-md px-sm shrink-0 justify-between animate-slide-right">
        <div>
          <div className="mb-lg px-sm">
            <div className="flex items-center gap-sm mb-1">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#004ac6] to-[#2563eb] flex items-center justify-center shadow-primary">
                <span className="material-symbols-outlined text-white text-lg" style={{ fontVariationSettings: "'FILL' 1" }}>bolt</span>
              </div>
              <h1 className="font-headline-md text-headline-md font-bold text-[#0b1c30] tracking-tight">Aegis</h1>
            </div>
            <p className="font-body-sm text-body-sm text-[#565e74] uppercase tracking-wider text-[11px] font-bold ml-[44px]">Employee Hub</p>
          </div>
          <nav className="space-y-0.5 px-sm">
            <a className="flex items-center gap-sm px-sm py-2.5 rounded-xl transition-all text-[#004ac6] bg-[#e5eeff] font-bold shadow-sm" href="#">
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>assignment</span>
              <span className="font-label-md text-label-md">My Objectives</span>
            </a>
          </nav>
        </div>
        
        {/* User profile with logout inside drawer */}
        <div className="border-t border-[#e2e8f0] pt-md px-sm flex flex-col gap-sm">
          <div className="flex items-center gap-sm px-sm py-sm">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#dae2fd] to-[#e5eeff] flex items-center justify-center font-bold text-[#004ac6] shadow-sm">
              {user?.name?.charAt(0) || 'E'}
            </div>
            <div className="overflow-hidden">
              <p className="font-label-md text-label-md truncate font-bold text-[#0b1c30]">{user?.name || 'Employee'}</p>
              <p className="font-label-sm text-label-sm text-[#565e74] truncate">{user?.email || 'employee@demo.com'}</p>
            </div>
          </div>
          <button 
            onClick={handleLogout}
            className="btn-press w-full bg-[#0b1c30] hover:bg-[#1a2a3e] text-white py-2.5 rounded-xl font-label-md text-label-md font-bold flex items-center justify-center gap-xs transition-all"
          >
            <span className="material-symbols-outlined text-[18px]">logout</span>
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content Canvas */}
      <main className="flex-1 flex flex-col min-h-screen overflow-x-hidden">
        {/* TopNavBar */}
        <header className="flex justify-between items-center w-full px-gutter py-base h-16 sticky top-0 z-40 bg-white/90 backdrop-blur-xl border-b border-[#e2e8f0]">
          <div className="flex items-center gap-md">
            <h2 className="font-headline-sm text-headline-sm text-[#0b1c30] font-black tracking-tight md:hidden">Aegis</h2>
            <div className="relative w-64 hidden sm:block">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[#c3c6d7] text-[20px] pointer-events-none">search</span>
              <input 
                className="w-full pl-10 pr-4 py-2.5 bg-[#f8f9ff] border border-[#e2e8f0] rounded-xl text-body-sm focus:outline-none focus:ring-4 focus:ring-[#004ac6]/8 focus:border-[#004ac6] transition-all placeholder:text-[#c3c6d7]" 
                placeholder="Search objectives..." 
                type="text"
              />
            </div>
          </div>
          <div className="flex items-center gap-sm">
            <span className="font-label-sm text-label-sm px-sm py-1.5 bg-[#e5eeff] text-[#004ac6] font-bold rounded-lg uppercase tracking-wider">
              {user?.department || 'Engineering'}
            </span>
          </div>
        </header>

        {/* Bento Grid Content */}
        <div className="p-gutter grid grid-cols-12 gap-gutter max-w-7xl mx-auto w-full">
          {/* Section Title */}
          <div className="col-span-12 mb-xs">
            <h2 className="font-headline-lg text-headline-lg text-[#0b1c30] font-bold tracking-tight">Assigned Objectives</h2>
            <p className="font-body-md text-body-md text-[#565e74]">Select a task to report progress, upload proof documents, and run AI verification.</p>
          </div>

          {/* Left Side: Tasks List */}
          <div className="col-span-12 lg:col-span-5 space-y-md">
            {tasks.length === 0 ? (
              <div className="bg-white/80 backdrop-blur-xl border border-[#e2e8f0] rounded-2xl text-center py-xl px-md">
                <span className="material-symbols-outlined text-5xl text-[#c3c6d7] mb-sm block">task_alt</span>
                <p className="text-[#565e74] italic">No active objectives assigned. Nice job!</p>
              </div>
            ) : (
              tasks.map((task) => {
                const overdue = isOverdue(task);
                const isActive = activeTask?.id === task.id;
                
                return (
                  <div 
                    key={task.id}
                    onClick={() => setActiveTask(task)}
                    className={`p-md rounded-2xl shadow-sm relative overflow-hidden transition-all cursor-pointer bg-white/80 backdrop-blur-sm border-2 hover:shadow-md ${
                      isActive ? 'border-[#004ac6] shadow-primary scale-[1.01]' : 'border-[#e2e8f0] hover:border-[#004ac6]/30'
                    }`}
                  >
                    <div className="absolute top-3 right-3 flex items-center gap-xs">
                      {task.status === 'completed' ? (
                        <span className="bg-[#e5eeff] text-[#004ac6] font-label-sm text-label-sm px-2 py-0.5 rounded-lg font-bold">Verified</span>
                      ) : overdue ? (
                        <span className="bg-[#ffdad6] text-[#ba1a1a] font-label-sm text-label-sm px-2 py-0.5 rounded-lg font-bold animate-pulse">Overdue</span>
                      ) : (
                        <span className="bg-[#eff4ff] text-[#565e74] font-label-sm text-label-sm px-2 py-0.5 rounded-lg font-semibold uppercase">{task.status === 'in_progress' ? 'In Progress' : task.status}</span>
                      )}
                    </div>
                    
                    <div className="flex flex-col gap-1 pr-14">
                      <span className="font-label-sm text-label-sm text-[#004ac6] uppercase tracking-widest font-bold">
                        {task.priority} priority
                      </span>
                      <h3 className="font-headline-sm text-headline-sm text-[#0b1c30] font-bold line-clamp-1">{task.title}</h3>
                      <p className="font-body-sm text-body-sm text-[#565e74] line-clamp-2 mt-1">
                        {task.description ? task.description.split('\n\n')[0] : 'No additional guidelines provided.'}
                      </p>
                      
                      <div className="mt-md flex items-center justify-between border-t border-[#e2e8f0] pt-sm text-[12px] text-[#565e74]">
                        <span className="flex items-center gap-1.5 font-semibold">
                          <span className="material-symbols-outlined text-[16px]">calendar_today</span>
                          Due {new Date(task.deadline).toLocaleDateString()}
                        </span>
                        <span>{task.work_logs?.length || 0} submissions</span>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Right Side: Active Task Submit Log & Verified Logs */}
          <div className="col-span-12 lg:col-span-7 space-y-gutter">
            {activeTask ? (
              <>
                {/* Submit Daily Work Log Card */}
                <section className="bg-white border border-[#c3c6d7] rounded-xl p-md flex flex-col h-fit shadow-sm">
                  <div className="flex items-center justify-between mb-md pb-xs border-b border-[#e2e8f0]">
                    <div className="flex items-center gap-sm">
                      <div className="w-10 h-10 rounded-lg bg-[#e5eeff] flex items-center justify-center text-[#004ac6]">
                        <span className="material-symbols-outlined text-2xl font-bold">edit_note</span>
                      </div>
                      <div>
                        <h3 className="font-headline-sm text-headline-sm text-[#0b1c30] font-bold">Report Progress & Proof</h3>
                        <p className="font-label-sm text-label-sm text-[#434655]">Objective: {activeTask.title}</p>
                      </div>
                    </div>
                  </div>

                  {/* Expected Criteria Scope Box */}
                  {activeTask.description && activeTask.description.includes('[Expected Verification Criteria]:') && (
                    <div className="mb-md p-sm bg-[#eff4ff] border border-[#004ac6]/10 rounded-lg flex items-start gap-xs text-body-sm text-[#004ac6]">
                      <span className="material-symbols-outlined text-[20px] shrink-0">verified_user</span>
                      <div>
                        <strong>Required Verification Scope:</strong>
                        <p className="mt-xs italic">{activeTask.description.split('[Expected Verification Criteria]:')[1].trim()}</p>
                      </div>
                    </div>
                  )}

                  <form onSubmit={handleLogSubmit} className="space-y-md">
                    <div className="relative">
                      <textarea 
                        value={logText}
                        onChange={(e) => setLogText(e.target.value)}
                        className="w-full p-sm bg-white border border-[#c3c6d7] rounded-lg text-body-md focus:outline-none focus:border-[#004ac6] focus:ring-4 focus:ring-[#004ac6]/5 transition-all resize-none min-h-[140px]" 
                        placeholder="Detail your completed milestones, URLs built, formulas applied, or specific updates..." 
                        required
                      />
                    </div>

                    <div className="flex flex-col gap-xs">
                      <label className="font-label-md text-label-md text-[#0b1c30] flex items-center gap-xs" htmlFor="file-upload">
                        <span className="material-symbols-outlined text-[20px]">upload_file</span>
                        Upload Proof Document or Screenshot (.xlsx, .pdf, .docx, .txt, .csv, .png, .jpg, .jpeg)
                      </label>
                      <input 
                        id="file-upload" 
                        type="file" 
                        accept=".pdf,.docx,.xlsx,.txt,.csv,.png,.jpg,.jpeg"
                        onChange={(e) => setFile(e.target.files[0])}
                        className="w-full text-body-sm file:mr-md file:py-2 file:px-md file:rounded-lg file:border-0 file:text-body-sm file:font-semibold file:bg-[#0b1c30] file:text-white hover:file:opacity-90 file:cursor-pointer"
                      />
                    </div>

                    <div className="mt-md flex flex-wrap items-center justify-between gap-sm pt-sm border-t border-[#e2e8f0]">
                      <div className="flex gap-sm items-center">
                        <span className="text-body-sm text-[#434655]">Sprint Status:</span>
                        <select 
                          value={logStatus} 
                          onChange={(e) => setLogStatus(e.target.value)}
                          className="bg-white border border-[#c3c6d7] rounded-lg text-body-sm py-1.5 px-sm focus:outline-none focus:border-[#004ac6]"
                        >
                          <option value="In Progress">In Progress</option>
                          <option value="Completed">Completed</option>
                        </select>
                      </div>
                      
                      <button 
                        type="submit" 
                        className="bg-[#004ac6] hover:bg-[#003ea8] text-white font-label-md text-label-md font-bold px-lg py-3 rounded-lg flex items-center gap-xs transition-all active:scale-[0.98] disabled:opacity-60"
                        disabled={submitting}
                      >
                        {submitting ? (
                          <>
                            <span className="material-symbols-outlined animate-spin text-sm">sync</span>
                            Running Playwright E2E Audit...
                          </>
                        ) : (
                          <>
                            <span className="material-symbols-outlined text-sm">auto_awesome</span>
                            Submit & Verify with AI
                          </>
                        )}
                      </button>
                    </div>
                  </form>
                </section>

                {/* Submissions Logs list */}
                {activeTask.work_logs && activeTask.work_logs.length > 0 && (
                  <section className="space-y-sm">
                    <h3 className="font-headline-sm text-headline-sm text-[#0b1c30] font-bold px-xs">Verification History</h3>
                    <div className="space-y-sm">
                      {activeTask.work_logs.map((log) => (
                        <div key={log.id} className="bg-white border border-[#e2e8f0] rounded-xl p-md flex flex-col gap-sm shadow-xs">
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-label-md text-label-md font-bold text-[#0b1c30]">
                                Logged {new Date(log.submitted_at).toLocaleString()}
                              </p>
                              {log.file_name && (
                                <p className="text-[12px] text-[#004ac6] font-semibold flex items-center gap-xs mt-xs">
                                  <span className="material-symbols-outlined text-[16px]">draft</span>
                                  {log.file_name} successfully parsed
                                </p>
                              )}
                            </div>
                            <span className={`px-sm py-0.5 rounded-full text-[12px] font-bold uppercase ${
                              log.ai_confidence === 'High' ? 'bg-[#e5eeff] text-[#004ac6]' :
                              log.ai_confidence === 'Medium' ? 'bg-[#eff4ff] text-[#434655]' : 'bg-[#ffdad6] text-[#ba1a1a] animate-pulse'
                            }`}>
                              {log.ai_confidence === 'Low' ? '🚨 BLUFF FLAGGED' : `${log.ai_confidence} Confidence`}
                            </span>
                          </div>
                          
                          <p className="font-body-sm text-body-sm text-[#434655] italic leading-relaxed whitespace-pre-wrap">
                            "{log.log_text}"
                          </p>
                          
                          {log.ai_feedback && (
                            <div className="mt-xs p-sm bg-[#f8f9ff] border border-[#e2e8f0] rounded-lg text-body-sm text-[#434655] flex items-start gap-xs">
                              <span className="material-symbols-outlined text-primary text-[20px]">psychology</span>
                              <div>
                                <strong>AI Agent Reasoning:</strong>
                                <p className="mt-xs">{log.ai_feedback}</p>
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </section>
                )}
              </>
            ) : (
              <div className="bento-card text-center py-xl bg-white border-[#c3c6d7] flex flex-col items-center justify-center">
                <span className="material-symbols-outlined text-6xl text-[#c3c6d7] mb-sm">select_all</span>
                <p className="text-[#434655] italic">Select a task objective from the left panel to begin logging and auditing proof.</p>
              </div>
            )}
          </div>
        </div>
      </main>

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
