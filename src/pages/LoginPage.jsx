import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import client from '../api/client';

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

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f8f9ff] text-[#0b1c30] p-gutter relative overflow-hidden font-body-md">
      {/* Background blobs */}
      <div className="absolute top-[-10%] right-[-5%] w-[45%] h-[50%] bg-[#004ac6]/5 blur-[120px] rounded-full pointer-events-none"></div>
      <div className="absolute bottom-[-10%] left-[-5%] w-[35%] h-[40%] bg-[#d3e4fe]/40 blur-[100px] rounded-full pointer-events-none"></div>

      <div className="w-full max-w-[420px] bg-white border border-[#e2e8f0] rounded-xl p-md shadow-sm relative z-10 transition-all hover:shadow-md">
        <div className="text-center mb-lg">
          <div className="flex items-center justify-center gap-sm mb-xs">
            <div className="w-10 h-10 rounded-lg bg-[#004ac6] flex items-center justify-center text-white">
              <span className="material-symbols-outlined font-bold text-2xl">bolt</span>
            </div>
            <h1 className="font-headline-lg text-headline-lg text-[#0b1c30] tracking-tight">WorkFlow</h1>
          </div>
          <p className="font-body-sm text-body-sm text-[#434655] tracking-wide uppercase">
            AI-Powered Task & Accountability
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-md">
          <div className="flex flex-col gap-xs">
            <label className="font-label-md text-label-md text-[#0b1c30]" htmlFor="email">
              Corporate Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              className="w-full p-sm bg-white border border-[#c3c6d7] rounded-lg text-body-sm focus:outline-none focus:border-[#004ac6] focus:ring-2 focus:ring-[#004ac6]/10 transition-all"
              required
              autoFocus
            />
          </div>

          <div className="flex flex-col gap-xs">
            <label className="font-label-md text-label-md text-[#0b1c30]" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full p-sm bg-white border border-[#c3c6d7] rounded-lg text-body-sm focus:outline-none focus:border-[#004ac6] focus:ring-2 focus:ring-[#004ac6]/10 transition-all"
              required
            />
          </div>

          {error && (
            <div className="p-sm bg-[#ffdad6] border border-[#ba1a1a]/20 text-[#ba1a1a] rounded-lg text-body-sm font-semibold flex items-center gap-xs">
              <span className="material-symbols-outlined text-[18px]">report</span>
              {error}
            </div>
          )}

          <button
            type="submit"
            className="w-full py-sm bg-[#004ac6] hover:bg-[#003ea8] text-white font-label-md text-label-md font-bold rounded-lg transition-all active:scale-[0.98] disabled:opacity-60 flex items-center justify-center gap-xs"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="material-symbols-outlined animate-spin text-[18px]">sync</span>
                Verifying Credentials...
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-[18px]">login</span>
                Sign In to Workspace
              </>
            )}
          </button>
        </form>

        <div className="mt-lg pt-md border-t border-[#e2e8f0] text-center">
          <p className="font-label-sm text-label-sm text-[#434655] mb-xs">
            DEMO SIGN-IN CREDENTIALS
          </p>
          <div className="bg-[#eff4ff] p-sm rounded-lg text-left text-body-sm text-[#003ea8] space-y-1">
            <div>🔑 <strong>Manager:</strong> <code>manager@demo.com</code></div>
            <div>🔑 <strong>Employee:</strong> <code>employee1@demo.com</code></div>
            <div className="border-t border-[#004ac6]/10 pt-xs mt-xs text-center text-[12px]">
              Password for both: <code className="font-bold">password123</code>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
