import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  MessageSquare,
  BarChart3,
  AlertTriangle,
  PlusCircle,
} from 'lucide-react';
import clsx from 'clsx';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/complaints', icon: MessageSquare, label: 'Complaints' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/escalations', icon: AlertTriangle, label: 'Escalations' },
  { to: '/submit', icon: PlusCircle, label: 'Submit' },
];

export default function Layout({ children }) {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 text-white flex flex-col">
        <div className="p-6 border-b border-gray-700">
          <h1 className="text-xl font-bold tracking-tight">
            <span className="text-blue-400">Complaint</span>IQ
          </h1>
          <p className="text-xs text-gray-400 mt-1">AI-Powered Dashboard</p>
        </div>
        <nav className="flex-1 py-4">
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
        </nav>
        <div className="p-4 border-t border-gray-700 text-xs text-gray-500">
          ComplaintIQ v1.0
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto bg-gray-50">
        <div className="p-6">{children}</div>
      </main>
    </div>
  );
}
