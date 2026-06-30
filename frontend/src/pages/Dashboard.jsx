import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertCircle,
  Clock,
  TrendingDown,
  MessageSquare,
  ShieldAlert,
  ChevronRight,
  Activity,
  Flame
} from 'lucide-react';
import { getAnalyticsSummary, getComplaints, getTrends } from '../api';
import { SkeletonKPIs, SkeletonTable } from '../components/Skeleton';
import LiveFeed from '../components/LiveFeed';
import clsx from 'clsx';

const SEVERITY_COLORS = {
  critical: 'bg-red-500 shadow-red-500/30',
  high: 'bg-orange-500 shadow-orange-500/30',
  medium: 'bg-amber-500 shadow-amber-500/30',
  low: 'bg-emerald-500 shadow-emerald-500/30',
};

const STATUS_COLORS = {
  new: 'bg-blue-500 shadow-blue-500/30',
  open: 'bg-indigo-500 shadow-indigo-500/30',
  in_progress: 'bg-amber-500 shadow-amber-500/30',
  escalated: 'bg-red-500 shadow-red-500/30',
  resolved: 'bg-emerald-500 shadow-emerald-500/30',
  closed: 'bg-slate-500 shadow-slate-500/30',
};

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [recentComplaints, setRecentComplaints] = useState([]);
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const [sumRes, compRes, trendsRes] = await Promise.all([
          getAnalyticsSummary(),
          getComplaints({ page: 1, page_size: 10 }),
          getTrends({ timeframe: '24h', group_by: 'category' })
        ]);
        setSummary(sumRes.data);
        setRecentComplaints(compRes.data.items);
        setTrends(trendsRes.data);
      } catch (err) {
        setError('Failed to load dashboard. Is the backend running?');
        console.error('Failed to load dashboard:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="flex items-center gap-3">
          <Activity className="text-primary-500 animate-pulse" size={28} />
          <h2 className="text-3xl font-bold font-heading bg-gradient-to-r from-slate-800 to-slate-500 dark:from-white dark:to-slate-400 bg-clip-text text-transparent">Overview Dashboard</h2>
        </div>
        <SkeletonKPIs count={5} />
        <div className="mt-8 glass-panel rounded-2xl p-6">
          <SkeletonTable rows={5} cols={7} />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center animate-fade-in glass-panel rounded-3xl p-8">
        <div className="w-20 h-20 bg-red-50 dark:bg-red-900/20 rounded-full flex items-center justify-center mb-6 shadow-inner shadow-red-500/10">
          <AlertCircle size={40} className="text-red-500" />
        </div>
        <p className="text-lg font-medium text-slate-700 dark:text-slate-300 mb-6 max-w-md">{error}</p>
        <button onClick={() => window.location.reload()} className="px-6 py-2.5 bg-gradient-to-r from-slate-800 to-slate-700 hover:from-slate-700 hover:to-slate-600 dark:from-white dark:to-slate-200 dark:hover:from-slate-200 dark:hover:to-slate-300 text-white dark:text-slate-900 rounded-xl font-semibold shadow-lg shadow-slate-500/20 transition-all transform hover:-translate-y-0.5">
          Retry Connection
        </button>
      </div>
    );
  }

  const kpis = [
    { label: 'Open Complaints', value: summary?.total_open ?? 0, icon: MessageSquare, gradient: 'from-blue-500 to-indigo-500', shadow: 'shadow-blue-500/20' },
    { label: 'Critical', value: summary?.total_critical ?? 0, icon: AlertCircle, gradient: 'from-red-500 to-rose-500', shadow: 'shadow-red-500/20' },
    { label: 'SLA Breached', value: summary?.total_sla_breached ?? 0, icon: ShieldAlert, gradient: 'from-orange-500 to-amber-500', shadow: 'shadow-orange-500/20' },
    { label: 'Avg Resolution (hrs)', value: summary?.avg_resolution_hours ?? '—', icon: Clock, gradient: 'from-emerald-400 to-teal-500', shadow: 'shadow-emerald-500/20' },
    { label: 'Avg Sentiment', value: summary?.avg_sentiment ?? '—', icon: TrendingDown, gradient: 'from-purple-500 to-fuchsia-500', shadow: 'shadow-purple-500/20' },
  ];

  const topTrend = (() => {
    if (!trends || trends.length === 0) return null;
    const counts = {};
    trends.forEach(t => {
      const cat = t.category || 'Unknown';
      counts[cat] = (counts[cat] || 0) + t.count;
    });
    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    return { category: sorted[0][0], count: sorted[0][1] };
  })();

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex items-center gap-3">
        <div className="p-2.5 bg-white dark:bg-dark-800 rounded-xl shadow-sm border border-slate-100 dark:border-white/5">
          <Activity className="text-primary-500" size={24} />
        </div>
        <h2 className="text-3xl font-bold font-heading bg-gradient-to-r from-slate-800 to-slate-600 dark:from-white dark:to-slate-300 bg-clip-text text-transparent">Overview Dashboard</h2>
      </div>

      {/* Trending Topics Panel */}
      {topTrend && (
        <div className="glass-card rounded-2xl p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-l-4 border-rose-500 bg-gradient-to-r from-rose-500/10 to-transparent">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-rose-500/20 flex items-center justify-center text-rose-500">
              <Flame size={24} className="animate-pulse" />
            </div>
            <div>
              <h3 className="font-bold text-slate-800 dark:text-white flex items-center gap-2">
                Trending Anomalies 
                <span className="px-2 py-0.5 rounded-full text-[10px] bg-rose-500 text-white uppercase tracking-wider font-bold">24h</span>
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Spike detected: <span className="font-semibold text-rose-500 dark:text-rose-400">+{topTrend.count}</span> complaints related to <span className="font-semibold text-slate-800 dark:text-slate-200">'{topTrend.category}'</span>
              </p>
            </div>
          </div>
          <Link to="/analytics" className="px-4 py-2 bg-white dark:bg-dark-700 text-slate-800 dark:text-white rounded-xl text-sm font-semibold shadow-sm hover:shadow transition-all whitespace-nowrap">
            Investigate Trend
          </Link>
        </div>
      )}

      {/* Modern KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-5">
        {kpis.map((kpi, idx) => (
          <div key={kpi.label} className={clsx("glass-card rounded-2xl p-5 relative overflow-hidden group", "animate-slide-up")} style={{ animationDelay: `${idx * 100}ms` }}>
            <div className={`absolute top-0 right-0 w-24 h-24 bg-gradient-to-br ${kpi.gradient} opacity-10 rounded-bl-full group-hover:scale-110 group-hover:opacity-20 transition-all duration-500`}></div>
            <div className="flex flex-col gap-3 relative z-10">
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${kpi.gradient} flex items-center justify-center text-white shadow-lg ${kpi.shadow} transform group-hover:-translate-y-1 transition-all duration-300`}>
                <kpi.icon size={22} strokeWidth={2.5} />
              </div>
              <div className="mt-2">
                <p className="text-3xl font-black font-heading text-slate-800 dark:text-white tracking-tight">{kpi.value}</p>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400 mt-0.5">{kpi.label}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Complaints - Glassmorphic Table */}
        <div className="lg:col-span-2 glass-panel rounded-3xl overflow-hidden flex flex-col">
          <div className="p-6 border-b border-slate-100 dark:border-white/5 flex items-center justify-between bg-white/40 dark:bg-dark-800/40">
            <h3 className="text-lg font-bold font-heading text-slate-800 dark:text-white flex items-center gap-2">
              Recent Complaints
              <span className="flex h-2 w-2 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary-500"></span>
              </span>
            </h3>
            <Link to="/complaints" className="text-sm font-semibold text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 flex items-center gap-1 group transition-colors">
              View All <ChevronRight size={16} className="group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
          <div className="overflow-x-auto flex-1">
            <table className="w-full text-sm">
              <thead className="bg-slate-50/50 dark:bg-dark-800/50 backdrop-blur-sm">
                <tr>
                  <th className="text-left p-4 font-semibold text-slate-600 dark:text-slate-300 text-xs uppercase tracking-wider">Channel</th>
                  <th className="text-left p-4 font-semibold text-slate-600 dark:text-slate-300 text-xs uppercase tracking-wider">Subject</th>
                  <th className="text-left p-4 font-semibold text-slate-600 dark:text-slate-300 text-xs uppercase tracking-wider">Severity</th>
                  <th className="text-left p-4 font-semibold text-slate-600 dark:text-slate-300 text-xs uppercase tracking-wider">Status</th>
                  <th className="text-left p-4 font-semibold text-slate-600 dark:text-slate-300 text-xs uppercase tracking-wider">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-white/5">
                {recentComplaints.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50/80 dark:hover:bg-white/5 cursor-pointer transition-colors" onClick={() => window.location.href = `/complaints/${c.id}`}>
                    <td className="p-4">
                      <span className="px-3 py-1.5 rounded-lg text-xs bg-white dark:bg-dark-700 font-semibold text-slate-700 dark:text-slate-200 shadow-sm border border-slate-200 dark:border-white/5 capitalize tracking-wide">
                        {c.channel}
                      </span>
                    </td>
                    <td className="p-4">
                      <p className="text-slate-800 dark:text-slate-200 font-medium max-w-[200px] sm:max-w-xs truncate">{c.subject || c.body?.slice(0, 60)}</p>
                    </td>
                    <td className="p-4">
                      <span className={clsx("px-3 py-1 rounded-full text-[11px] font-bold text-white uppercase tracking-wider shadow-sm", SEVERITY_COLORS[c.severity] || 'bg-slate-500')}>
                        {c.severity}
                      </span>
                    </td>
                    <td className="p-4">
                      <span className={clsx("px-3 py-1 rounded-full text-[11px] font-bold text-white uppercase tracking-wider shadow-sm", STATUS_COLORS[c.status] || 'bg-slate-500')}>
                        {c.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="p-4 text-slate-500 dark:text-slate-400 text-xs font-medium">
                      {new Date(c.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                    </td>
                  </tr>
                ))}
                {recentComplaints.length === 0 && (
                  <tr>
                    <td colSpan={5} className="p-12 text-center text-slate-500">
                      <div className="flex flex-col items-center justify-center gap-3">
                        <MessageSquare className="opacity-20" size={48} />
                        <p className="font-medium">No complaints yet. Submit one to get started!</p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Live Feed Component wrapper */}
        <div className="glass-panel rounded-3xl overflow-hidden flex flex-col h-full">
          <LiveFeed />
        </div>
      </div>
    </div>
  );
}
