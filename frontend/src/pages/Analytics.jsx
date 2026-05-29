import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, Sparkles } from 'lucide-react';
import { getTrends, getRootCause, getWeeklySummary, getComplaintClusters } from '../api';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  BarChart, Bar, PieChart, Pie, Cell, ScatterChart, Scatter,
} from 'recharts';
import { SkeletonCard } from '../components/Skeleton';

const COLORS = ['#3b82f6', '#ef4444', '#f59e0b', '#22c55e', '#8b5cf6', '#ec4899', '#14b8a6'];

export default function Analytics() {
  const navigate = useNavigate();
  const [trends, setTrends] = useState([]);
  const [rootCause, setRootCause] = useState(null);
  const [weeklySummary, setWeeklySummary] = useState('');
  const [groupBy, setGroupBy] = useState('category');
  const [clusters, setClusters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generatingRCA, setGeneratingRCA] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => { loadData(); }, [groupBy]);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const [tRes, rRes, wRes, cRes] = await Promise.all([
        getTrends({ days: 30, group_by: groupBy }),
        getRootCause({ days: 30 }),
        getWeeklySummary(),
        getComplaintClusters(),
      ]);
      setTrends(tRes.data);
      setRootCause(rRes.data);
      setWeeklySummary(wRes.data.summary);
      setClusters(cRes.data);
    } catch (err) {
      setError('Failed to load analytics data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateRCA() {
    setGeneratingRCA(true);
    try {
      const rRes = await getRootCause({ days: 30 });
      setRootCause(rRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setGeneratingRCA(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <SkeletonCard lines={2} />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6"><SkeletonCard lines={6} /><SkeletonCard lines={6} /></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <AlertCircle size={40} className="text-red-400 mb-3" />
        <p className="text-gray-600 dark:text-gray-400">{error}</p>
        <button onClick={loadData} className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm">Retry</button>
      </div>
    );
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
      <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-6">Analytics</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trend Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-4 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-800 dark:text-gray-200">Complaint Trends (Last 30 Days)</h3>
            <div className="flex gap-2">
              {['category', 'channel', 'severity'].map((g) => (
                <button key={g} onClick={() => setGroupBy(g)}
                  className={`px-3 py-1 rounded-full text-xs border dark:border-gray-600 ${groupBy === g ? 'bg-blue-600 text-white' : 'text-gray-600 dark:text-gray-400'}`}>
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
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-4 relative">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-semibold text-gray-800 dark:text-gray-200">AI Deep Root Cause Analysis</h3>
            <button 
              onClick={handleGenerateRCA} 
              disabled={generatingRCA}
              className="px-3 py-1 bg-purple-600 text-white rounded-lg text-xs hover:bg-purple-700 disabled:opacity-50"
            >
              {generatingRCA ? 'Analyzing...' : 'Generate Deep RCA'}
            </button>
          </div>
          {rootCause ? (
            <div>
              <p className="text-sm text-gray-700 dark:text-gray-300 mb-4">{rootCause.summary}</p>
              <div className="mb-3">
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Top Categories</p>
                {rootCause.top_categories?.map((c, i) => (
                  <div key={i} className="flex justify-between text-sm py-1 dark:text-gray-300">
                    <span>{c.name || c.category}</span>
                    <span className="font-medium">{c.count}</span>
                  </div>
                ))}
              </div>
              <div>
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Recommendations</p>
                <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                  {rootCause.recommendations?.map((r, i) => <li key={i}>• {r}</li>)}
                </ul>
              </div>
            </div>
          ) : <p className="text-sm text-gray-400 dark:text-gray-500">No data available</p>}
        </div>

        {/* Category Distribution Pie */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-4">
          <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-3">Category Distribution</h3>
          {rootCause?.top_categories?.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie 
                  data={rootCause.top_categories.map(c => ({ ...c, displayLabel: c.name || c.category }))} 
                  dataKey="count" 
                  nameKey="displayLabel" 
                  cx="50%" 
                  cy="50%" 
                  innerRadius={50} 
                  outerRadius={90} 
                  label={({ displayLabel, count }) => `${displayLabel} (${count})`}
                >
                  {rootCause.top_categories.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value, name, props) => [value, props.payload.displayLabel]} />
              </PieChart>
            </ResponsiveContainer>
          ) : <p className="text-sm text-gray-400 dark:text-gray-500">No data available</p>}
        </div>

        {/* Semantic Clustering Scatter Plot */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-4 lg:col-span-2">
          <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-2">Complaint Semantic Clusters (PCA Map)</h3>
          <p className="text-xs text-gray-400 dark:text-gray-500 mb-4">
            High-dimensional embeddings of complaints projected into 2D space using Principal Component Analysis (PCA) and grouped using K-Means.
          </p>
          {clusters.length === 0 ? (
            <p className="text-sm text-gray-400 dark:text-gray-500 py-12 text-center">
              Not enough complaint data (minimum 3 complaints with vector embeddings required) to calculate clusters.
            </p>
          ) : (
            <div className="h-[350px] relative">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" dataKey="x" name="PCA Component 1" hide />
                  <YAxis type="number" dataKey="y" name="PCA Component 2" hide />
                  <Tooltip
                    cursor={{ strokeDasharray: '3 3' }}
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="bg-white dark:bg-gray-900 border dark:border-gray-700 p-3 rounded-lg shadow-lg text-xs max-w-sm">
                            <p className="font-bold text-gray-800 dark:text-gray-200 mb-1">{data.subject}</p>
                            <p className="text-gray-500 dark:text-gray-400 mb-1">
                              Category: <span className="font-medium text-blue-500">{data.category}</span>
                            </p>
                            <p className="text-gray-500 dark:text-gray-400 mb-1">
                              Status: <span className="font-medium capitalize">{data.status}</span>
                            </p>
                            <p className="text-purple-600 dark:text-purple-400 font-semibold mt-1">
                              {data.cluster_label}
                            </p>
                            <p className="text-[10px] text-gray-400 mt-2 italic">Click point to view details</p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Scatter
                    name="Complaints"
                    data={clusters}
                    onClick={(node) => {
                      if (node && node.id) {
                        navigate(`/complaints/${node.id}`);
                      }
                    }}
                  >
                    {clusters.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[entry.cluster_id % COLORS.length]}
                        className="cursor-pointer hover:scale-125 transition-transform"
                        r={8}
                      />
                    ))}
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Weekly Summary */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-4 lg:col-span-2">
          <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-3">AI Weekly Summary</h3>
          <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-line">{weeklySummary || 'No summary available'}</p>
        </div>
      </div>
    </div>
  );
}
