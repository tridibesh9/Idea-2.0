import React, { useState } from 'react';
import { loginAgent } from '../api';
import { useToast } from '../components/Toast';
import { Mail, ShieldCheck } from 'lucide-react';

export default function Login({ onLoginSuccess }) {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const addToast = useToast();

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!email) return;
    setLoading(true);
    try {
      const res = await loginAgent(email);
      const { token, name, email: agentEmail, role, department, id } = res.data;
      localStorage.setItem('agent_token', token);
      localStorage.setItem('agent_name', name);
      localStorage.setItem('agent_email', agentEmail);
      localStorage.setItem('agent_role', role);
      localStorage.setItem('agent_dept', department);
      localStorage.setItem('agent_id', id);
      addToast(`Welcome back, ${name}!`, 'success');
      onLoginSuccess();
    } catch (err) {
      const errMsg = err.response?.data?.detail || 'Invalid agent email. Please check your credentials.';
      addToast(errMsg, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-dark-950 px-4 transition-colors duration-300">
      <div className="w-full max-w-md bg-white/60 dark:bg-dark-900/60 backdrop-blur-xl border border-gray-200/50 dark:border-white/5 shadow-2xl rounded-3xl p-8 space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-extrabold tracking-tight font-heading">
            <span className="bg-gradient-to-r from-indigo-500 to-purple-500 bg-clip-text text-transparent">Complaint</span>
            <span className="text-slate-800 dark:text-white">IQ</span>
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-2 font-medium">Agent Portal Access</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Agent Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input
                type="email"
                placeholder="e.g. sarah@complaintiq.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-10 pr-4 py-3 rounded-2xl bg-slate-100 dark:bg-dark-800 border-none text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-500 text-sm focus:outline-none transition-all"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 text-white font-semibold rounded-2xl shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/30 transition-all flex items-center justify-center gap-2 transform hover:-translate-y-0.5 disabled:opacity-50"
          >
            {loading ? (
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
            ) : (
              <>
                <ShieldCheck size={18} />
                <span>Verify & Login</span>
              </>
            )}
          </button>
        </form>

        <div className="pt-4 border-t border-slate-200 dark:border-slate-800 text-center">
          <p className="text-[11px] text-slate-400">Available Demo Accounts:</p>
          <div className="mt-2 grid grid-cols-2 gap-1.5 text-[10px] text-slate-500 dark:text-slate-400 font-mono">
            <div className="p-1.5 bg-slate-100 dark:bg-dark-800/50 rounded-lg cursor-pointer hover:bg-slate-250 dark:hover:bg-dark-800 hover:text-indigo-500" onClick={() => setEmail('sarah@complaintiq.com')}>sarah@complaintiq.com</div>
            <div className="p-1.5 bg-slate-100 dark:bg-dark-800/50 rounded-lg cursor-pointer hover:bg-slate-250 dark:hover:bg-dark-800 hover:text-indigo-500" onClick={() => setEmail('priya@complaintiq.com')}>priya@complaintiq.com</div>
            <div className="p-1.5 bg-slate-100 dark:bg-dark-800/50 rounded-lg cursor-pointer hover:bg-slate-250 dark:hover:bg-dark-800 hover:text-indigo-500" onClick={() => setEmail('james@complaintiq.com')}>james@complaintiq.com</div>
            <div className="p-1.5 bg-slate-100 dark:bg-dark-800/50 rounded-lg cursor-pointer hover:bg-slate-250 dark:hover:bg-dark-800 hover:text-indigo-500" onClick={() => setEmail('rahul@complaintiq.com')}>rahul@complaintiq.com</div>
          </div>
        </div>
      </div>
    </div>
  );
}
