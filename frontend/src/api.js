import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

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

// ── Escalations ──
export const getEscalations = (params) => api.get("/escalations", { params });

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

export default api;
