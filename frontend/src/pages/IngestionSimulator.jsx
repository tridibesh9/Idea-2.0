import { useState } from 'react';
import { Mail, MessageCircle, Twitter, AlertCircle, RefreshCw } from 'lucide-react';
import { simulateChannel } from '../api';

export default function IngestionSimulator() {
  const [loading, setLoading] = useState(null);
  const [result, setResult] = useState(null);

  const handleSimulate = async (channel) => {
    setLoading(channel);
    setResult(null);
    try {
      // Assuming backend has a /simulator/simulate/{channel} endpoint.
      // If it doesn't, we can just hit /complaints directly with mock payload.
      // For this demo, let's just create a raw complaint hitting the actual POST /complaints endpoint to run through the whole pipeline.
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
        },
        email: {
          channel: 'email',
          customer_email: 'john.doe@example.com',
          customer_name: 'John Doe',
          subject: 'Unauthorized transaction on my account',
          body: 'Dear Support,\nI noticed an unauthorized charge of $500 on my account yesterday. My customer ID is CUST-88392. Please investigate this immediately as I believe my account has been compromised. My SSN is 123-45-6789 just in case you need it to verify my identity.',
        }
      };

      const { createComplaint } = await import('../api');
      const res = await createComplaint(payloads[channel]);
      setResult(res.data);
    } catch (err) {
      console.error(err);
      setResult({ error: 'Failed to simulate complaint' });
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-12">
      <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-2">Multi-Channel Ingestion Demo</h2>
      <p className="text-gray-600 dark:text-gray-400 mb-8">Click a channel below to simulate an incoming complaint. It will instantly run through the AI pipeline (PII Redaction, Entity Extraction, Classification, and Grouping).</p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Twitter */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-blue-200 dark:border-blue-900 p-6 flex flex-col items-center text-center hover:shadow-md transition">
          <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/50 text-blue-500 rounded-full flex items-center justify-center mb-4">
            <Twitter size={32} />
          </div>
          <h3 className="font-bold text-gray-800 dark:text-gray-200 mb-2">Angry Tweet</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">Simulates a highly frustrated user exposing a credit card number on public social media.</p>
          <button 
            onClick={() => handleSimulate('twitter')}
            disabled={loading !== null}
            className="mt-auto px-6 py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 w-full flex justify-center items-center gap-2"
          >
            {loading === 'twitter' ? <RefreshCw size={18} className="animate-spin" /> : 'Simulate Tweet'}
          </button>
        </div>

        {/* WhatsApp */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-green-200 dark:border-green-900 p-6 flex flex-col items-center text-center hover:shadow-md transition">
          <div className="w-16 h-16 bg-green-100 dark:bg-green-900/50 text-green-500 rounded-full flex items-center justify-center mb-4">
            <MessageCircle size={32} />
          </div>
          <h3 className="font-bold text-gray-800 dark:text-gray-200 mb-2">WhatsApp Message</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">Simulates a neutral customer asking about a delayed order with an Order Number entity.</p>
          <button 
            onClick={() => handleSimulate('whatsapp')}
            disabled={loading !== null}
            className="mt-auto px-6 py-2 bg-green-500 text-white rounded-lg font-medium hover:bg-green-600 w-full flex justify-center items-center gap-2"
          >
            {loading === 'whatsapp' ? <RefreshCw size={18} className="animate-spin" /> : 'Simulate WhatsApp'}
          </button>
        </div>

        {/* Email */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-purple-200 dark:border-purple-900 p-6 flex flex-col items-center text-center hover:shadow-md transition">
          <div className="w-16 h-16 bg-purple-100 dark:bg-purple-900/50 text-purple-500 rounded-full flex items-center justify-center mb-4">
            <Mail size={32} />
          </div>
          <h3 className="font-bold text-gray-800 dark:text-gray-200 mb-2">Urgent Email</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">Simulates a formal email reporting fraud, exposing an SSN and Customer ID.</p>
          <button 
            onClick={() => handleSimulate('email')}
            disabled={loading !== null}
            className="mt-auto px-6 py-2 bg-purple-500 text-white rounded-lg font-medium hover:bg-purple-600 w-full flex justify-center items-center gap-2"
          >
            {loading === 'email' ? <RefreshCw size={18} className="animate-spin" /> : 'Simulate Email'}
          </button>
        </div>
      </div>

      {result && (
        <div className="mt-8 p-6 bg-gray-50 dark:bg-gray-800 rounded-xl border dark:border-gray-700">
          <h3 className="font-bold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
            <AlertCircle className="text-blue-500" /> Simulation Result
          </h3>
          {result.error ? (
            <p className="text-red-500">{result.error}</p>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-gray-700 dark:text-gray-300">Successfully ingested and processed complaint <strong>{result.id}</strong></p>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-white dark:bg-gray-700 p-3 rounded shadow-sm border dark:border-gray-600">
                  <span className="text-xs text-gray-500 dark:text-gray-400 block mb-1">Category</span>
                  <span className="font-medium text-gray-800 dark:text-gray-200">{result.category}</span>
                </div>
                <div className="bg-white dark:bg-gray-700 p-3 rounded shadow-sm border dark:border-gray-600">
                  <span className="text-xs text-gray-500 dark:text-gray-400 block mb-1">Sentiment</span>
                  <span className="font-medium text-gray-800 dark:text-gray-200">{result.sentiment_label}</span>
                </div>
                <div className="bg-white dark:bg-gray-700 p-3 rounded shadow-sm border dark:border-gray-600">
                  <span className="text-xs text-gray-500 dark:text-gray-400 block mb-1">Incident Group</span>
                  <span className="font-medium text-gray-800 dark:text-gray-200 font-mono text-xs">{result.incident_group_id || 'N/A'}</span>
                </div>
                <div className="bg-white dark:bg-gray-700 p-3 rounded shadow-sm border dark:border-gray-600">
                  <span className="text-xs text-gray-500 dark:text-gray-400 block mb-1">Next Best Action</span>
                  <span className="font-medium text-gray-800 dark:text-gray-200 text-xs">{result.next_best_action || 'N/A'}</span>
                </div>
              </div>

              {result.entities && result.entities.length > 0 && (
                <div>
                  <span className="text-xs text-gray-500 dark:text-gray-400 block mb-2">Extracted Entities:</span>
                  <div className="flex flex-wrap gap-2">
                    {result.entities.map((e, i) => (
                      <span key={i} className={`px-2 py-1 rounded text-xs border ${e.is_sensitive ? 'bg-red-50 border-red-200 text-red-700 dark:bg-red-900/30 dark:border-red-800 dark:text-red-400' : 'bg-gray-100 border-gray-200 text-gray-700 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-300'}`}>
                        {e.entity_type}: {e.entity_value}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
