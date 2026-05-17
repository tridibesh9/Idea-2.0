import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft, Clock, AlertCircle, Send, Sparkles, History, Users,
} from 'lucide-react';
import {
  getComplaint, getTimeline, getSimilar, generateResponse, addMessage, getAuditTrail, updateComplaint,
} from '../api';
import { SkeletonCard } from '../components/Skeleton';

const SEVERITY_COLORS = { critical: '#ef4444', high: '#f97316', medium: '#eab308', low: '#22c55e' };
const STATUS_COLORS = { new: '#3b82f6', open: '#8b5cf6', in_progress: '#f59e0b', escalated: '#ef4444', resolved: '#22c55e', closed: '#6b7280' };

export default function ComplaintDetail() {
  const { id } = useParams();
  const [complaint, setComplaint] = useState(null);
  const [messages, setMessages] = useState([]);
  const [similar, setSimilar] = useState([]);
  const [audit, setAudit] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // AI Response
  const [showAiModal, setShowAiModal] = useState(false);
  const [aiDraft, setAiDraft] = useState('');
  const [aiTone, setAiTone] = useState('empathetic');
  const [aiActions, setAiActions] = useState([]);
  const [generating, setGenerating] = useState(false);

  // New message
  const [newMessage, setNewMessage] = useState('');

  useEffect(() => { loadAll(); }, [id]);

  async function loadAll() {
    setLoading(true);
    setError(null);
    try {
      const [cRes, tRes, sRes, aRes] = await Promise.all([
        getComplaint(id),
        getTimeline(id),
        getSimilar(id),
        getAuditTrail(id),
      ]);
      setComplaint(cRes.data);
      setMessages(tRes.data);
      setSimilar(sRes.data);
      setAudit(aRes.data);
    } catch (err) {
      setError('Failed to load complaint details');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateResponse() {
    setGenerating(true);
    try {
      const res = await generateResponse(id, { tone: aiTone });
      setAiDraft(res.data.draft_text);
      setAiActions(res.data.suggested_actions);
      setShowAiModal(true);
    } catch (err) {
      console.error(err);
    } finally {
      setGenerating(false);
    }
  }

  async function handleSendMessage(content) {
    if (!content.trim()) return;
    await addMessage(id, { sender_type: 'agent', sender_name: 'Agent', content });
    setNewMessage('');
    setShowAiModal(false);
    loadAll();
  }

  async function handleStatusChange(status) {
    await updateComplaint(id, { status });
    loadAll();
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <SkeletonCard lines={2} />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4"><SkeletonCard lines={4} /><SkeletonCard lines={6} /></div>
          <div className="space-y-4"><SkeletonCard lines={3} /><SkeletonCard lines={3} /></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <AlertCircle size={40} className="text-red-400 mb-3" />
        <p className="text-gray-600 dark:text-gray-400">{error}</p>
        <button onClick={loadAll} className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm">Retry</button>
      </div>
    );
  }

  if (!complaint) {
    return <div className="text-center py-12 text-gray-400 dark:text-gray-500">Complaint not found</div>;
  }

  const keyIssues = complaint.key_issues ? JSON.parse(complaint.key_issues) : [];
  const regFlags = complaint.regulatory_flags ? JSON.parse(complaint.regulatory_flags) : [];

  return (
    <div>
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <Link to="/complaints" className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg dark:text-gray-300"><ArrowLeft size={18} /></Link>
        <div className="flex-1">
          <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100">{complaint.subject || 'Complaint Detail'}</h2>
          <p className="text-xs text-gray-400 dark:text-gray-500">ID: {complaint.id}</p>
        </div>
        <div className="flex gap-2">
          <span className="px-3 py-1 rounded-full text-xs font-medium text-white" style={{ backgroundColor: SEVERITY_COLORS[complaint.severity] }}>{complaint.severity}</span>
          <span className="px-3 py-1 rounded-full text-xs font-medium text-white" style={{ backgroundColor: STATUS_COLORS[complaint.status] }}>{complaint.status}</span>
          <span className="px-3 py-1 rounded-full text-xs bg-gray-100 dark:bg-gray-700 font-medium dark:text-gray-300">{complaint.channel}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column — Timeline + Actions */}
        <div className="lg:col-span-2 space-y-4">
          {/* AI Classification Card */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-4">
            <h3 className="font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2 mb-3">
              <Sparkles size={16} className="text-purple-500" /> AI Classification
              {complaint.ai_confidence_score && (
                <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full ml-auto">
                  {(complaint.ai_confidence_score * 100).toFixed(0)}% confidence
                </span>
              )}
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <div><span className="text-gray-400 text-xs">Category</span><p className="font-medium">{complaint.category || '—'}</p></div>
              <div><span className="text-gray-400 text-xs">Product</span><p className="font-medium">{complaint.product || '—'}</p></div>
              <div><span className="text-gray-400 text-xs">Sentiment</span><p className="font-medium">{complaint.sentiment_label} ({complaint.sentiment_score?.toFixed(2)})</p></div>
              <div><span className="text-gray-400 text-xs">Severity</span><p className="font-medium capitalize">{complaint.severity}</p></div>
            </div>
            {keyIssues.length > 0 && (
              <div className="mt-3">
                <span className="text-gray-400 text-xs">Key Issues</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {keyIssues.map((issue, i) => (
                    <span key={i} className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs">{issue}</span>
                  ))}
                </div>
              </div>
            )}
            {regFlags.length > 0 && (
              <div className="mt-3">
                <span className="text-red-500 text-xs font-medium">⚠ Regulatory Flags</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {regFlags.map((flag, i) => (
                    <span key={i} className="px-2 py-0.5 bg-red-50 text-red-700 rounded text-xs">{flag}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Communication Timeline */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-4">
            <h3 className="font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2 mb-4">
              <History size={16} /> Communication Timeline
            </h3>
            <div className="space-y-4 max-h-[500px] overflow-y-auto">
              <div className="flex justify-start">
                  <div className="max-w-[75%] rounded-xl px-4 py-3 text-sm bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200 border dark:border-gray-600">
                    <p className="text-xs font-semibold mb-2 opacity-70">Original Complaint</p>
                    <p className="whitespace-pre-wrap">{complaint.body}</p>
                    {/* Multimodal Image Attachment Rendering */}
                    <div className="mt-3">
                      <img 
                        src={`http://localhost:8000/api/complaints/${complaint.id}/image`} 
                        alt="User Attachment" 
                        className="max-w-full h-auto rounded-lg border border-gray-300 dark:border-gray-600"
                        onError={(e) => { e.target.style.display = 'none'; }}
                      />
                    </div>
                    <p className="text-[10px] mt-2 opacity-50">{new Date(complaint.created_at).toLocaleString()}</p>
                  </div>
              </div>

              {messages.filter(m => m.created_at !== complaint.created_at).map((msg) => (
                <div key={msg.id} className={`flex ${msg.sender_type === 'customer' ? 'justify-start' : 'justify-end'}`}>
                  <div className={`max-w-[75%] rounded-xl px-4 py-2 text-sm ${
                    msg.sender_type === 'customer' ? 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200 border dark:border-gray-600' :
                    msg.sender_type === 'system' ? 'bg-purple-100 text-purple-800 border border-purple-200' :
                    'bg-blue-600 text-white shadow-sm'
                  }`}>
                    <p className="text-xs font-medium mb-1 opacity-70">{msg.sender_name || msg.sender_type}</p>
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    <p className="text-[10px] mt-1 opacity-50">{new Date(msg.created_at).toLocaleString()}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Reply Box */}
            <div className="mt-4 flex gap-2">
              <input
                className="flex-1 border dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 dark:text-gray-200"
                placeholder="Type a response..."
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendMessage(newMessage)}
              />
              <button onClick={() => handleSendMessage(newMessage)} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"><Send size={14} /></button>
              <button onClick={handleGenerateResponse} disabled={generating} className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 flex items-center gap-1 disabled:opacity-50">
                <Sparkles size={14} /> {generating ? 'Generating...' : 'AI Draft'}
              </button>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-2">
            {complaint.status !== 'resolved' && (
              <button onClick={() => handleStatusChange('resolved')} className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700">Mark Resolved</button>
            )}
            {complaint.status !== 'escalated' && complaint.status !== 'resolved' && (
              <button onClick={() => handleStatusChange('escalated')} className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700">Escalate</button>
            )}
            {complaint.status === 'new' && (
              <button onClick={() => handleStatusChange('in_progress')} className="px-4 py-2 bg-yellow-500 text-white rounded-lg text-sm hover:bg-yellow-600">Start Working</button>
            )}
          </div>
        </div>

        {/* Right Column — Info Panels */}
        <div className="space-y-4">
          {/* SLA Tracker */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-4">
            <h3 className="font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2 mb-3">
              <Clock size={16} /> SLA Tracker
            </h3>
            {complaint.sla_deadline ? (
              <SLABar deadline={complaint.sla_deadline} createdAt={complaint.created_at} breached={complaint.is_sla_breached} />
            ) : (
              <p className="text-sm text-gray-400 dark:text-gray-500">No SLA set</p>
            )}
          </div>

          {/* Similar Complaints */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-4">
            <h3 className="font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2 mb-3">
              <Users size={16} /> Related Complaints
            </h3>
            {similar.length === 0 ? (
              <p className="text-sm text-gray-400 dark:text-gray-500">No related complaints found</p>
            ) : (
              <div className="space-y-2">
                {similar.map((s) => (
                  <Link key={s.complaint_id} to={`/complaints/${s.complaint_id}`} className="block p-2 rounded-lg hover:bg-gray-50 border text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-700 truncate flex-1">{s.subject || s.category}</span>
                      <span className="text-purple-600 font-medium text-xs ml-2">{(s.similarity_score * 100).toFixed(0)}%</span>
                    </div>
                    <div className="flex gap-1 mt-1">
                      <span className="px-1.5 py-0.5 rounded text-[10px] text-white" style={{ backgroundColor: SEVERITY_COLORS[s.severity] }}>{s.severity}</span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] text-white" style={{ backgroundColor: STATUS_COLORS[s.status] }}>{s.status}</span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Audit Trail */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-4">
            <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-3">Audit Trail</h3>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {audit.map((a) => (
                <div key={a.id} className="text-xs border-l-2 border-gray-200 dark:border-gray-600 pl-3 py-1">
                  <p className="font-medium text-gray-700 dark:text-gray-300">{a.action}</p>
                  <p className="text-gray-400 dark:text-gray-500">{a.performed_by} · {new Date(a.created_at).toLocaleString()}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* AI Response Modal */}
      {showAiModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-2xl p-6 mx-4">
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2 dark:text-gray-100"><Sparkles className="text-purple-500" /> AI Generated Response</h3>
            <div className="flex gap-2 mb-3">
              {['formal', 'empathetic', 'neutral'].map((t) => (
                <button key={t} onClick={() => { setAiTone(t); handleGenerateResponse(); }}
                  className={`px-3 py-1 rounded-full text-xs border ${aiTone === t ? 'bg-purple-600 text-white border-purple-600' : 'text-gray-600'}`}>
                  {t}
                </button>
              ))}
            </div>
            <textarea className="w-full border dark:border-gray-600 rounded-lg p-3 text-sm h-48 bg-white dark:bg-gray-700 dark:text-gray-200" value={aiDraft} onChange={(e) => setAiDraft(e.target.value)} />
            {aiActions.length > 0 && (
              <div className="mt-3">
                <p className="text-xs font-medium text-gray-500 mb-1">Suggested Actions:</p>
                <ul className="text-xs text-gray-600 space-y-1">
                  {aiActions.map((a, i) => <li key={i}>• {a}</li>)}
                </ul>
              </div>
            )}
            <div className="flex gap-2 mt-4 justify-end">
              <button onClick={() => setShowAiModal(false)} className="px-4 py-2 border dark:border-gray-600 rounded-lg text-sm dark:text-gray-300">Cancel</button>
              <button onClick={() => handleSendMessage(aiDraft)} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">Send Response</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SLABar({ deadline, createdAt, breached }) {
  const now = new Date();
  const start = new Date(createdAt);
  const end = new Date(deadline);
  const total = end - start;
  const elapsed = now - start;
  const pct = Math.min(100, Math.max(0, (elapsed / total) * 100));
  const remaining = Math.max(0, end - now);
  const hours = Math.floor(remaining / 3600000);
  const minutes = Math.floor((remaining % 3600000) / 60000);

  const color = breached ? 'bg-red-500' : pct > 80 ? 'bg-yellow-500' : 'bg-green-500';

  return (
    <div>
      <div className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <div className="flex justify-between mt-1 text-xs text-gray-500">
        <span>{pct.toFixed(0)}% elapsed</span>
        <span className={breached ? 'text-red-600 font-medium' : ''}>
          {breached ? 'SLA BREACHED' : `${hours}h ${minutes}m remaining`}
        </span>
      </div>
    </div>
  );
}
