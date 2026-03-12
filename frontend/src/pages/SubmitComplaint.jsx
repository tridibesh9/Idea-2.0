import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Send, Mail, MessageCircle, Twitter, Phone, Globe } from 'lucide-react';
import { createComplaint } from '../api';

const channels = [
  { id: 'email', label: 'Email', icon: Mail },
  { id: 'chat', label: 'Chat', icon: MessageCircle },
  { id: 'twitter', label: 'Twitter/X', icon: Twitter },
  { id: 'phone', label: 'Phone', icon: Phone },
  { id: 'web_form', label: 'Web Form', icon: Globe },
];

export default function SubmitComplaint() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    channel: 'web_form',
    subject: '',
    body: '',
    customer_name: '',
    customer_email: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.body.trim()) { setError('Complaint text is required'); return; }
    setSubmitting(true);
    setError('');
    try {
      const res = await createComplaint(form);
      navigate(`/complaints/${res.data.id}`);
    } catch (err) {
      setError('Failed to submit complaint. Is the backend running?');
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-6">Submit a Complaint</h2>

      <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-6 space-y-4">
        {/* Channel Selector */}
        <div>
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300 block mb-2">Channel</label>
          <div className="flex gap-2 flex-wrap">
            {channels.map(({ id, label, icon: Icon }) => (
              <button key={id} type="button"
                onClick={() => setForm({ ...form, channel: id })}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm transition ${
                  form.channel === id ? 'bg-blue-600 text-white border-blue-600' : 'bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 dark:border-gray-600'
                }`}>
                <Icon size={14} /> {label}
              </button>
            ))}
          </div>
        </div>

        {/* Customer Info */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300 block mb-1">Name</label>
            <input className="w-full border dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 dark:text-gray-200" placeholder="Customer name"
              value={form.customer_name} onChange={(e) => setForm({ ...form, customer_name: e.target.value })} />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300 block mb-1">Email</label>
            <input className="w-full border dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 dark:text-gray-200" placeholder="customer@example.com" type="email"
              value={form.customer_email} onChange={(e) => setForm({ ...form, customer_email: e.target.value })} />
          </div>
        </div>

        {/* Subject */}
        <div>
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300 block mb-1">Subject</label>
          <input className="w-full border dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 dark:text-gray-200" placeholder="Brief subject line"
            value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} />
        </div>

        {/* Complaint Body */}
        <div>
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300 block mb-1">Complaint *</label>
          <textarea className="w-full border dark:border-gray-600 rounded-lg px-3 py-2 text-sm h-40 bg-white dark:bg-gray-700 dark:text-gray-200" placeholder="Describe the issue in detail..."
            value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })} />
        </div>

        {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}

        <button type="submit" disabled={submitting}
          className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition flex items-center justify-center gap-2 disabled:opacity-50">
          <Send size={16} /> {submitting ? 'Submitting & Classifying...' : 'Submit Complaint'}
        </button>

        <p className="text-xs text-gray-400 dark:text-gray-500 text-center">
          The complaint will be automatically classified by AI upon submission.
        </p>
      </form>
    </div>
  );
}
