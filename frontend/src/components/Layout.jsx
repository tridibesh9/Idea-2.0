import { NavLink } from 'react-router-dom';
import { useState } from 'react';
import {
  LayoutDashboard,
  MessageSquare,
  BarChart3,
  AlertTriangle,
  PlusCircle,
  Sun,
  Moon,
  Zap,
  Download,
  FileText,
  Sparkles,
} from 'lucide-react';
import clsx from 'clsx';
import { useTheme } from '../context/ThemeContext';
import { useToast } from './Toast';
import { simulateChannel, simulateBurst, exportComplaints } from '../api';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/complaints', icon: MessageSquare, label: 'Complaints' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/escalations', icon: AlertTriangle, label: 'Escalations' },
  { to: '/submit', icon: PlusCircle, label: 'Submit' },
  { to: '/simulator', icon: Sparkles, label: 'Simulator Demo' },
];

const channels = ['email', 'twitter', 'chat', 'phone'];

export default function Layout({ children, onLogout }) {
  const { dark, toggle } = useTheme();
  const addToast = useToast();
  const [simulating, setSimulating] = useState(false);

  const agentName = localStorage.getItem('agent_name');
  const agentRole = localStorage.getItem('agent_role');
  const agentDept = localStorage.getItem('agent_dept');

  async function handleSimulate(channel) {
    setSimulating(true);
    try {
      await simulateChannel(channel);
      addToast(`Simulated ${channel} complaint created`, 'success');
    } catch {
      addToast('Simulation failed — is the backend running?', 'error');
    } finally {
      setSimulating(false);
    }
  }

  async function handleBurst() {
    setSimulating(true);
    try {
      const res = await simulateBurst(5);
      addToast(`Burst: ${res.data.simulated} complaints created`, 'success');
    } catch {
      addToast('Burst simulation failed', 'error');
    } finally {
      setSimulating(false);
    }
  }

  async function handleExport(format) {
    try {
      if (format === 'csv') {
        const res = await exportComplaints({ format: 'csv' });
        const blob = new Blob([res.data], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `complaints_export.csv`;
        a.click();
        URL.revokeObjectURL(url);
        addToast('CSV exported successfully', 'success');
      } else {
        window.open('/api/reports/export?format=pdf', '_blank');
        addToast('Report opened in new tab', 'success');
      }
    } catch {
      addToast('Export failed', 'error');
    }
  }

  return (
    <div className="flex h-screen overflow-hidden bg-transparent">
      {/* Sidebar - Glassmorphic */}
      <aside className="w-64 bg-white/60 dark:bg-dark-900/60 backdrop-blur-xl border-r border-gray-200/50 dark:border-white/5 flex flex-col flex-shrink-0 z-20 transition-all duration-300">
        <div className="p-6">
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2 font-heading">
            <span className="bg-gradient-to-r from-indigo-500 to-purple-500 bg-clip-text text-transparent">Complaint</span>
            <span className="text-slate-800 dark:text-white">IQ</span>
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-medium">Gen-AI Dashboard</p>
        </div>
        
        <nav className="flex-1 py-4 px-3 overflow-y-auto custom-scrollbar">
          <div className="space-y-1">
            {navItems.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group',
                    isActive
                      ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 shadow-sm'
                      : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-dark-800 hover:text-slate-900 dark:hover:text-slate-200'
                  )
                }
              >
                <Icon size={18} className="group-hover:scale-110 transition-transform duration-200" />
                {label}
              </NavLink>
            ))}
          </div>

          <div className="mt-8">
            <div className="px-4 flex items-center gap-2 mb-3">
              <div className="h-px bg-slate-200 dark:bg-slate-700/50 flex-1"></div>
              <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 dark:text-slate-500">Simulator</span>
              <div className="h-px bg-slate-200 dark:bg-slate-700/50 flex-1"></div>
            </div>
            
            <div className="grid grid-cols-2 gap-2 px-2">
              {channels.map((ch) => (
                <button
                  key={ch}
                  disabled={simulating}
                  onClick={() => handleSimulate(ch)}
                  className="px-2 py-2 text-xs font-medium bg-white dark:bg-dark-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:border-primary-400 dark:hover:border-primary-500 hover:text-primary-600 dark:hover:text-primary-400 disabled:opacity-50 capitalize shadow-sm transition-all"
                >
                  {ch}
                </button>
              ))}
            </div>
            <div className="px-2 mt-2">
              <button
                disabled={simulating}
                onClick={handleBurst}
                className="w-full px-2 py-2 text-xs font-semibold bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 rounded-lg text-white shadow-md shadow-indigo-500/20 disabled:opacity-50 flex items-center justify-center gap-2 transition-all transform hover:-translate-y-0.5"
              >
                <Zap size={14} className={simulating ? 'animate-pulse' : ''} /> Burst (5)
              </button>
            </div>
          </div>

          <div className="mt-6">
            <div className="px-4 flex items-center gap-2 mb-3">
              <div className="h-px bg-slate-200 dark:bg-slate-700/50 flex-1"></div>
              <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 dark:text-slate-500">Export</span>
              <div className="h-px bg-slate-200 dark:bg-slate-700/50 flex-1"></div>
            </div>
            <div className="flex gap-2 px-2">
              <button onClick={() => handleExport('csv')} className="flex-1 px-2 py-2 text-xs font-medium bg-slate-100 dark:bg-dark-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg flex items-center justify-center gap-1.5 transition-colors">
                <Download size={14} /> CSV
              </button>
              <button onClick={() => handleExport('pdf')} className="flex-1 px-2 py-2 text-xs font-medium bg-slate-100 dark:bg-dark-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg flex items-center justify-center gap-1.5 transition-colors">
                <FileText size={14} /> Report
              </button>
            </div>
          </div>
        </nav>

        {/* Agent Profile Card */}
        <div className="p-4 border-t border-slate-200/50 dark:border-white/5 bg-slate-50/50 dark:bg-dark-900/30">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm">
              {agentName ? agentName.charAt(0) : 'A'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-slate-800 dark:text-white truncate">{agentName || 'Agent'}</p>
              <p className="text-[10px] text-slate-400 truncate capitalize">{agentRole ? `${agentRole.replace('_', ' ')} • ${agentDept}` : 'Role'}</p>
            </div>
          </div>
          <button
            onClick={onLogout}
            className="w-full mt-3 py-1.5 px-3 rounded-lg text-xs font-medium text-red-600 hover:text-white bg-red-50 hover:bg-red-600 dark:bg-red-950/20 dark:hover:bg-red-900/30 transition-all flex items-center justify-center gap-1.5"
          >
            <span>Log out</span>
          </button>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200/50 dark:border-white/5 flex items-center justify-between">
          <span className="text-xs font-medium text-slate-400">v1.0 &copy; 2024</span>
          <button
            onClick={toggle}
            className="p-2 rounded-xl bg-slate-100 dark:bg-dark-800 hover:bg-slate-200 dark:hover:bg-dark-700 text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white transition-all transform hover:rotate-12"
            title={dark ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {dark ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto relative z-10 custom-scrollbar">
        <div className="p-4 md:p-8 max-w-7xl mx-auto animate-fade-in">{children}</div>
      </main>
    </div>
  );
}
