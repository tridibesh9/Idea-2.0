import { useEffect, useState } from 'react';
import { getTrends, getRootCause, getWeeklySummary } from '../api';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  BarChart, Bar, PieChart, Pie, Cell,
} from 'recharts';

const COLORS = ['#3b82f6', '#ef4444', '#f59e0b', '#22c55e', '#8b5cf6', '#ec4899', '#14b8a6'];

export default function Analytics() {
  const [trends, setTrends] = useState([]);
  const [rootCause, setRootCause] = useState(null);
  const [weeklySummary, setWeeklySummary] = useState('');
  const [groupBy, setGroupBy] = useState('category');
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, [groupBy]);

  async function loadData() {
    setLoading(true);
    try {
      const [tRes, rRes, wRes] = await Promise.all([
        getTrends({ days: 30, group_by: groupBy }),
        getRootCause({ days: 30 }),
        getWeeklySummary(),
      ]);
      setTrends(tRes.data);
      setRootCause(rRes.data);
      setWeeklySummary(wRes.data.summary);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div></div>;
  }

  // Aggregate trend data for the chart
  const dateMap = {};
  trends.forEach((t) => {
    if (!dateMap[t.date]) dateMap[t.date] = {};
    const key = t.category || t.channel || 'unknown';
    dateMap[t.date][key] = (dateMap[t.date][key] || 0) + t.count;
  });
  const chartData = Object.entries(dateMap).map(([date, vals]) => ({ date, ...vals }));
  const allKeys = [...new Set(trends.map(t => t.category || t.channel || 'unknown'))];

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Analytics</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trend Chart */}
        <div className="bg-white rounded-xl shadow-sm border p-4 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-800">Complaint Trends (Last 30 Days)</h3>
            <div className="flex gap-2">
              {['category', 'channel', 'severity'].map((g) => (
                <button key={g} onClick={() => setGroupBy(g)}
                  className={`px-3 py-1 rounded-full text-xs border ${groupBy === g ? 'bg-blue-600 text-white' : 'text-gray-600'}`}>
                  {g}
                </button>
              ))}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} />
              <YAxis />
              <Tooltip />
              <Legend />
              {allKeys.map((key, i) => (
                <Bar key={key} dataKey={key} stackId="a" fill={COLORS[i % COLORS.length]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Root Cause */}
        <div className="bg-white rounded-xl shadow-sm border p-4">
          <h3 className="font-semibold text-gray-800 mb-3">AI Root Cause Analysis</h3>
          {rootCause ? (
            <div>
              <p className="text-sm text-gray-700 mb-4">{rootCause.summary}</p>
              <div className="mb-3">
                <p className="text-xs font-medium text-gray-500 mb-2">Top Categories</p>
                {rootCause.top_categories?.map((c, i) => (
                  <div key={i} className="flex justify-between text-sm py-1">
                    <span>{c.category}</span>
                    <span className="font-medium">{c.count}</span>
                  </div>
                ))}
              </div>
              <div>
                <p className="text-xs font-medium text-gray-500 mb-2">Recommendations</p>
                <ul className="text-sm text-gray-600 space-y-1">
                  {rootCause.recommendations?.map((r, i) => <li key={i}>• {r}</li>)}
                </ul>
              </div>
            </div>
          ) : <p className="text-sm text-gray-400">No data available</p>}
        </div>

        {/* Category Distribution Pie */}
        <div className="bg-white rounded-xl shadow-sm border p-4">
          <h3 className="font-semibold text-gray-800 mb-3">Category Distribution</h3>
          {rootCause?.top_categories?.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={rootCause.top_categories} dataKey="count" nameKey="category" cx="50%" cy="50%" innerRadius={50} outerRadius={90} label>
                  {rootCause.top_categories.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : <p className="text-sm text-gray-400">No data available</p>}
        </div>

        {/* Weekly Summary */}
        <div className="bg-white rounded-xl shadow-sm border p-4 lg:col-span-2">
          <h3 className="font-semibold text-gray-800 mb-3">AI Weekly Summary</h3>
          <p className="text-sm text-gray-700 whitespace-pre-line">{weeklySummary || 'No summary available'}</p>
        </div>
      </div>
    </div>
  );
}
