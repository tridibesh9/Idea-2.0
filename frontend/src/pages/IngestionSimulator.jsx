import { useState, useEffect } from 'react';
import { Mail, MessageCircle, Twitter, AlertCircle, RefreshCw, Send, CheckCircle2 } from 'lucide-react';
import { 
  simulateIncomingEmail, 
  simulateIncomingTelegram, 
  getSentMessages,
  createComplaint
} from '../api';

export default function IngestionSimulator() {
  const [loading, setLoading] = useState(null);
  const [result, setResult] = useState(null);
  
  // Custom incoming email state
  const [emailForm, setEmailForm] = useState({
    from_name: 'David Miller',
    from_email: 'david.miller@example.com',
    subject: 'Double charge on my savings account',
    body: 'Hello, I see two identical charges of $150.00 on my savings account today. Please refund one of them.'
  });

  // Custom incoming telegram state
  const [tgForm, setTgForm] = useState({
    chat_id: String(Math.floor(100000 + Math.random() * 900000)),
    first_name: 'Alex',
    text: 'Hello support, my debit card has not arrived yet. It has been two weeks.'
  });

  // Sent logs state
  const [logs, setLogs] = useState({ emails: [], telegram: [] });
  const [activeLogTab, setActiveLogTab] = useState('email');
  const [refreshingLogs, setRefreshingLogs] = useState(false);

  useEffect(() => {
    fetchLogs();
  }, []);

  async function fetchLogs() {
    setRefreshingLogs(true);
    try {
      const res = await getSentMessages();
      setLogs(res.data);
    } catch (err) {
      console.error('Failed to load sent logs:', err);
    } finally {
      setRefreshingLogs(false);
    }
  }

  const handleSimulateQuick = async (channel) => {
    setLoading(channel);
    setResult(null);
    try {
      const payloads = {
        twitter: {
          channel: 'twitter',
          customer_name: '@angry_user_99',
          body: 'This new update is GARBAGE! My app crashes every time I try to login. And who thought it was a good idea to charge my card 4567-1234-9876-0000 twice?! Fix it NOW! #fail',
        },
        whatsapp: {
          channel: 'whatsapp',
          customer_name: '+1-555-0198',
          body: 'Hi, I need help. My order ORD-99882 hasn\'t arrived yet. It was supposed to be here 3 days ago.',
        }
      };

      const res = await createComplaint(payloads[channel]);
      setResult({ ...res.data, source: 'Quick Simulator' });
      fetchLogs();
    } catch (err) {
      console.error(err);
      setResult({ error: 'Failed to simulate quick complaint' });
    } finally {
      setLoading(null);
    }
  };

  const handleSimulateEmail = async (e) => {
    e.preventDefault();
    setLoading('email_form');
    setResult(null);
    try {
      const res = await simulateIncomingEmail(emailForm);
      setResult({ 
        success: true, 
        message: `EML file '${res.data.file}' written to mock_emails/inbox. The background listener will ingest it shortly! Check the complaints feed.`,
        source: 'Mock Inbound Email'
      });
      fetchLogs();
    } catch (err) {
      console.error(err);
      setResult({ error: 'Failed to simulate incoming email file' });
    } finally {
      setLoading(null);
    }
  };

  const handleSimulateTelegram = async (e) => {
    e.preventDefault();
    setLoading('tg_form');
    setResult(null);
    try {
      const res = await simulateIncomingTelegram(tgForm);
      setResult({
        success: true,
        message: `JSON update file '${res.data.file}' written to mock_telegram/inbox. The background listener will ingest it shortly! Check the complaints feed.`,
        source: 'Mock Inbound Telegram'
      });
      // Generate new chat id for next time
      setTgForm(prev => ({ ...prev, chat_id: String(Math.floor(100000 + Math.random() * 900000)) }));
      fetchLogs();
    } catch (err) {
      console.error(err);
      setResult({ error: 'Failed to simulate incoming telegram update' });
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="max-w-6xl mx-auto py-6 space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-2">Two-Way Integration & Simulator</h2>
        <p className="text-gray-600 dark:text-gray-400">
          Simulate incoming omnichannel customer messages, trigger background listeners, and verify outgoing response logs in real-time.
        </p>
      </div>

      {/* Main Grid: Simulation Forms (Left) and Logs (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Left Column: Intake simulators */}
        <div className="space-y-6">
          
          {/* Quick Simulators */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border dark:border-gray-700 p-6 shadow-sm">
            <h3 className="text-base font-bold text-gray-800 dark:text-gray-200 mb-4">Quick Intake Simulators</h3>
            <div className="grid grid-cols-2 gap-4">
              <button 
                onClick={() => handleSimulateQuick('twitter')}
                disabled={loading !== null}
                className="p-4 bg-blue-50 hover:bg-blue-100 dark:bg-blue-900/20 dark:hover:bg-blue-900/30 border border-blue-100 dark:border-blue-800 rounded-xl flex flex-col items-center text-center transition"
              >
                <Twitter size={24} className="text-blue-500 mb-2" />
                <span className="text-xs font-bold text-gray-800 dark:text-gray-200">Simulate Tweet</span>
                <span className="text-[10px] text-gray-400 mt-1">Exposes credit card details</span>
              </button>
              <button 
                onClick={() => handleSimulateQuick('whatsapp')}
                disabled={loading !== null}
                className="p-4 bg-green-50 hover:bg-green-100 dark:bg-green-900/20 dark:hover:bg-green-900/30 border border-green-100 dark:border-green-800 rounded-xl flex flex-col items-center text-center transition"
              >
                <MessageCircle size={24} className="text-green-500 mb-2" />
                <span className="text-xs font-bold text-gray-800 dark:text-gray-200">Simulate WhatsApp</span>
                <span className="text-[10px] text-gray-400 mt-1">Delayed delivery check</span>
              </button>
            </div>
          </div>

          {/* Two-way Email simulator */}
          <form onSubmit={handleSimulateEmail} className="bg-white dark:bg-gray-800 rounded-xl border dark:border-gray-700 p-6 shadow-sm space-y-4">
            <h3 className="text-base font-bold text-gray-800 dark:text-gray-200 flex items-center gap-2">
              <Mail className="text-purple-500" size={20} /> Simulate Inbound Email (.eml)
            </h3>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <label className="text-gray-500 block mb-1">Sender Name</label>
                <input 
                  type="text" 
                  value={emailForm.from_name}
                  onChange={e => setEmailForm(prev => ({ ...prev, from_name: e.target.value }))}
                  className="w-full border dark:border-gray-600 rounded p-2 bg-white dark:bg-gray-700 dark:text-gray-200" 
                  required
                />
              </div>
              <div>
                <label className="text-gray-500 block mb-1">Sender Email</label>
                <input 
                  type="email" 
                  value={emailForm.from_email}
                  onChange={e => setEmailForm(prev => ({ ...prev, from_email: e.target.value }))}
                  className="w-full border dark:border-gray-600 rounded p-2 bg-white dark:bg-gray-700 dark:text-gray-200" 
                  required
                />
              </div>
            </div>
            <div className="text-xs">
              <label className="text-gray-500 block mb-1">Subject</label>
              <input 
                type="text" 
                value={emailForm.subject}
                onChange={e => setEmailForm(prev => ({ ...prev, subject: e.target.value }))}
                className="w-full border dark:border-gray-600 rounded p-2 bg-white dark:bg-gray-700 dark:text-gray-200" 
                required
              />
            </div>
            <div className="text-xs">
              <label className="text-gray-500 block mb-1">Body Content</label>
              <textarea 
                value={emailForm.body}
                onChange={e => setEmailForm(prev => ({ ...prev, body: e.target.value }))}
                rows={3}
                className="w-full border dark:border-gray-600 rounded p-2 bg-white dark:bg-gray-700 dark:text-gray-200" 
                required
              />
            </div>
            <button 
              type="submit"
              disabled={loading !== null}
              className="w-full py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-bold flex justify-center items-center gap-1 disabled:opacity-50"
            >
              {loading === 'email_form' ? <RefreshCw size={14} className="animate-spin" /> : <Send size={12} />}
              Simulate Email File Creation
            </button>
          </form>

          {/* Two-way Telegram simulator */}
          <form onSubmit={handleSimulateTelegram} className="bg-white dark:bg-gray-800 rounded-xl border dark:border-gray-700 p-6 shadow-sm space-y-4">
            <h3 className="text-base font-bold text-gray-800 dark:text-gray-200 flex items-center gap-2">
              <MessageCircle className="text-blue-500" size={20} /> Simulate Inbound Telegram Update (.json)
            </h3>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <label className="text-gray-500 block mb-1">Chat ID (External ID)</label>
                <input 
                  type="text" 
                  value={tgForm.chat_id}
                  onChange={e => setTgForm(prev => ({ ...prev, chat_id: e.target.value }))}
                  className="w-full border dark:border-gray-600 rounded p-2 bg-white dark:bg-gray-700 dark:text-gray-200" 
                  required
                />
              </div>
              <div>
                <label className="text-gray-500 block mb-1">First Name</label>
                <input 
                  type="text" 
                  value={tgForm.first_name}
                  onChange={e => setTgForm(prev => ({ ...prev, first_name: e.target.value }))}
                  className="w-full border dark:border-gray-600 rounded p-2 bg-white dark:bg-gray-700 dark:text-gray-200" 
                  required
                />
              </div>
            </div>
            <div className="text-xs">
              <label className="text-gray-500 block mb-1">Message Body</label>
              <textarea 
                value={tgForm.text}
                onChange={e => setTgForm(prev => ({ ...prev, text: e.target.value }))}
                rows={2}
                className="w-full border dark:border-gray-600 rounded p-2 bg-white dark:bg-gray-700 dark:text-gray-200" 
                required
              />
            </div>
            <button 
              type="submit"
              disabled={loading !== null}
              className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold flex justify-center items-center gap-1 disabled:opacity-50"
            >
              {loading === 'tg_form' ? <RefreshCw size={14} className="animate-spin" /> : <Send size={12} />}
              Simulate Telegram File Creation
            </button>
          </form>

        </div>

        {/* Right Column: Outgoing Sent Logs Center */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border dark:border-gray-700 shadow-sm flex flex-col h-[750px]">
          
          {/* Header tabs */}
          <div className="p-4 border-b dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-gray-800/50 rounded-t-xl">
            <div className="flex gap-2">
              <button 
                onClick={() => setActiveLogTab('email')}
                className={`px-4 py-1.5 rounded-lg text-xs font-bold transition ${activeLogTab === 'email' ? 'bg-purple-600 text-white shadow-sm' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'}`}
              >
                Mock Outbox (Emails)
              </button>
              <button 
                onClick={() => setActiveLogTab('telegram')}
                className={`px-4 py-1.5 rounded-lg text-xs font-bold transition ${activeLogTab === 'telegram' ? 'bg-blue-600 text-white shadow-sm' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'}`}
              >
                Mock Outbox (Telegram)
              </button>
            </div>
            <button 
              onClick={fetchLogs}
              disabled={refreshingLogs}
              className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300 disabled:opacity-40"
              title="Refresh outbox logs"
            >
              <RefreshCw size={14} className={refreshingLogs ? 'animate-spin' : ''} />
            </button>
          </div>

          {/* Logs feed */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {activeLogTab === 'email' ? (
              logs.emails.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center text-gray-400 dark:text-gray-500 py-12">
                  <Mail size={36} className="mb-2 opacity-50" />
                  <p className="text-sm">No outgoing emails found in outbox.</p>
                  <p className="text-xs mt-1">Reply to an email complaint to see it here.</p>
                </div>
              ) : (
                logs.emails.map((email) => (
                  <div key={email.id} className="p-3 bg-gray-50 dark:bg-gray-700/40 border dark:border-gray-700 rounded-xl space-y-2 text-xs relative">
                    <span className="absolute top-3 right-3 text-[10px] text-gray-400">{new Date(email.timestamp).toLocaleString()}</span>
                    <div className="pr-20">
                      <p className="text-gray-400">To: <span className="text-gray-800 dark:text-gray-200 font-medium">{email.recipient}</span></p>
                      <p className="text-gray-400 font-bold mt-1">Subject: <span className="text-gray-800 dark:text-gray-200">{email.subject}</span></p>
                    </div>
                    <div className="bg-white dark:bg-gray-800 p-2.5 rounded border dark:border-gray-700 text-gray-700 dark:text-gray-300 font-mono text-[10px] leading-relaxed whitespace-pre-wrap">
                      {email.body}
                    </div>
                  </div>
                ))
              )
            ) : (
              logs.telegram.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center text-gray-400 dark:text-gray-500 py-12">
                  <MessageCircle size={36} className="mb-2 opacity-50" />
                  <p className="text-sm">No outgoing Telegram messages found.</p>
                  <p className="text-xs mt-1">Reply to a Telegram complaint to see it here.</p>
                </div>
              ) : (
                logs.telegram.map((tg) => (
                  <div key={tg.id} className="p-3 bg-gray-50 dark:bg-gray-700/40 border dark:border-gray-700 rounded-xl space-y-2 text-xs relative">
                    <span className="absolute top-3 right-3 text-[10px] text-gray-400">{new Date(tg.timestamp).toLocaleString()}</span>
                    <div>
                      <p className="text-gray-400">Chat ID: <span className="text-gray-800 dark:text-gray-200 font-mono font-medium">{tg.chat_id}</span></p>
                    </div>
                    <div className="bg-white dark:bg-gray-800 p-2.5 rounded border dark:border-gray-700 text-gray-700 dark:text-gray-300 font-mono text-[10px] leading-relaxed">
                      {tg.text}
                    </div>
                  </div>
                ))
              )
            )}
          </div>
        </div>

      </div>

      {/* Result Alert Block */}
      {result && (
        <div className={`p-4 rounded-xl border flex gap-3 ${result.error ? 'bg-red-50 border-red-200 text-red-800 dark:bg-red-950/20 dark:border-red-900 dark:text-red-300' : 'bg-green-50 border-green-200 text-green-800 dark:bg-green-950/20 dark:border-green-900 dark:text-green-300'}`}>
          {result.error ? <AlertCircle size={20} /> : <CheckCircle2 size={20} className="text-green-500" />}
          <div className="text-xs">
            <p className="font-bold">{result.source ? `${result.source} Source` : 'Simulation Result'}</p>
            <p className="mt-1 leading-relaxed">
              {result.error || result.message || `Successfully created complaint ID: ${result.id} (Category: ${result.category}, Sentiment: ${result.sentiment_label})`}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
