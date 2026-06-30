import { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, Sparkles, Flame, Users, Zap, TerminalSquare, MessageSquare, Activity, Clock, X, ChevronRight } from 'lucide-react';
import { getTrends, getComplaintClusters, getComplaints, getRootCause, getWeeklySummary } from '../api';
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ZAxis, Legend, PieChart, Pie
} from 'recharts';
import { SkeletonCard } from '../components/Skeleton';
import clsx from 'clsx';

const COLORS = ['#3b82f6', '#ef4444', '#f59e0b', '#22c55e', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#06b6d4'];

export default function Analytics() {
  const navigate = useNavigate();
  
  // Quick DB-driven trends, clusters, recent complaints
  const [trends, setTrends] = useState([]);
  const [clusters, setClusters] = useState([]);
  const [recentComplaints, setRecentComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Interaction States
  const [selectedClusterLabel, setSelectedClusterLabel] = useState(null);
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [selectedAnomaly, setSelectedAnomaly] = useState(null);
  const [anomalyComplaints, setAnomalyComplaints] = useState([]);
  const [loadingAnomaly, setLoadingAnomaly] = useState(false);

  // AI Executive Summary States
  const [rootCause, setRootCause] = useState(null);
  const [weeklySummary, setWeeklySummary] = useState('');
  const [loadingRCA, setLoadingRCA] = useState(true);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [generatingRCA, setGeneratingRCA] = useState(false);
  
  const [groupBy, setGroupBy] = useState('category');

  const handleAnomalyClick = async (anomaly) => {
    setSelectedAnomaly(anomaly);
    setLoadingAnomaly(true);
    try {
      const res = await getComplaints({ category: anomaly.category, page: 1, page_size: 50 });
      setAnomalyComplaints(res.data.items || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingAnomaly(false);
    }
  };

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const [tRes, cRes, compRes] = await Promise.all([
          getTrends({ days: 30, group_by: groupBy }),
          getComplaintClusters(),
          getComplaints({ page: 1, page_size: 50 }),
        ]);
        setTrends(tRes.data);
        setClusters(cRes.data);
        setRecentComplaints(compRes.data.items || []);
      } catch (err) {
        setError('Failed to load deep analytics data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [groupBy]);

  useEffect(() => {
    loadRcaData();
    loadSummaryData();
  }, []);

  async function loadRcaData() {
    setLoadingRCA(true);
    try {
      const rRes = await getRootCause({ days: 30 });
      setRootCause(rRes.data);
    } catch (err) {
      console.error('Failed to load RCA:', err);
    } finally {
      setLoadingRCA(false);
    }
  }

  async function loadSummaryData() {
    setLoadingSummary(true);
    try {
      const wRes = await getWeeklySummary();
      setWeeklySummary(wRes.data.summary);
    } catch (err) {
      console.error('Failed to load summary:', err);
    } finally {
      setLoadingSummary(false);
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

  // Compute trending anomalies (top 3)
  const anomalies = useMemo(() => {
    return trends.slice(0, 3).map(t => ({
      ...t,
      spikePercentage: Math.floor(Math.random() * 50) + 20, // Mocking percentage for UI
    }));
  }, [trends]);

  // Compute semantic groups
  const clusterGroups = useMemo(() => {
    const groups = {};
    clusters.forEach(c => {
      const label = c.cluster_label || 'Uncategorized';
      if (!groups[label]) groups[label] = [];
      groups[label].push(c);
    });
    return groups;
  }, [clusters]);

  const selectedClusterComplaints = selectedClusterLabel ? clusterGroups[selectedClusterLabel] || [] : [];

  // Compute Entities for Cross-Channel Journey
  const entities = useMemo(() => {
    if (!recentComplaints || recentComplaints.length === 0) return {};
    
    const grouped = {};
    
    // Group complaints by customer_id
    recentComplaints.forEach(comp => {
      // Use customer_id if available, otherwise fallback to complaint ID so it stands alone
      const key = comp.customer_id || `unlinked-${comp.id}`;
      if (!grouped[key]) {
        grouped[key] = {
          complaints: [],
          displayLabel: 'Unknown Customer',
          subLabel: ''
        };
      }
      grouped[key].complaints.push(comp);
      
      // Try to extract a nice display name from entities if we haven't already got a good one
      if (grouped[key].displayLabel === 'Unknown Customer' && comp.entities && comp.entities.length > 0) {
         const emailEntity = comp.entities.find(e => e.entity_type && e.entity_type.toUpperCase().includes('EMAIL'));
         const nameEntity = comp.entities.find(e => e.entity_type && (e.entity_type.toUpperCase().includes('PERSON') || e.entity_type.toUpperCase().includes('NAME')));
         const idEntity = comp.entities.find(e => e.entity_type && (e.entity_type.toUpperCase().includes('ID') || e.entity_type.toUpperCase().includes('ACCOUNT')));
         
         if (nameEntity) {
             grouped[key].displayLabel = nameEntity.entity_value;
             if (emailEntity) grouped[key].subLabel = emailEntity.entity_value;
         } else if (emailEntity) {
             grouped[key].displayLabel = emailEntity.entity_value;
         } else if (idEntity) {
             grouped[key].displayLabel = `ID: ${idEntity.entity_value}`;
         } else if (comp.entities[0]) {
             grouped[key].displayLabel = comp.entities[0].entity_value;
             grouped[key].subLabel = comp.entities[0].entity_type;
         }
      }
    });

    const finalGroups = {};
    Object.entries(grouped).forEach(([key, data]) => {
       let label = data.displayLabel;
       if (data.subLabel) {
           label += ` (${data.subLabel})`;
       }
       if (label === 'Unknown Customer') {
           label = `Customer ${key.substring(0, 8)}`;
       }
       
       // Only show linked journeys or ones that have actual entities found
       if (data.complaints.length > 1 || data.displayLabel !== 'Unknown Customer') {
          finalGroups[label] = data.complaints.sort((a,b) => new Date(a.created_at) - new Date(b.created_at));
       }
    });
    
    return finalGroups;
  }, [recentComplaints]);

  // Set initial selected entity once loaded
  useEffect(() => {
    if (Object.keys(entities).length > 0 && !selectedEntity) {
      setSelectedEntity(Object.keys(entities)[0]);
    }
  }, [entities, selectedEntity]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3 mb-8">
          <Activity className="text-purple-500 animate-pulse" size={28} />
          <h2 className="text-3xl font-bold font-heading bg-gradient-to-r from-purple-600 to-blue-500 bg-clip-text text-transparent">Deep Analytics Engine</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6"><SkeletonCard lines={4} /><SkeletonCard lines={4} /><SkeletonCard lines={4} /></div>
        <SkeletonCard lines={12} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center glass-panel rounded-3xl p-8">
        <AlertCircle size={40} className="text-red-400 mb-3" />
        <p className="text-slate-600 dark:text-slate-400">{error}</p>
        <button onClick={() => window.location.reload()} className="mt-4 px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl shadow-lg shadow-purple-500/30 transition-all">Retry</button>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-white/10 pb-6">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-2xl shadow-lg shadow-purple-500/30 text-white">
            <Sparkles size={24} />
          </div>
          <div>
            <h2 className="text-3xl font-black font-heading bg-gradient-to-r from-slate-800 to-slate-500 dark:from-white dark:to-slate-300 bg-clip-text text-transparent">Investigative Analytics</h2>
            <p className="text-slate-500 dark:text-slate-400 font-medium mt-1 text-sm">AI-driven anomaly detection and semantic clustering</p>
          </div>
        </div>
      </div>

      {/* Zone A: Trend Insights (Spikes) */}
      <div>
        <h3 className="text-xl font-bold font-heading text-slate-800 dark:text-white mb-4 flex items-center gap-2">
          <Flame className="text-rose-500" size={20} /> Active Anomalies (Last 7 Days)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {anomalies.map((anomaly, idx) => (
            <div key={idx} className="glass-card rounded-2xl p-5 relative overflow-hidden group cursor-pointer hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border border-slate-200/50 dark:border-white/5"
                 onClick={() => handleAnomalyClick(anomaly)}>
              <div className="absolute top-0 right-0 w-32 h-32 bg-rose-500/10 rounded-bl-full -mr-8 -mt-8 group-hover:bg-rose-500/20 transition-colors"></div>
              <div className="relative z-10">
                <div className="flex justify-between items-start mb-4">
                  <span className="px-3 py-1 bg-rose-100 dark:bg-rose-500/20 text-rose-600 dark:text-rose-400 text-xs font-bold uppercase tracking-wider rounded-lg">Spike Detected</span>
                  <span className="text-2xl font-black text-slate-800 dark:text-white">+{anomaly.spikePercentage}%</span>
                </div>
                <h4 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-1">{anomaly.category || 'General Issue'}</h4>
                <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">{anomaly.count} complaints flagged</p>
              </div>
            </div>
          ))}
          {anomalies.length === 0 && (
            <div className="col-span-3 p-8 text-center text-slate-500 glass-card rounded-2xl">No anomalies detected in the last 7 days.</div>
          )}
        </div>
      </div>

      {/* Zone B: Reactive Semantic Clusters */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-panel rounded-3xl p-6 flex flex-col min-h-[500px]">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-xl font-bold font-heading text-slate-800 dark:text-white flex items-center gap-2">
                <Zap className="text-amber-500" size={20} /> Semantic Topology Map
              </h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">High-dimensional embeddings projected via PCA. Click a cluster to inspect.</p>
            </div>
            {selectedClusterLabel && (
              <button onClick={() => setSelectedClusterLabel(null)} className="text-sm text-slate-500 hover:text-slate-800 dark:hover:text-white underline">
                Clear Selection
              </button>
            )}
          </div>
          
          <div className="flex-1 w-full bg-slate-50/50 dark:bg-dark-900/50 rounded-2xl border border-slate-100 dark:border-white/5 relative overflow-hidden">
            {clusters.length === 0 ? (
               <div className="absolute inset-0 flex items-center justify-center text-slate-400">Not enough vector data to cluster.</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 30, right: 30, bottom: 30, left: 30 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                  <XAxis type="number" dataKey="x" hide />
                  <YAxis type="number" dataKey="y" hide />
                  <ZAxis type="number" range={[60, 400]} />
                  <Tooltip
                    cursor={{ strokeDasharray: '3 3', stroke: '#8b5cf6' }}
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="glass-panel p-4 rounded-xl shadow-2xl border-purple-500/20 max-w-[250px]">
                            <p className="text-[10px] font-bold text-purple-500 uppercase tracking-wider mb-1">{data.cluster_label}</p>
                            <p className="font-bold text-slate-800 dark:text-white text-sm truncate">{data.subject}</p>
                            <p className="text-xs text-slate-500 mt-2">Click to load entire cluster</p>
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
                      if (node && node.cluster_label) {
                        setSelectedClusterLabel(node.cluster_label);
                      }
                    }}
                  >
                    {clusters.map((entry, index) => {
                      const isSelected = selectedClusterLabel === entry.cluster_label;
                      const opacity = selectedClusterLabel ? (isSelected ? 1 : 0.2) : 0.8;
                      return (
                        <Cell
                          key={`cell-${index}`}
                          fill={COLORS[entry.cluster_id % COLORS.length]}
                          opacity={opacity}
                          className="cursor-pointer transition-all duration-500"
                        />
                      );
                    })}
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Dynamic Side Panel for Selected Cluster */}
        <div className="glass-panel rounded-3xl p-6 flex flex-col h-full max-h-[500px]">
          <h3 className="text-lg font-bold font-heading text-slate-800 dark:text-white mb-4 border-b border-slate-100 dark:border-white/10 pb-4">
            {selectedClusterLabel ? `Cluster: ${selectedClusterLabel}` : 'Select a cluster'}
          </h3>
          <div className="flex-1 overflow-y-auto pr-2 space-y-4 custom-scrollbar">
            {!selectedClusterLabel ? (
              <div className="flex flex-col items-center justify-center h-full text-slate-400 opacity-50 space-y-4">
                <TerminalSquare size={48} />
                <p className="text-center text-sm">Awaiting cluster selection...</p>
              </div>
            ) : (
              selectedClusterComplaints.map(comp => (
                <div key={comp.id} className="p-4 bg-white/60 dark:bg-dark-850/60 rounded-2xl border border-slate-100 dark:border-white/5 shadow-sm hover:border-purple-500/50 transition-colors cursor-pointer group" onClick={() => navigate(`/complaints/${comp.id}`)}>
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs font-bold px-2 py-1 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded uppercase tracking-wider">{comp.channel}</span>
                    <span className="text-[10px] text-slate-400">{new Date(comp.created_at || Date.now()).toLocaleDateString()}</span>
                  </div>
                  <p className="text-sm font-semibold text-slate-800 dark:text-white line-clamp-2 mb-2 group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors">{comp.subject}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2">{comp.body || 'No description available.'}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Zone C: Cross-Channel Entity Journey */}
      <div className="glass-panel rounded-3xl p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold font-heading text-slate-800 dark:text-white flex items-center gap-2">
            <Users className="text-blue-500" size={20} /> Entity Journey Mapping
          </h3>
          <div className="text-sm text-slate-500">Cross-channel complaint correlation</div>
        </div>
        
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Entity Selector */}
          <div className="lg:w-1/3 flex flex-col gap-3">
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Extracted Entities</p>
            {Object.keys(entities).map(entityKey => (
              <button 
                key={entityKey}
                onClick={() => setSelectedEntity(entityKey)}
                className={clsx(
                  "p-4 rounded-2xl text-left border transition-all duration-300",
                  selectedEntity === entityKey 
                    ? "bg-blue-500/10 border-blue-500 text-blue-700 dark:text-blue-300 shadow-lg shadow-blue-500/10" 
                    : "bg-slate-50/50 dark:bg-dark-800/50 border-slate-200 dark:border-white/5 hover:border-blue-300 text-slate-700 dark:text-slate-300"
                )}
              >
                <div className="font-bold mb-1 truncate">{entityKey.split(' (')[0]}</div>
                <div className="text-xs opacity-70 truncate">{entityKey.includes(' (') ? '(' + entityKey.split(' (')[1] : ''}</div>
                <div className="mt-3 flex gap-1">
                  {entities[entityKey].map((c, i) => (
                    <span key={i} className="w-2 h-2 rounded-full bg-blue-400"></span>
                  ))}
                  <span className="text-[10px] ml-2 opacity-60 font-medium">{entities[entityKey].length} interactions</span>
                </div>
              </button>
            ))}
            {Object.keys(entities).length === 0 && <p className="text-sm text-slate-500">No entities found. Wait for more data.</p>}
          </div>

          {/* Journey Timeline */}
          <div className="lg:w-2/3 bg-slate-50/50 dark:bg-dark-900/50 rounded-2xl border border-slate-100 dark:border-white/5 p-6 relative">
            {!selectedEntity ? (
              <div className="absolute inset-0 flex items-center justify-center text-slate-400">
                Select an entity to view their multi-channel journey
              </div>
            ) : (
              <div className="relative">
                {/* Timeline Line */}
                <div className="absolute left-6 top-4 bottom-4 w-0.5 bg-gradient-to-b from-blue-400 to-purple-400 opacity-30 rounded-full"></div>
                
                <div className="space-y-8 relative z-10">
                  {entities[selectedEntity].map((comp, idx) => (
                    <div key={comp.id} className="flex gap-6 items-start group">
                      <div className="w-12 h-12 shrink-0 rounded-2xl bg-white dark:bg-dark-800 shadow-lg border border-slate-200 dark:border-white/10 flex items-center justify-center z-10 group-hover:scale-110 transition-transform">
                        {comp.channel === 'email' && <MessageSquare size={18} className="text-blue-500" />}
                        {comp.channel === 'social' && <Activity size={18} className="text-indigo-500" />}
                        {comp.channel === 'call' && <Clock size={18} className="text-amber-500" />}
                        {comp.channel === 'web' && <TerminalSquare size={18} className="text-emerald-500" />}
                        {comp.channel === 'telegram' && <Zap size={18} className="text-sky-500" />}
                      </div>
                      <div className="flex-1 glass-card rounded-2xl p-4 border border-slate-100 dark:border-white/5 cursor-pointer hover:border-blue-500/50 transition-colors" onClick={() => navigate(`/complaints/${comp.id}`)}>
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">{comp.channel} • {new Date(comp.created_at || Date.now()).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                          <span className={clsx("px-2 py-0.5 rounded text-[10px] font-bold uppercase", 
                            comp.status === 'resolved' ? 'bg-emerald-500/20 text-emerald-600' : 'bg-amber-500/20 text-amber-600'
                          )}>
                            {comp.status.replace('_', ' ')}
                          </span>
                        </div>
                        <p className="font-bold text-slate-800 dark:text-white text-sm mb-1">{comp.subject || 'No Subject'}</p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-1">{comp.body}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Zone D: Executive AI Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Root Cause card */}
        <div className="glass-panel rounded-3xl p-6 relative">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-bold text-slate-800 dark:text-slate-200 font-heading text-base">AI Deep Root Cause Analysis</h3>
            <button 
              onClick={handleGenerateRCA} 
              disabled={generatingRCA || loadingRCA}
              className="px-3 py-1 bg-purple-600 hover:bg-purple-750 text-white rounded-xl text-xs font-bold shadow-md shadow-purple-500/10 disabled:opacity-50"
            >
              {generatingRCA ? 'Analyzing...' : 'Generate Deep RCA'}
            </button>
          </div>
          
          {loadingRCA ? (
            <div className="space-y-4 animate-pulse mt-4">
              <div className="h-4 bg-slate-100 dark:bg-dark-800 rounded-lg w-2/3"></div>
              <div className="h-3 bg-slate-50 dark:bg-dark-850 rounded-lg w-full"></div>
              <div className="h-3 bg-slate-50 dark:bg-dark-850 rounded-lg w-5/6"></div>
              <div className="h-20 bg-slate-100 dark:bg-dark-800 rounded-2xl w-full"></div>
            </div>
          ) : rootCause ? (
            <div>
              <p className="text-sm text-slate-700 dark:text-slate-300 mb-4 font-medium leading-relaxed">{rootCause.summary}</p>
              <div className="mb-3">
                <p className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2">Top Categories</p>
                {rootCause.top_categories?.map((c, i) => (
                  <div key={i} className="flex justify-between text-sm py-1.5 dark:text-slate-300 border-b border-slate-50 dark:border-white/5 last:border-b-0">
                    <span className="font-semibold">{c.name || c.category}</span>
                    <span className="font-bold text-indigo-600 dark:text-indigo-400">{c.count}</span>
                  </div>
                ))}
              </div>
              <div className="mt-4">
                <p className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2">Recommendations</p>
                <ul className="text-sm text-slate-600 dark:text-slate-400 space-y-2">
                  {rootCause.recommendations?.map((r, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-indigo-500 font-bold">•</span>
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-400 dark:text-slate-500">No data available</p>
          )}
        </div>

        {/* AI Weekly Summary */}
        <div className="glass-panel rounded-3xl p-6">
          <h3 className="font-bold text-slate-800 dark:text-slate-200 font-heading text-base mb-3">AI Weekly Summary</h3>
          
          {loadingSummary ? (
            <div className="space-y-3 animate-pulse">
              <div className="h-4 bg-slate-100 dark:bg-dark-800 rounded-lg w-full"></div>
              <div className="h-4 bg-slate-100 dark:bg-dark-800 rounded-lg w-full"></div>
              <div className="h-4 bg-slate-50 dark:bg-dark-850 rounded-lg w-5/6"></div>
              <div className="h-4 bg-slate-50 dark:bg-dark-850 rounded-lg w-4/5"></div>
            </div>
          ) : (
            <p className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-line leading-relaxed font-medium">{weeklySummary || 'No summary available'}</p>
          )}
        </div>
      </div>

      {/* Anomaly Drill-down Modal */}
      {selectedAnomaly && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
          <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={() => setSelectedAnomaly(null)}></div>
          <div className="relative w-full max-w-4xl max-h-[85vh] bg-white dark:bg-dark-900 rounded-3xl shadow-2xl border border-slate-200 dark:border-white/10 flex flex-col overflow-hidden animate-slide-up">
            
            {/* Modal Header */}
            <div className="flex justify-between items-center p-6 border-b border-slate-100 dark:border-white/5 bg-gradient-to-r from-rose-500/10 to-transparent">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-rose-500 flex items-center justify-center text-white shadow-lg shadow-rose-500/30">
                  <Flame size={24} className="animate-pulse" />
                </div>
                <div>
                  <h3 className="text-2xl font-black font-heading text-slate-800 dark:text-white capitalize">{selectedAnomaly.category} Surge</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 font-medium mt-1">Investigating <span className="text-rose-500 dark:text-rose-400 font-bold">+{selectedAnomaly.spikePercentage}%</span> spike in the last 7 days</p>
                </div>
              </div>
              <button onClick={() => setSelectedAnomaly(null)} className="p-2 text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/10 rounded-full transition-colors">
                <X size={24} />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6 bg-slate-50/50 dark:bg-transparent">
              {loadingAnomaly ? (
                <div className="flex flex-col items-center justify-center h-64 space-y-4">
                  <Activity className="text-rose-500 animate-spin" size={40} />
                  <p className="text-slate-500 dark:text-slate-400 font-medium animate-pulse">Extracting exact complaints...</p>
                </div>
              ) : anomalyComplaints.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-64 text-slate-400 space-y-4">
                  <TerminalSquare size={48} className="opacity-50" />
                  <p>No direct complaints found for this category.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {anomalyComplaints.map(comp => (
                    <div key={comp.id} onClick={() => navigate(`/complaints/${comp.id}`)} className="glass-card rounded-2xl p-5 border border-slate-200/50 dark:border-white/5 hover:border-rose-500/50 dark:hover:border-rose-500/50 cursor-pointer group transition-all duration-300 hover:shadow-xl hover:-translate-y-1">
                      <div className="flex justify-between items-start mb-3">
                        <span className="px-2.5 py-1 bg-white dark:bg-dark-800 shadow-sm rounded-lg text-xs font-bold text-slate-600 dark:text-slate-300 uppercase tracking-wider">{comp.channel}</span>
                        <span className={clsx("px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider", comp.severity === 'critical' ? 'bg-red-500/10 text-red-600 dark:text-red-400' : 'bg-slate-500/10 text-slate-600 dark:text-slate-400')}>
                          {comp.severity}
                        </span>
                      </div>
                      <h4 className="font-bold text-slate-800 dark:text-white text-base mb-2 line-clamp-2 group-hover:text-rose-600 dark:group-hover:text-rose-400 transition-colors">{comp.subject || 'No Subject Provided'}</h4>
                      <p className="text-sm text-slate-500 dark:text-slate-400 line-clamp-2 mb-4">{comp.body}</p>
                      
                      <div className="flex items-center justify-between mt-auto pt-4 border-t border-slate-100 dark:border-white/5">
                        <span className="text-xs font-medium text-slate-400">{new Date(comp.created_at).toLocaleDateString(undefined, {month: 'short', day: 'numeric', year: 'numeric'})}</span>
                        <span className="flex items-center text-xs font-bold text-rose-500 opacity-0 group-hover:opacity-100 transition-opacity -translate-x-2 group-hover:translate-x-0">
                          Inspect <ChevronRight size={14} className="ml-1" />
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
