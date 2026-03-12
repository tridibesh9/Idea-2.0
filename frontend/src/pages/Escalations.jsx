import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, AlertCircle } from 'lucide-react';
import { getEscalations } from '../api';
import { SkeletonCard } from '../components/Skeleton';

export default function Escalations() {
  const [escalations, setEscalations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => { load(); }, []);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await getEscalations({ status: 'active' });
      setEscalations(res.data);
    } catch (err) {
      setError('Failed to load escalations');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <div className="space-y-3"><SkeletonCard lines={2} /><SkeletonCard lines={2} /><SkeletonCard lines={2} /></div>;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <AlertCircle size={40} className="text-red-400 mb-3" />
        <p className="text-gray-600 dark:text-gray-400">{error}</p>
        <button onClick={load} className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm">Retry</button>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-6 flex items-center gap-2">
        <AlertTriangle className="text-red-500" /> Escalation Queue
      </h2>

      {escalations.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-8 text-center text-gray-400 dark:text-gray-500">
          <AlertTriangle size={40} className="mx-auto mb-3 opacity-30" />
          <p>No active escalations</p>
        </div>
      ) : (
        <div className="space-y-3">
          {escalations.map((e) => (
            <div key={e.id} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-4 flex items-center justify-between">
              <div>
                <Link to={`/complaints/${e.complaint_id}`} className="text-blue-600 hover:underline font-medium text-sm">
                  Complaint {e.complaint_id.slice(0, 8)}...
                </Link>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{e.reason}</p>
                <p className="text-xs text-gray-400 dark:text-gray-500">Escalated by {e.escalated_by} · {new Date(e.created_at).toLocaleString()}</p>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                e.status === 'active' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
              }`}>
                {e.status}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
