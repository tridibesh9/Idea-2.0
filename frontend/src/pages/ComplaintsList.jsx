import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter, AlertCircle, UserCheck } from 'lucide-react';
import { getComplaints, getAgents, updateComplaint } from '../api';
import { SkeletonTable } from '../components/Skeleton';
import { useToast } from '../components/Toast';

const SEVERITY_COLORS = {
  critical: '#ef4444', high: '#f97316', medium: '#eab308', low: '#22c55e',
};
const STATUS_COLORS = {
  new: '#3b82f6', open: '#8b5cf6', in_progress: '#f59e0b',
  escalated: '#ef4444', resolved: '#22c55e', closed: '#6b7280',
};

export default function ComplaintsList() {
  const [complaints, setComplaints] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({ status: '', category: '', severity: '', channel: '' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState('assigned'); // all, assigned, department
  const [agents, setAgents] = useState([]);
  const [agentsMap, setAgentsMap] = useState({});
  const addToast = useToast();

  const pageSize = 20;
  const currentAgentId = localStorage.getItem('agent_id');
  const currentAgentRole = localStorage.getItem('agent_role');
  const currentAgentDept = localStorage.getItem('agent_dept');

  const isManager = currentAgentRole === 'supervisor' || currentAgentRole === 'manager';

  useEffect(() => {
    loadAgents();
  }, []);

  useEffect(() => {
    loadComplaints();
  }, [page, filters, viewMode]);

  async function loadAgents() {
    try {
      const res = await getAgents();
      setAgents(res.data);
      const m = {};
      res.data.forEach(a => { m[a.id] = a.name; });
      setAgentsMap(m);
    } catch (err) {
      console.error("Failed to load agents list", err);
    }
  }

  async function loadComplaints() {
    setLoading(true);
    setError(null);
    try {
      const params = { page, page_size: pageSize };
      Object.entries(filters).forEach(([k, v]) => { if (v) params[k] = v; });
      
      if (viewMode === 'assigned') {
        params.assigned_agent_id = currentAgentId;
      } else if (viewMode === 'department') {
        params.prioritize_dept = currentAgentDept;
      }

      const res = await getComplaints(params);
      setComplaints(res.data.items);
      setTotal(res.data.total);
    } catch (err) {
      setError('Failed to load complaints');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleAssign(complaintId, agentId) {
    try {
      const targetAgentId = agentId === "" ? null : agentId;
      await updateComplaint(complaintId, { assigned_agent_id: targetAgentId });
      addToast('Assignment updated successfully', 'success');
      loadComplaints();
    } catch (err) {
      addToast('Failed to update assignment', 'error');
    }
  }

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100 font-heading font-semibold">Complaints Feed</h2>
        <Link
          to="/submit"
          className="px-4 py-2 bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 text-white rounded-xl text-sm font-semibold shadow-md shadow-indigo-500/20 transition-all transform hover:-translate-y-0.5"
        >
          + Submit New
        </Link>
      </div>

      {/* View Mode Tabs */}
      <div className="flex gap-2">
        <button
          onClick={() => { setViewMode('all'); setPage(1); }}
          className={`px-4 py-2 text-xs font-bold rounded-xl transition-all border border-transparent ${viewMode === 'all' ? 'bg-indigo-600 text-white shadow-md' : 'bg-slate-100 dark:bg-dark-850 hover:bg-slate-200 dark:hover:bg-dark-800 text-slate-600 dark:text-slate-400'}`}
        >
          All Complaints
        </button>
        <button
          onClick={() => { setViewMode('assigned'); setPage(1); }}
          className={`px-4 py-2 text-xs font-bold rounded-xl transition-all border border-transparent ${viewMode === 'assigned' ? 'bg-indigo-600 text-white shadow-md' : 'bg-slate-100 dark:bg-dark-850 hover:bg-slate-200 dark:hover:bg-dark-800 text-slate-600 dark:text-slate-400'}`}
        >
          My Assigned
        </button>
        <button
          onClick={() => { setViewMode('department'); setPage(1); }}
          className={`px-4 py-2 text-xs font-bold rounded-xl transition-all border border-transparent ${viewMode === 'department' ? 'bg-indigo-600 text-white shadow-md' : 'bg-slate-100 dark:bg-dark-850 hover:bg-slate-200 dark:hover:bg-dark-800 text-slate-600 dark:text-slate-400'}`}
        >
          Department Priority ({currentAgentDept || 'None'})
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white/60 dark:bg-dark-900/60 backdrop-blur-xl border border-gray-200/50 dark:border-white/5 rounded-2xl p-4 flex flex-wrap gap-3 items-center shadow-sm">
        <Filter size={16} className="text-gray-400" />
        {['status', 'category', 'severity', 'channel'].map((field) => (
          <select
            key={field}
            className="border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2 text-xs text-gray-700 dark:text-gray-300 bg-white dark:bg-dark-800 focus:ring-2 focus:ring-indigo-500 focus:outline-none transition-all"
            value={filters[field]}
            onChange={(e) => { setFilters({ ...filters, [field]: e.target.value }); setPage(1); }}
          >
            <option value="">{field.charAt(0).toUpperCase() + field.slice(1)}: All</option>
            {field === 'status' && ['new', 'open', 'in_progress', 'escalated', 'resolved', 'closed'].map(v => <option key={v} value={v}>{v.replace('_', ' ')}</option>)}
            {field === 'category' && ['billing', 'product_defect', 'service_delay', 'account_access', 'delivery', 'refund', 'fraud'].map(v => <option key={v} value={v}>{v.replace('_', ' ')}</option>)}
            {field === 'severity' && ['critical', 'high', 'medium', 'low'].map(v => <option key={v} value={v}>{v}</option>)}
            {field === 'channel' && ['email', 'twitter', 'chat', 'phone', 'web_form'].map(v => <option key={v} value={v}>{v.replace('_', ' ')}</option>)}
          </select>
        ))}
        <span className="text-xs text-gray-400 dark:text-gray-500 ml-auto">{total} total complaints</span>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl p-6 text-center">
          <AlertCircle size={32} className="mx-auto mb-2 text-red-400" />
          <p className="text-red-700 dark:text-red-400">{error}</p>
          <button onClick={loadComplaints} className="mt-2 px-4 py-1.5 bg-red-600 text-white rounded-xl text-sm hover:bg-red-700 transition-all">Retry</button>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && !error && <SkeletonTable rows={8} cols={8} />}

      {/* Table */}
      {!loading && !error && (
        <div className="bg-white/60 dark:bg-dark-900/60 backdrop-blur-xl border border-gray-200/50 dark:border-white/5 rounded-2xl overflow-hidden shadow-xl">
          <table className="w-full text-xs">
            <thead className="bg-slate-50/50 dark:bg-dark-850/50 border-b border-slate-200/50 dark:border-white/5">
              <tr>
                <th className="text-left p-4 font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Channel</th>
                <th className="text-left p-4 font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Subject</th>
                <th className="text-left p-4 font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Category</th>
                <th className="text-left p-4 font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Severity</th>
                <th className="text-left p-4 font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Status</th>
                <th className="text-left p-4 font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Assigned Agent</th>
                <th className="text-left p-4 font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Sentiment</th>
                <th className="text-left p-4 font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">SLA</th>
                <th className="text-left p-4 font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-white/5">
              {complaints.length === 0 ? (
                <tr><td colSpan={9} className="p-8 text-center text-gray-400 dark:text-gray-500">No complaints found</td></tr>
              ) : complaints.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50/50 dark:hover:bg-dark-850/30 transition-colors">
                  <td className="p-4">
                    <span className="px-2.5 py-1 rounded-lg text-[10px] bg-slate-100 dark:bg-dark-800 font-bold dark:text-gray-300 capitalize">{c.channel}</span>
                  </td>
                  <td className="p-4 max-w-xs">
                    <Link to={`/complaints/${c.id}`} className="text-indigo-600 dark:text-indigo-400 hover:underline font-medium truncate block">
                      {c.subject || c.body?.slice(0, 60) || 'No subject'}
                    </Link>
                  </td>
                  <td className="p-4 text-slate-600 dark:text-slate-400 capitalize">{c.category ? c.category.replace('_', ' ') : '—'}</td>
                  <td className="p-4">
                    <span className="px-2 py-0.5 rounded-md text-[10px] font-bold text-white uppercase" style={{ backgroundColor: SEVERITY_COLORS[c.severity] }}>{c.severity}</span>
                  </td>
                  <td className="p-4">
                    <span className="px-2.5 py-1 rounded-full text-[10px] font-bold text-white capitalize" style={{ backgroundColor: STATUS_COLORS[c.status] }}>{c.status.replace('_', ' ')}</span>
                  </td>
                  <td className="p-4">
                    {isManager ? (
                      <select
                        className="border border-slate-200 dark:border-dark-850 rounded-lg px-2 py-1 bg-white dark:bg-dark-800 text-slate-700 dark:text-slate-300 focus:ring-1 focus:ring-indigo-500 focus:outline-none transition-all"
                        value={c.assigned_agent_id || ''}
                        onChange={(e) => handleAssign(c.id, e.target.value)}
                      >
                        <option value="">Unassigned</option>
                        {agents.map(a => (
                          <option key={a.id} value={a.id}>{a.name} ({a.department})</option>
                        ))}
                      </select>
                    ) : (
                      <span className="text-slate-600 dark:text-slate-400 font-medium">
                        {agentsMap[c.assigned_agent_id] || 'Unassigned'}
                      </span>
                    )}
                  </td>
                  <td className="p-4 text-slate-600 dark:text-slate-400 font-mono font-medium">{c.sentiment_score != null ? c.sentiment_score.toFixed(2) : '—'}</td>
                  <td className="p-4">
                    {c.is_sla_breached ? (
                      <span className="text-red-600 dark:text-red-400 font-bold text-[10px] bg-red-50 dark:bg-red-950/20 px-2 py-1 rounded-md">BREACHED</span>
                    ) : c.sla_deadline ? (
                      <span className="text-emerald-600 dark:text-emerald-400 font-bold text-[10px] bg-green-50 dark:bg-green-950/20 px-2 py-1 rounded-md">On Track</span>
                    ) : '—'}
                  </td>
                  <td className="p-4 text-slate-500 dark:text-slate-400 font-medium">{new Date(c.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-4">
          <button disabled={page === 1} onClick={() => setPage(page - 1)} className="px-3 py-1 bg-white dark:bg-dark-800 border dark:border-slate-800 rounded-lg text-xs disabled:opacity-40 text-slate-600 dark:text-slate-400 hover:bg-slate-50 transition-all">Prev</button>
          <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">Page {page} of {totalPages}</span>
          <button disabled={page === totalPages} onClick={() => setPage(page + 1)} className="px-3 py-1 bg-white dark:bg-dark-800 border dark:border-slate-800 rounded-lg text-xs disabled:opacity-40 text-slate-600 dark:text-slate-400 hover:bg-slate-50 transition-all">Next</button>
        </div>
      )}
    </div>
  );
}
