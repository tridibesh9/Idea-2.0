import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter } from 'lucide-react';
import { getComplaints } from '../api';

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

  const pageSize = 20;

  useEffect(() => {
    loadComplaints();
  }, [page, filters]);

  async function loadComplaints() {
    setLoading(true);
    try {
      const params = { page, page_size: pageSize };
      Object.entries(filters).forEach(([k, v]) => { if (v) params[k] = v; });
      const res = await getComplaints(params);
      setComplaints(res.data.items);
      setTotal(res.data.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Complaints</h2>
        <Link
          to="/submit"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition"
        >
          + New Complaint
        </Link>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border p-4 mb-4 flex flex-wrap gap-3 items-center">
        <Filter size={16} className="text-gray-400" />
        {['status', 'category', 'severity', 'channel'].map((field) => (
          <select
            key={field}
            className="border rounded-lg px-3 py-1.5 text-sm text-gray-700 bg-white"
            value={filters[field]}
            onChange={(e) => { setFilters({ ...filters, [field]: e.target.value }); setPage(1); }}
          >
            <option value="">{field.charAt(0).toUpperCase() + field.slice(1)}: All</option>
            {field === 'status' && ['new', 'open', 'in_progress', 'escalated', 'resolved', 'closed'].map(v => <option key={v} value={v}>{v}</option>)}
            {field === 'category' && ['billing', 'product_defect', 'service_delay', 'account_access', 'delivery', 'refund', 'fraud'].map(v => <option key={v} value={v}>{v}</option>)}
            {field === 'severity' && ['critical', 'high', 'medium', 'low'].map(v => <option key={v} value={v}>{v}</option>)}
            {field === 'channel' && ['email', 'twitter', 'chat', 'phone', 'web_form'].map(v => <option key={v} value={v}>{v}</option>)}
          </select>
        ))}
        <span className="text-xs text-gray-400 ml-auto">{total} total complaints</span>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left p-3 font-medium text-gray-600">Channel</th>
              <th className="text-left p-3 font-medium text-gray-600">Subject</th>
              <th className="text-left p-3 font-medium text-gray-600">Category</th>
              <th className="text-left p-3 font-medium text-gray-600">Severity</th>
              <th className="text-left p-3 font-medium text-gray-600">Status</th>
              <th className="text-left p-3 font-medium text-gray-600">Sentiment</th>
              <th className="text-left p-3 font-medium text-gray-600">SLA</th>
              <th className="text-left p-3 font-medium text-gray-600">Date</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={8} className="p-8 text-center text-gray-400">Loading...</td></tr>
            ) : complaints.length === 0 ? (
              <tr><td colSpan={8} className="p-8 text-center text-gray-400">No complaints found</td></tr>
            ) : complaints.map((c) => (
              <tr key={c.id} className="border-t hover:bg-gray-50">
                <td className="p-3">
                  <span className="px-2 py-1 rounded-full text-xs bg-gray-100 font-medium">{c.channel}</span>
                </td>
                <td className="p-3 max-w-xs">
                  <Link to={`/complaints/${c.id}`} className="text-blue-600 hover:underline truncate block">
                    {c.subject || c.body?.slice(0, 60) || 'No subject'}
                  </Link>
                </td>
                <td className="p-3 text-gray-600">{c.category || '—'}</td>
                <td className="p-3">
                  <span className="px-2 py-1 rounded-full text-xs font-medium text-white" style={{ backgroundColor: SEVERITY_COLORS[c.severity] }}>{c.severity}</span>
                </td>
                <td className="p-3">
                  <span className="px-2 py-1 rounded-full text-xs font-medium text-white" style={{ backgroundColor: STATUS_COLORS[c.status] }}>{c.status}</span>
                </td>
                <td className="p-3 text-gray-600">{c.sentiment_score != null ? c.sentiment_score.toFixed(2) : '—'}</td>
                <td className="p-3">
                  {c.is_sla_breached ? (
                    <span className="text-red-600 font-medium text-xs">BREACHED</span>
                  ) : c.sla_deadline ? (
                    <span className="text-green-600 text-xs">On Track</span>
                  ) : '—'}
                </td>
                <td className="p-3 text-gray-500 text-xs">{new Date(c.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-4">
          <button disabled={page === 1} onClick={() => setPage(page - 1)} className="px-3 py-1 border rounded text-sm disabled:opacity-40">Prev</button>
          <span className="text-sm text-gray-600">Page {page} of {totalPages}</span>
          <button disabled={page === totalPages} onClick={() => setPage(page + 1)} className="px-3 py-1 border rounded text-sm disabled:opacity-40">Next</button>
        </div>
      )}
    </div>
  );
}
