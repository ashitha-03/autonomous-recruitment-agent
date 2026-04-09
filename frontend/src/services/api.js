// frontend/src/services/api.js
import axios from "axios";

// ✅ FIX: Use REACT_APP_API_URL (set this in Vercel env vars to your Render URL)
// For local dev: create frontend/.env.local with REACT_APP_API_URL=http://127.0.0.1:8000
const API = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://127.0.0.1:8000",
});

API.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const login = async (email, password) => {
  try {
    const res = await API.post("/auth/login", { email, password });
    return res.data;
  } catch (err) {
    if (err.response) {
      throw err.response.data;
    } else {
      throw { detail: "Server not reachable" };
    }
  }
};

// ── Job Descriptions ──────────────────────────────────────────────────────────
export const generateJD = (data) => API.post("/jd/generate", data);
export const listJDs = () => API.get("/jd/list");
export const deleteJD = (jdId) => API.delete(`/jd/${jdId}`);
export const updateJD = (jdId, data) => API.put(`/jd/${jdId}`, data);

// ── Resumes ───────────────────────────────────────────────────────────────────
export const uploadResumes = (files, jdId) => {
  const formData = new FormData();
  files.forEach((f) => formData.append("files", f));
  formData.append("jd_id", jdId);
  return API.post("/resume/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

// ── Candidates ────────────────────────────────────────────────────────────────
export const getCandidates = (jdId) =>
  API.get("/candidates/", { params: jdId ? { jd_id: jdId } : {} });

// ── Outreach ──────────────────────────────────────────────────────────────────
export const runOutreachAgent = (jdId, options = {}) =>
  API.post("/outreach/run-agent", {
    jd_id: jdId,
    send_shortlist: options.sendShortlist ?? true,
    send_rejection: options.sendRejection ?? false,
    schedule_interviews: options.scheduleInterviews ?? true,
  });

export const sendSingleEmail = (candidateId, jdId, emailType) =>
  API.post("/outreach/send-email", {
    candidate_id: candidateId,
    jd_id: jdId,
    email_type: emailType,
  });

// ── LinkedIn ──────────────────────────────────────────────────────────────────
export const scrapeLinkedIn = (keywords, jdId, maxProfiles) =>
  API.post("/linkedin/scrape", {
    search_keywords: keywords,
    jd_id: jdId,
    max_profiles: maxProfiles,
  });