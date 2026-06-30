import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL 
    ? `${import.meta.env.VITE_API_URL}/api` 
    : "/api",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("agent_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Auth ──
export const loginAgent = (email) => api.post("/auth/login", { email });
export const getAgents = () => api.get("/auth/agents");

// ── Complaints ──
export const createComplaint = (data) => api.post("/complaints", data);
export const getComplaints = (params) => api.get("/complaints", { params });
export const getComplaint = (id) => api.get(`/complaints/${id}`);
export const updateComplaint = (id, data) =>
  api.patch(`/complaints/${id}`, data);
export const getTimeline = (id) => api.get(`/complaints/${id}/timeline`);
export const addMessage = (id, data) =>
  api.post(`/complaints/${id}/messages`, data);
export const sendEmailReply = (id, data) =>
  api.post(`/complaints/${id}/send-reply`, data);
export const getSimilar = (id) => api.get(`/complaints/${id}/similar`);
export const generateResponse = (id, data) =>
  api.post(`/complaints/${id}/generate-response`, data);

// ── Analytics ──
export const getAnalyticsSummary = () => api.get("/analytics/summary");
export const getTrends = (params) => api.get("/analytics/trends", { params });
export const getRootCause = (params) =>
  api.get("/analytics/root-cause", { params });
export const getWeeklySummary = () => api.get("/analytics/weekly-summary");
export const getComplaintClusters = () => api.get("/analytics/complaint-clusters");

// ── Knowledge Base ──
export const searchKnowledgeBase = (q, category, complaintId) => api.get("/knowledge/search", { params: { q, category, complaint_id: complaintId } });
export const addKnowledgeDocument = (data) => api.post("/knowledge", data);

// ── Escalations ──
export const getEscalations = (params) => api.get("/escalations", { params });
export const getHandoverReport = (id) => api.get(`/escalations/handover/${id}`);
export const createEscalation = (data) => api.post("/escalations", data);

// ── Audit ──
export const getAuditTrail = (complaintId) => api.get(`/audit/${complaintId}`);

// ── Reports / Export ──
export const exportComplaints = (params) =>
  api.get("/reports/export", {
    params,
    responseType: params?.format === "csv" ? "blob" : undefined,
  });

// ── Simulator ──
export const simulateChannel = (channel) =>
  api.post(`/simulator/simulate/${channel}`);
export const simulateBurst = (count = 5) =>
  api.post(`/simulator/simulate/burst?count=${count}`);
export const simulateIncomingTelegram = (data) => api.post("/simulator/telegram/incoming", data);
export const simulateIncomingEmail = (data) => api.post("/simulator/email/incoming", data);
export const getSentMessages = () => api.get("/simulator/sent-messages");
export const generateMissingEmbeddings = () => api.post("/complaints/generate-missing-embeddings");

export default api;
