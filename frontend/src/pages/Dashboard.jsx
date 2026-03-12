import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertCircle,
  Clock,
  TrendingDown,
  MessageSquare,
  ShieldAlert,
} from 'lucide-react';
import { getAnalyticsSummary, getComplaints } from '../api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from 'recharts';

const SEVERITY_COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
};

const STATUS_COLORS = {
  new: '#3b82f6',
  open: '#8b5cf6',
  in_progress: '#f59e0b',
  escalated: '#ef4444',
  resolved: '#22c55e',
  closed: '#6b7280',
};

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [recentComplaints, setRecentComplaints] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [sumRes, compRes] = await Promise.all([
          getAnalyticsSummary(),
          getComplaints({ page: 1, page_size: 10 }),
        ]);
        setSummary(sumRes.data);
        setRecentComplaints(compRes.data.items);
      } catch (err) {
        console.error('Failed to load dashboard:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const kpis = [
    { label: 'Open Complaints', value: summary?.total_open ?? 0, icon: MessageSquare, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Critical', value: summary?.total_critical ?? 0, icon: AlertCircle, color: 'text-red-600', bg: 'bg-red-50' },
    { label: 'SLA Breached', value: summary?.total_sla_breached ?? 0, icon: ShieldAlert, color: 'text-orange-600', bg: 'bg-orange-50' },
    { label: 'Avg Resolution (hrs)', value: summary?.avg_resolution_hours ?? '—', icon: Clock, color: 'text-green-600', bg: 'bg-green-50' },
    { label: 'Avg Sentiment', value: summary?.avg_sentiment ?? '—', icon: TrendingDown, color: 'text-purple-600', bg: 'bg-purple-50' },
  ];

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Dashboard</h2>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
        {kpis.map((kpi) => (
          <div key={kpi.label} className="bg-white rounded-xl shadow-sm border p-4">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${kpi.bg}`}>
                <kpi.icon size={20} className={kpi.color} />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{kpi.value}</p>
                <p className="text-xs text-gray-500">{kpi.label}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Complaints */}
      <div className="bg-white rounded-xl shadow-sm border">
        <div className="p-4 border-b flex items-center justify-between">
          <h3 className="font-semibold text-gray-800">Recent Complaints</h3>
          <Link to="/complaints" className="text-sm text-blue-600 hover:underline">
            View All →
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left p-3 font-medium text-gray-600">Channel</th>
                <th className="text-left p-3 font-medium text-gray-600">Subject</th>
                <th className="text-left p-3 font-medium text-gray-600">Category</th>
                <th className="text-left p-3 font-medium text-gray-600">Severity</th>
                <th className="text-left p-3 font-medium text-gray-600">Status</th>
                <th className="text-left p-3 font-medium text-gray-600">Sentiment</th>
                <th className="text-left p-3 font-medium text-gray-600">Date</th>
              </tr>
            </thead>
            <tbody>
              {recentComplaints.map((c) => (
                <tr key={c.id} className="border-t hover:bg-gray-50 cursor-pointer" onClick={() => window.location.href = `/complaints/${c.id}`}>
                  <td className="p-3">
                    <span className="px-2 py-1 rounded-full text-xs bg-gray-100 font-medium">
                      {c.channel}
                    </span>
                  </td>
                  <td className="p-3 text-gray-800 max-w-xs truncate">{c.subject || c.body?.slice(0, 60)}</td>
                  <td className="p-3 text-gray-600">{c.category || '—'}</td>
                  <td className="p-3">
                    <span
                      className="px-2 py-1 rounded-full text-xs font-medium text-white"
                      style={{ backgroundColor: SEVERITY_COLORS[c.severity] || '#6b7280' }}
                    >
                      {c.severity}
                    </span>
                  </td>
                  <td className="p-3">
                    <span
                      className="px-2 py-1 rounded-full text-xs font-medium text-white"
                      style={{ backgroundColor: STATUS_COLORS[c.status] || '#6b7280' }}
                    >
                      {c.status}
                    </span>
                  </td>
                  <td className="p-3 text-gray-600">
                    {c.sentiment_score != null ? c.sentiment_score.toFixed(2) : '—'}
                  </td>
                  <td className="p-3 text-gray-500 text-xs">
                    {new Date(c.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
              {recentComplaints.length === 0 && (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-gray-400">
                    No complaints yet. Submit one to get started!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
