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
  { to: '/simulator', icon: Zap, label: 'Simulator Demo' },
];

const channels = ['email', 'twitter', 'chat', 'phone'];

export default function Layout({ children }) {
  const { dark, toggle } = useTheme();
  const addToast = useToast();
  const [simulating, setSimulating] = useState(false);

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
        addToast('CSV exported', 'success');
      } else {
        window.open('/api/reports/export?format=pdf', '_blank');
        addToast('Report opened in new tab', 'success');
      }
    } catch {
      addToast('Export failed', 'error');
    }
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 dark:bg-gray-950 text-white flex flex-col flex-shrink-0">
        <div className="p-6 border-b border-gray-700">
          <h1 className="text-xl font-bold tracking-tight">
            <span className="text-blue-400">Complaint</span>IQ
          </h1>
          <p className="text-xs text-gray-400 mt-1">AI-Powered Dashboard</p>
        </div>
        <nav className="flex-1 py-4 overflow-y-auto">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-6 py-3 text-sm transition-colors',
                  isActive
                    ? 'bg-blue-600/20 text-blue-400 border-r-2 border-blue-400'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                )
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}

          {/* Simulator Section */}
          <div className="mt-6 px-4">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-2 px-2">Simulator</p>
            <div className="grid grid-cols-2 gap-1">
              {channels.map((ch) => (
                <button
                  key={ch}
                  disabled={simulating}
                  onClick={() => handleSimulate(ch)}
                  className="px-2 py-1.5 text-[10px] bg-gray-800 hover:bg-gray-700 rounded text-gray-300 disabled:opacity-40 capitalize transition"
                >
                  {ch}
                </button>
              ))}
            </div>
            <button
              disabled={simulating}
              onClick={handleBurst}
              className="w-full mt-1 px-2 py-1.5 text-[10px] bg-purple-700 hover:bg-purple-600 rounded text-white disabled:opacity-40 flex items-center justify-center gap-1 transition"
            >
              <Zap size={10} /> Burst (5)
            </button>
          </div>

          {/* Export Section */}
          <div className="mt-4 px-4">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-2 px-2">Export</p>
            <div className="flex gap-1">
              <button onClick={() => handleExport('csv')} className="flex-1 px-2 py-1.5 text-[10px] bg-gray-800 hover:bg-gray-700 rounded text-gray-300 flex items-center justify-center gap-1 transition">
                <Download size={10} /> CSV
              </button>
              <button onClick={() => handleExport('pdf')} className="flex-1 px-2 py-1.5 text-[10px] bg-gray-800 hover:bg-gray-700 rounded text-gray-300 flex items-center justify-center gap-1 transition">
                <FileText size={10} /> Report
              </button>
            </div>
          </div>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-700 flex items-center justify-between">
          <span className="text-xs text-gray-500">ComplaintIQ v1.0</span>
          <button
            onClick={toggle}
            className="p-1.5 rounded-lg hover:bg-gray-700 text-gray-400 hover:text-white transition"
            title={dark ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {dark ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900">
        <div className="p-6">{children}</div>
      </main>
    </div>
  );
}
