import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import client from '../api/client';

const DEMO_CREDENTIALS = [
  { label: 'Manager', email: 'manager@aegis.com', password: 'AegisAdmin2024!', role: 'manager' },
  { label: 'Employee', email: 'james.smith@aegis.com', password: 'EmployeePass2024!', role: 'employee' },
];

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const { data } = await client.post('/api/auth/login', { email, password });
      login(data.access_token, data.user);
      navigate(data.user.role === 'manager' ? '/manager' : '/employee');
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  async function handleQuickLogin(email, password) {
    setEmail(email);
    setPassword(password);
    setError('');
    setLoading(true);

    try {
      const { data } = await client.post('/api/auth/login', { email, password });
      login(data.access_token, data.user);
      navigate(data.user.role === 'manager' ? '/manager' : '/employee');
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Login failed.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f8f9ff] text-[#0b1c30] relative overflow-hidden font-body-md">
      {/* Background gradient orbs */}
      <div className="absolute inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-[-15%] right-[-8%] w-[50%] h-[60%] bg-gradient-to-br from-[#004ac6]/8 via-[#2563eb]/5 to-transparent blur-[140px] rounded-full"></div>
        <div className="absolute bottom-[-12%] left-[-8%] w-[40%] h-[50%] bg-gradient-to-tr from-[#d3e4fe]/50 via-[#e5eeff]/30 to-transparent blur-[120px] rounded-full"></div>
        <div className="absolute top-[30%] left-[20%] w-[20%] h-[20%] bg-[#004ac6]/3 blur-[100px] rounded-full"></div>
      </div>

      <div className="w-full max-w-[440px] animate-slide-up px-gutter">
        {/* Branding */}
        <div className="text-center mb-lg">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-[#004ac6] to-[#2563eb] shadow-primary mb-md">
            <span className="material-symbols-outlined text-white text-3xl font-bold" style={{ fontVariationSettings: "'FILL' 1" }}>bolt</span>
          </div>
          <h1 className="font-display-lg text-display-lg text-[#0b1c30] tracking-tight font-black">Aegis</h1>
          <p className="font-body-md text-body-md text-[#565e74] mt-1 font-semibold tracking-wide">
            AI-Powered Task &amp; Accountability Platform
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-white/80 backdrop-blur-xl border border-white/40 rounded-2xl p-lg shadow-xl shadow-black/5 relative">
          {/* Card glow */}
          <div className="absolute -top-px left-1/2 -translate-x-1/2 w-3/4 h-px bg-gradient-to-r from-transparent via-[#004ac6]/30 to-transparent"></div>

          <h2 className="font-headline-sm text-headline-sm text-[#0b1c30] text-center mb-md font-bold">
            Sign in to your workspace
          </h2>

          <form onSubmit={handleSubmit} className="space-y-md">
            <div className="flex flex-col gap-xs">
              <label className="font-label-md text-label-md text-[#434655] font-semibold" htmlFor="email">
                Corporate Email
              </label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[#c3c6d7] text-[20px] pointer-events-none">mail</span>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  className="w-full pl-10 pr-4 py-3 bg-white border border-[#e2e8f0] rounded-xl text-body-sm focus:outline-none focus:border-[#004ac6] focus:ring-4 focus:ring-[#004ac6]/8 transition-all text-[#0b1c30] placeholder:text-[#c3c6d7]"
                  required
                  autoFocus
                  autoComplete="email"
                />
              </div>
            </div>

            <div className="flex flex-col gap-xs">
              <label className="font-label-md text-label-md text-[#434655] font-semibold" htmlFor="password">
                Password
              </label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[#c3c6d7] text-[20px] pointer-events-none">lock</span>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full pl-10 pr-4 py-3 bg-white border border-[#e2e8f0] rounded-xl text-body-sm focus:outline-none focus:border-[#004ac6] focus:ring-4 focus:ring-[#004ac6]/8 transition-all text-[#0b1c30] placeholder:text-[#c3c6d7]"
                  required
                  autoComplete="current-password"
                />
              </div>
            </div>

            {error && (
              <div className="px-sm py-3 bg-[#ffdad6]/80 backdrop-blur-sm border border-[#ba1a1a]/15 text-[#ba1a1a] rounded-xl text-body-sm font-semibold flex items-center gap-xs animate-fade-in">
                <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>report</span>
                {error}
              </div>
            )}

            <button
              type="submit"
              className="btn-press w-full py-3 bg-gradient-to-r from-[#004ac6] to-[#2563eb] text-white font-label-md text-label-md font-bold rounded-xl shadow-primary hover:shadow-lg hover:from-[#003ea8] hover:to-[#1d4ed8] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-xs"
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="material-symbols-outlined animate-spin text-[18px]">sync</span>
                  Verifying credentials...
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[18px]">login</span>
                  Sign In
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="divider-label my-md">
            <span className="text-body-sm text-[#c3c6d7] font-semibold px-xs">or continue with demo</span>
          </div>

          {/* Demo Quick Login */}
          <div className="flex gap-sm">
            {DEMO_CREDENTIALS.map((demo) => (
              <button
                key={demo.role}
                onClick={() => handleQuickLogin(demo.email, demo.password)}
                disabled={loading}
                className="btn-press flex-1 py-3 bg-[#f8f9ff] border border-[#e2e8f0] hover:border-[#004ac6]/30 hover:bg-[#eff4ff] rounded-xl text-center transition-all group"
              >
                <span className="font-label-md text-label-md font-bold text-[#0b1c30] group-hover:text-[#004ac6] transition-colors">
                  {demo.label}
                </span>
                <p className="text-[10px] text-[#c3c6d7] mt-0.5 font-semibold tracking-wide">
                  Quick access
                </p>
              </button>
            ))}
          </div>
        </div>

        {/* Footer */}
        <p className="text-center mt-md text-body-sm text-[#c3c6d7] font-semibold">
          Secure enterprise authentication &bull; AES-256 encrypted
        </p>
      </div>
    </div>
  );
}
