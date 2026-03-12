import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle } from 'lucide-react';
import { getEscalations } from '../api';

export default function Escalations() {
  const [escalations, setEscalations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await getEscalations({ status: 'active' });
        setEscalations(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div></div>;
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
        <AlertTriangle className="text-red-500" /> Escalation Queue
      </h2>

      {escalations.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border p-8 text-center text-gray-400">
          <AlertTriangle size={40} className="mx-auto mb-3 opacity-30" />
          <p>No active escalations</p>
        </div>
      ) : (
        <div className="space-y-3">
          {escalations.map((e) => (
            <div key={e.id} className="bg-white rounded-xl shadow-sm border p-4 flex items-center justify-between">
              <div>
                <Link to={`/complaints/${e.complaint_id}`} className="text-blue-600 hover:underline font-medium text-sm">
                  Complaint {e.complaint_id.slice(0, 8)}...
                </Link>
                <p className="text-sm text-gray-600 mt-1">{e.reason}</p>
                <p className="text-xs text-gray-400">Escalated by {e.escalated_by} · {new Date(e.created_at).toLocaleString()}</p>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                e.status === 'active' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'
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
