// frontend/src/App.jsx
import { useState, useEffect, useRef } from "react";
import Login from "./pages/Login";
import { generateJD, listJDs, uploadResumes, getCandidates, scrapeLinkedIn, runOutreachAgent } from "./services/api";
import axios from "axios";

const API = axios.create({ baseURL: process.env.REACT_APP_BACKEND_URL });

const TABS = ["Job Descriptions", "Upload Resumes", "Candidates", "LinkedIn"];

const badge = (score) => {
  if (!score && score !== 0) return null;
  const s = parseFloat(score);
  const color = s >= 70 ? "#16a34a" : s >= 50 ? "#d97706" : "#dc2626";
  return <span style={{ background: color, color: "#fff", borderRadius: 4, padding: "2px 8px", fontSize: 12, fontWeight: 600 }}>{s.toFixed(0)}%</span>;
};

const statusChip = (status) => {
  const colors = {
    "Shortlisted": { bg: "#dcfce7", color: "#16a34a" },
    "Email Sent": { bg: "#dcfce7", color: "#16a34a" },
    "Interview Scheduled": { bg: "#dbeafe", color: "#1d4ed8" },
    "Applied": { bg: "#f1f5f9", color: "#475569" },
    "Rejected": { bg: "#fee2e2", color: "#dc2626" },
    "Maybe": { bg: "#fef9c3", color: "#ca8a04" },
    "Duplicate": { bg: "#f3e8ff", color: "#7c3aed" },
  };
  const c = colors[status] || colors["Applied"];
  return <span style={{ fontSize: 11, padding: "2px 8px", borderRadius: 4, fontWeight: 600, background: c.bg, color: c.color }}>{status}</span>;
};

const skillTag = (skill, matched) => (
  <span key={skill} style={{ display: "inline-block", fontSize: 11, padding: "2px 8px", borderRadius: 12, margin: "2px", fontWeight: 500, background: matched ? "#dcfce7" : "#fee2e2", color: matched ? "#16a34a" : "#dc2626", border: `1px solid ${matched ? "#86efac" : "#fca5a5"}` }}>
    {matched ? "✓" : "✗"} {skill}
  </span>
);

// ── JD Card Component ─────────────────────────────────────────────────────────
const JDCard = ({ jd, onDelete, onEdit, onUploadResumes }) => {
  const [expanded, setExpanded] = useState(false);

  const downloadPDF = () => {
    const link = document.createElement("a");
    link.href = `http://localhost:8000/jd/${jd.jd_id}/pdf`;
    link.download = `${jd.role_title.replace(/ /g, "_")}_JD.pdf`;
    link.click();
  };

  return (
    <div style={{ background: "#fff", borderRadius: 12, marginBottom: 20, boxShadow: "0 2px 8px rgba(0,0,0,.08)", overflow: "hidden", border: "1px solid #e2e8f0" }}>
      <div style={{ background: "linear-gradient(135deg, #0f1e3c 0%, #1a3a6e 100%)", padding: "24px 28px", color: "#fff" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 24, fontWeight: 700, fontFamily: "Georgia, serif", marginBottom: 4 }}>{jd.role_title}</div>
            <div style={{ fontSize: 14, opacity: 0.8, marginBottom: 16 }}>
              {jd.company_name && <span>{jd.company_name} • </span>}{jd.department} Department
            </div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {[
                { icon: "📍", text: jd.location || "Location TBD" },
                { icon: "💼", text: jd.employment_type || "Full-time" },
                { icon: "🏠", text: jd.work_mode || "Hybrid" },
                { icon: "⏱️", text: `${jd.experience_years || 0}+ years` },
                { icon: "💰", text: jd.salary_range || "Competitive" },
              ].map((item, i) => (
                <span key={i} style={{ background: "rgba(255,255,255,0.12)", borderRadius: 20, padding: "5px 12px", fontSize: 12, display: "flex", alignItems: "center", gap: 5 }}>
                  {item.icon} {item.text}
                </span>
              ))}
            </div>
          </div>
          <div style={{ display: "flex", gap: 8, marginLeft: 16 }}>
            <button onClick={downloadPDF} style={{ background: "rgba(240,192,64,0.2)", border: "1px solid rgba(240,192,64,0.4)", color: "#f0c040", borderRadius: 8, padding: "8px 14px", cursor: "pointer", fontSize: 12, fontWeight: 600 }}>📄 PDF</button>
            <button onClick={() => onEdit(jd)} style={{ background: "rgba(59,130,246,0.2)", border: "1px solid rgba(59,130,246,0.4)", color: "#93c5fd", borderRadius: 8, padding: "8px 14px", cursor: "pointer", fontSize: 12 }}>✏️ Edit</button>
            <button onClick={() => onDelete(jd.jd_id)} style={{ background: "rgba(220,38,38,0.2)", border: "1px solid rgba(220,38,38,0.4)", color: "#fca5a5", borderRadius: 8, padding: "8px 14px", cursor: "pointer", fontSize: 12 }}>🗑️</button>
          </div>
        </div>
      </div>

      {jd.summary && (
        <div style={{ padding: "20px 28px", background: "#fafbfc", borderBottom: "1px solid #f1f5f9" }}>
          <div style={{ fontSize: 13, color: "#374151", lineHeight: 1.8 }}>{jd.summary}</div>
        </div>
      )}

      <div style={{ padding: "14px 28px", borderBottom: "1px solid #f1f5f9", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {(jd.required_skills || "").split(", ").slice(0, 5).map((s, i) => s && (
            <span key={i} style={{ background: "#f0f4ff", color: "#3b82f6", fontSize: 11, padding: "3px 10px", borderRadius: 20, fontWeight: 500 }}>{s}</span>
          ))}
          {(jd.required_skills || "").split(", ").length > 5 && (
            <span style={{ background: "#f1f5f9", color: "#64748b", fontSize: 11, padding: "3px 10px", borderRadius: 20 }}>+{(jd.required_skills || "").split(", ").length - 5} more</span>
          )}
        </div>
        <button onClick={() => setExpanded(!expanded)} style={{ background: "none", border: "none", color: "#3b82f6", fontSize: 13, cursor: "pointer", fontWeight: 600 }}>
          {expanded ? "Hide ▲" : "View Full JD ▼"}
        </button>
      </div>

      {expanded && (
        <div style={{ padding: "24px 28px" }}>
          {jd.responsibilities && (
            <div style={{ marginBottom: 24 }}>
              <div style={{ fontWeight: 700, fontSize: 15, color: "#0f1e3c", marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ background: "#f0c040", width: 4, height: 18, borderRadius: 2, display: "inline-block" }}></span>
                Key Responsibilities
              </div>
              {jd.responsibilities.split(" | ").filter(r => r.trim()).map((r, i) => (
                <div key={i} style={{ display: "flex", gap: 10, marginBottom: 8, fontSize: 13, color: "#374151", lineHeight: 1.6 }}>
                  <span style={{ color: "#0f1e3c", fontWeight: 700, flexShrink: 0 }}>▸</span>
                  <span>{r.trim()}</span>
                </div>
              ))}
            </div>
          )}

          {jd.required_skills && (
            <div style={{ marginBottom: 24 }}>
              <div style={{ fontWeight: 700, fontSize: 15, color: "#0f1e3c", marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ background: "#f0c040", width: 4, height: 18, borderRadius: 2, display: "inline-block" }}></span>
                Required Skills
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {jd.required_skills.split(", ").filter(s => s.trim()).map((s, i) => (
                  <span key={i} style={{ background: "#dcfce7", color: "#15803d", fontSize: 13, padding: "6px 16px", borderRadius: 20, fontWeight: 500, border: "1px solid #86efac" }}>✓ {s}</span>
                ))}
              </div>
            </div>
          )}

          {jd.preferred_skills && (
            <div style={{ marginBottom: 24 }}>
              <div style={{ fontWeight: 700, fontSize: 15, color: "#0f1e3c", marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ background: "#e2e8f0", width: 4, height: 18, borderRadius: 2, display: "inline-block" }}></span>
                Nice to Have
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {jd.preferred_skills.split(", ").filter(s => s.trim()).map((s, i) => (
                  <span key={i} style={{ background: "#f0f4ff", color: "#3b82f6", fontSize: 13, padding: "6px 16px", borderRadius: 20, fontWeight: 500, border: "1px solid #bfdbfe" }}>+ {s}</span>
                ))}
              </div>
            </div>
          )}

          <div style={{ background: "#f8fafc", borderRadius: 10, padding: "16px 20px", display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 8 }}>
            <div style={{ fontSize: 12, color: "#64748b" }}>
              📅 Posted: {jd.created_at ? new Date(jd.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" }) : "Recently"}
            </div>
            <button onClick={() => onUploadResumes(jd.jd_id)} style={{ background: "#0f1e3c", color: "#fff", border: "none", borderRadius: 8, padding: "10px 20px", fontWeight: 600, cursor: "pointer", fontSize: 13 }}>
              Upload Resumes →
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// ── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [user, setUser] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("user");
    const token = localStorage.getItem("token");
    if (stored && token) setUser(JSON.parse(stored));
    setAuthChecked(true);
  }, []);

  const [tab, setTab] = useState(0);
  const [jds, setJDs] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState({ text: "", type: "" });
  const [expandedCandidate, setExpandedCandidate] = useState(null);
  const [filterStatus, setFilterStatus] = useState("All");
  const [dragOver, setDragOver] = useState(false);
  const [linkedInKeywords, setLinkedInKeywords] = useState("");
  const [linkedInJdId, setLinkedInJdId] = useState("");
  const [linkedInMax, setLinkedInMax] = useState(10);
  const [linkedInResults, setLinkedInResults] = useState([]);
  const [resumeFiles, setResumeFiles] = useState([]);
  const [selectedJdId, setSelectedJdId] = useState("");
  const [uploadResults, setUploadResults] = useState([]);
  const fileInputRef = useRef(null);
  const [editingJd, setEditingJd] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [selectedCandidateJdId, setSelectedCandidateJdId] = useState("");
  const [outreachLoading, setOutreachLoading] = useState(false);
  const [outreachResult, setOutreachResult] = useState(null);

  const [jdForm, setJdForm] = useState({
    role_title: "", department: "", experience_years: 3,
    skills_hint: "", work_mode: "Hybrid",
    location: "", employment_type: "Full-time", salary_range: ""
  });

  useEffect(() => { if (user) listJDs().then(r => setJDs(r.data)).catch(() => {}); }, [user, tab]);

  const notify = (text, type = "success") => { setMsg({ text, type }); setTimeout(() => setMsg({ text: "", type: "" }), 4000); };

  const handleLogin = (userData) => setUser(userData);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
    setTab(0);
  };

  const handleGenerateJD = async () => {
    if (!jdForm.role_title) return notify("Enter a role title first!", "error");
    setLoading(true);
    try {
      await generateJD({ ...jdForm, experience_years: Number(jdForm.experience_years) });
      const r = await listJDs();
      setJDs(r.data);
      notify("✅ Job Description generated and saved!");
      setJdForm({ role_title: "", department: "", experience_years: 3, skills_hint: "", work_mode: "Hybrid", location: "", employment_type: "Full-time", salary_range: "" });
    } catch (e) { notify("❌ " + (e.response?.data?.detail || e.message), "error"); }
    setLoading(false);
  };

  const handleDeleteJD = async (jdId) => {
    if (!window.confirm("Delete this Job Description?")) return;
    try {
      await API.delete(`/jd/${jdId}`);
      const r = await listJDs();
      setJDs(r.data);
      notify("✅ Job Description deleted!");
    } catch (e) { notify("❌ Failed to delete", "error"); }
  };

  const handleEditJD = (jd) => {
    setEditingJd(jd);
    setEditForm({
      role_title: jd.role_title || "",
      department: jd.department || "",
      location: jd.location || "",
      employment_type: jd.employment_type || "Full-time",
      work_mode: jd.work_mode || "Hybrid",
      experience_years: jd.experience_years || 3,
      salary_range: jd.salary_range || "",
      summary: jd.summary || "",
      required_skills: jd.required_skills || "",
      preferred_skills: jd.preferred_skills || "",
    });
  };

  const handleSaveEdit = async () => {
    try {
      await API.put(`/jd/${editingJd.jd_id}`, editForm);
      const r = await listJDs();
      setJDs(r.data);
      setEditingJd(null);
      notify("✅ Job Description updated!");
    } catch (e) { notify("❌ Failed to update", "error"); }
  };

  const handleLoadCandidates = async (jdId) => {
    if (!jdId) { setCandidates([]); return; }
    setLoading(true);
    setExpandedCandidate(null);
    setOutreachResult(null);
    try {
      const r = await getCandidates(jdId);
      setCandidates(r.data);
    } catch (e) { notify("❌ " + e.message, "error"); }
    setLoading(false);
  };

  const handleDeleteCandidate = async (candidateId) => {
  if (!window.confirm("Delete this candidate?")) return;

  try {
    await API.delete(`/candidates/${candidateId}`);
    setCandidates(prev => prev.filter(c => c.candidate_id !== candidateId));
    notify("✅ Candidate deleted!");
  } catch (e) {
    notify("❌ Failed to delete candidate", "error");
  }
};

  const handleRunOutreach = async () => {
    if (!selectedCandidateJdId) return notify("Select a JD first!", "error");
    const shortlisted = candidates.filter(c => c.status === "Shortlisted");
    if (shortlisted.length === 0) return notify("No shortlisted candidates to contact!", "error");
    if (!window.confirm(`Send emails + schedule interviews for ${shortlisted.length} shortlisted candidate(s)?`)) return;
    setOutreachLoading(true);
    setOutreachResult(null);
    try {
      const r = await runOutreachAgent(selectedCandidateJdId, {
        sendShortlist: true,
        sendRejection: false,
        scheduleInterviews: true,
      });
      setOutreachResult(r.data);
      notify("✅ Outreach agent completed!");
      // Refresh candidates to show updated status
      await handleLoadCandidates(selectedCandidateJdId);
    } catch (e) { notify("❌ " + (e.response?.data?.detail || e.message), "error"); }
    setOutreachLoading(false);
  };

  const handleFiles = (files) => {
    const allowed = [".pdf", ".docx", ".doc", ".jpg", ".jpeg", ".png"];
    const valid = Array.from(files).filter(f => allowed.some(ext => f.name.toLowerCase().endsWith(ext)));
    const invalid = Array.from(files).filter(f => !allowed.some(ext => f.name.toLowerCase().endsWith(ext)));
    if (invalid.length > 0) notify(`❌ ${invalid.length} file(s) rejected!`, "error");
    if (valid.length > 0) setResumeFiles(valid);
  };
const handleUpload = async () => {
  if (resumeFiles.length === 0) return notify("Select at least one file!", "error");
  if (!selectedJdId) return notify("Select a Job Description first!", "error");

  setLoading(true);
  setUploadResults([]);

  try {
    const r = await uploadResumes(resumeFiles, selectedJdId);
    setUploadResults(r.data.results || []);
    notify(`✅ ${r.data.processed} resume(s) processed!`);

    // ✅ ADD THIS (AUTO REFRESH)
    await handleLoadCandidates(selectedJdId);

  } catch (e) {
    notify("❌ " + (e.response?.data?.detail || e.message), "error");
  }

  setLoading(false);



};



  const s = {
    wrap: { fontFamily: "system-ui, sans-serif", minHeight: "100vh", background: "#f1f5f9" },
    header: { background: "#0f1e3c", color: "#fff", padding: "0 32px", height: 56, display: "flex", alignItems: "center", justifyContent: "space-between" },
    nav: { display: "flex", gap: 2, padding: "10px 32px", background: "#fff", borderBottom: "1px solid #e2e8f0" },
    navBtn: (active) => ({ padding: "7px 16px", borderRadius: 6, border: "none", cursor: "pointer", fontWeight: 500, background: active ? "#0f1e3c" : "transparent", color: active ? "#fff" : "#64748b", fontSize: 13 }),
    body: { padding: "28px 32px", maxWidth: 1000, margin: "0 auto" },
    card: { background: "#fff", borderRadius: 10, padding: 24, boxShadow: "0 1px 4px rgba(0,0,0,.07)", marginBottom: 20 },
    cardTitle: { marginTop: 0, color: "#0f1e3c", fontSize: 18, fontFamily: "Georgia, serif", marginBottom: 4 },
    cardSub: { color: "#64748b", fontSize: 13, marginBottom: 20, marginTop: 0 },
    label: { display: "block", fontWeight: 600, marginBottom: 5, fontSize: 13, color: "#374151" },
    input: { width: "100%", padding: "9px 12px", borderRadius: 7, border: "1.5px solid #e5e7eb", fontSize: 13, boxSizing: "border-box", marginBottom: 14, outline: "none" },
    btn: (color = "#0f1e3c", disabled = false) => ({ background: disabled ? "#94a3b8" : color, color: "#fff", border: "none", borderRadius: 7, padding: "10px 22px", fontWeight: 600, cursor: disabled ? "not-allowed" : "pointer", fontSize: 14 }),
    row: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 },
    row3: { display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 },
    toast: { position: "fixed", bottom: 24, left: "50%", transform: "translateX(-50%)", color: "#fff", padding: "12px 24px", borderRadius: 8, zIndex: 999, fontSize: 13, whiteSpace: "nowrap", boxShadow: "0 4px 20px rgba(0,0,0,0.2)" },
  };

  if (!authChecked) return null;
  if (!user) return <Login onLogin={handleLogin} />;

  // Sorted + filtered candidates for ranking
  const rankedCandidates = [...candidates]
    .sort((a, b) => (parseFloat(b.overall_score) || 0) - (parseFloat(a.overall_score) || 0));

  // Shortlisted rank counter
  let shortlistRank = 0;

  return (
    <div style={s.wrap}>
      {/* Header */}
      <div style={s.header}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 20, color: "#f0c040" }}>⬡</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: 16, fontFamily: "Georgia, serif" }}>RecruitAI</div>
            <div style={{ fontSize: 11, opacity: 0.6 }}>Autonomous Recruitment Agent</div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, background: "rgba(255,255,255,0.08)", borderRadius: 20, padding: "5px 14px", fontSize: 13 }}>
            <div style={{ width: 28, height: 28, borderRadius: "50%", background: "#f0c040", color: "#0f1e3c", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: 12 }}>{user.name[0].toUpperCase()}</div>
            <span>{user.name}</span>
          </div>
          <button style={{ background: "none", border: "1px solid rgba(255,255,255,0.2)", color: "rgba(255,255,255,0.7)", borderRadius: 6, padding: "3px 10px", fontSize: 12, cursor: "pointer" }} onClick={handleLogout}>Logout</button>
        </div>
      </div>

      {/* Nav */}
      <div style={s.nav}>
        {TABS.map((t, i) => <button key={i} style={s.navBtn(tab === i)} onClick={() => setTab(i)}>{t}</button>)}
      </div>

      <div style={s.body}>

        {/* TAB 0: Job Descriptions */}
        {tab === 0 && (
          <>
            <div style={s.card}>
              <h2 style={s.cardTitle}>✨ AI Job Description Generator</h2>
              <p style={s.cardSub}>Enter minimal info — AI generates a complete professional JD automatically.</p>

              <div style={s.row}>
                <div>
                  <label style={s.label}>Role Title *</label>
                  <input style={s.input} placeholder="e.g. Senior Python Developer" value={jdForm.role_title} onChange={e => setJdForm({ ...jdForm, role_title: e.target.value })} />
                </div>
                <div>
                  <label style={s.label}>Department *</label>
                  <input style={s.input} placeholder="e.g. Engineering" value={jdForm.department} onChange={e => setJdForm({ ...jdForm, department: e.target.value })} />
                </div>
              </div>

              <div style={s.row3}>
                <div>
                  <label style={s.label}>Location</label>
                  <input style={s.input} placeholder="e.g. Bangalore, India" value={jdForm.location} onChange={e => setJdForm({ ...jdForm, location: e.target.value })} />
                </div>
                <div>
                  <label style={s.label}>Employment Type</label>
                  <select style={s.input} value={jdForm.employment_type} onChange={e => setJdForm({ ...jdForm, employment_type: e.target.value })}>
                    <option>Full-time</option><option>Part-time</option><option>Contract</option><option>Internship</option>
                  </select>
                </div>
                <div>
                  <label style={s.label}>Work Mode</label>
                  <select style={s.input} value={jdForm.work_mode} onChange={e => setJdForm({ ...jdForm, work_mode: e.target.value })}>
                    <option>Hybrid</option><option>Remote</option><option>On-site</option>
                  </select>
                </div>
              </div>

              <div style={s.row}>
                <div>
                  <label style={s.label}>Years of Experience</label>
                  <input style={s.input} type="number" min={0} max={20} value={jdForm.experience_years} onChange={e => setJdForm({ ...jdForm, experience_years: e.target.value })} />
                </div>
                <div>
                  <label style={s.label}>Salary Range (optional)</label>
                  <input style={s.input} placeholder="e.g. ₹8-12 LPA" value={jdForm.salary_range} onChange={e => setJdForm({ ...jdForm, salary_range: e.target.value })} />
                </div>
              </div>

              <div>
                <label style={s.label}>Skills Hints (optional)</label>
                <input style={s.input} placeholder="e.g. FastAPI, PostgreSQL, Docker" value={jdForm.skills_hint} onChange={e => setJdForm({ ...jdForm, skills_hint: e.target.value })} />
              </div>

              <button style={s.btn()} onClick={handleGenerateJD} disabled={loading}>
                {loading ? "Generating…" : "🚀 Generate with AI"}
              </button>
            </div>

            {jds.length > 0 && (
              <div>
                <h3 style={{ color: "#0f1e3c", fontFamily: "Georgia, serif", marginBottom: 16 }}>Active Job Descriptions ({jds.length})</h3>
                {jds.map((jd, i) => (
                  <JDCard key={i} jd={jd} onDelete={handleDeleteJD} onEdit={handleEditJD} onUploadResumes={(jdId) => { setSelectedJdId(jdId); setTab(1); }} />
                ))}
              </div>
            )}

            {editingJd && (
              <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <div style={{ background: "#fff", borderRadius: 12, padding: 32, width: 600, maxHeight: "90vh", overflowY: "auto", boxShadow: "0 20px 60px rgba(0,0,0,0.3)" }}>
                  <h2 style={{ marginTop: 0, color: "#0f1e3c", fontFamily: "Georgia, serif" }}>✏️ Edit Job Description</h2>
                  {[
                    { label: "Role Title", key: "role_title" },
                    { label: "Department", key: "department" },
                    { label: "Location", key: "location" },
                    { label: "Salary Range", key: "salary_range" },
                    { label: "Required Skills (comma separated)", key: "required_skills" },
                    { label: "Preferred Skills (comma separated)", key: "preferred_skills" },
                  ].map(({ label, key }) => (
                    <div key={key}>
                      <label style={{ display: "block", fontWeight: 600, marginBottom: 4, fontSize: 13, color: "#374151" }}>{label}</label>
                      <input style={{ width: "100%", padding: "8px 12px", borderRadius: 7, border: "1.5px solid #e5e7eb", fontSize: 13, boxSizing: "border-box", marginBottom: 12 }} value={editForm[key] || ""} onChange={e => setEditForm({ ...editForm, [key]: e.target.value })} />
                    </div>
                  ))}
                  <div style={s.row}>
                    <div>
                      <label style={{ display: "block", fontWeight: 600, marginBottom: 4, fontSize: 13, color: "#374151" }}>Work Mode</label>
                      <select style={{ width: "100%", padding: "8px 12px", borderRadius: 7, border: "1.5px solid #e5e7eb", fontSize: 13, marginBottom: 12 }} value={editForm.work_mode} onChange={e => setEditForm({ ...editForm, work_mode: e.target.value })}>
                        <option>Hybrid</option><option>Remote</option><option>On-site</option>
                      </select>
                    </div>
                    <div>
                      <label style={{ display: "block", fontWeight: 600, marginBottom: 4, fontSize: 13, color: "#374151" }}>Employment Type</label>
                      <select style={{ width: "100%", padding: "8px 12px", borderRadius: 7, border: "1.5px solid #e5e7eb", fontSize: 13, marginBottom: 12 }} value={editForm.employment_type} onChange={e => setEditForm({ ...editForm, employment_type: e.target.value })}>
                        <option>Full-time</option><option>Part-time</option><option>Contract</option><option>Internship</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label style={{ display: "block", fontWeight: 600, marginBottom: 4, fontSize: 13, color: "#374151" }}>Summary</label>
                    <textarea style={{ width: "100%", padding: "8px 12px", borderRadius: 7, border: "1.5px solid #e5e7eb", fontSize: 13, boxSizing: "border-box", marginBottom: 12, height: 80 }} value={editForm.summary || ""} onChange={e => setEditForm({ ...editForm, summary: e.target.value })} />
                  </div>
                  <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
                    <button onClick={() => setEditingJd(null)} style={{ background: "#f1f5f9", border: "none", borderRadius: 7, padding: "10px 20px", cursor: "pointer", fontSize: 13, fontWeight: 600 }}>Cancel</button>
                    <button onClick={handleSaveEdit} style={{ background: "#0f1e3c", color: "#fff", border: "none", borderRadius: 7, padding: "10px 20px", cursor: "pointer", fontSize: 13, fontWeight: 600 }}>Save Changes</button>
                  </div>
                  <div>
  <label style={{ display: "block", fontWeight: 600, marginBottom: 4, fontSize: 13, color: "#374151" }}>
    Years of Experience
  </label>
  <input
    type="number"
    style={{ width: "100%", padding: "8px 12px", borderRadius: 7, border: "1.5px solid #e5e7eb", fontSize: 13, marginBottom: 12 }}
    value={editForm.experience_years || 0}
    onChange={e => setEditForm({ ...editForm, experience_years: Number(e.target.value) })}
  />
</div>
                </div>
              </div>
            )}
          </>
        )}
        

        {/* TAB 1: Upload Resumes */}
        {tab === 1 && (
          <div style={s.card}>
            <h2 style={s.cardTitle}>📄 Upload & Score Resumes</h2>
            <p style={s.cardSub}>Upload multiple resumes at once. Gemini agent evaluates each one autonomously.</p>

            <label style={s.label}>Select Job Description *</label>
            <select style={s.input} value={selectedJdId} onChange={e => setSelectedJdId(e.target.value)}>
              <option value="">-- Select a JD --</option>
              {jds.map((jd, i) => <option key={i} value={jd.jd_id}>{jd.role_title} — {jd.department}</option>)}
            </select>

            <label style={s.label}>Resume Files *</label>
            <div
              style={{ border: `2px dashed ${dragOver ? "#0f1e3c" : "#e2e8f0"}`, borderRadius: 8, padding: "24px", textAlign: "center", marginBottom: 14, background: dragOver ? "#f0f4ff" : "#f8fafc", cursor: "pointer", transition: "all 0.2s" }}
              onClick={() => fileInputRef.current.click()}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files); }}
            >
              <input ref={fileInputRef} type="file" multiple accept=".pdf,.docx,.doc,.jpg,.jpeg,.png,.tiff" style={{ display: "none" }} onChange={e => handleFiles(e.target.files)} />
              {resumeFiles.length === 0 ? (
                <div>
                  <div style={{ fontSize: 32, marginBottom: 8 }}>📁</div>
                  <div style={{ color: "#64748b", fontSize: 13 }}><strong>Click to select</strong> or drag & drop resumes here<br /><span style={{ fontSize: 11, color: "#94a3b8" }}>PDF, DOCX, JPG, PNG accepted</span></div>
                </div>
              ) : (
                <div>
                  <div style={{ fontWeight: 600, color: "#0f1e3c", marginBottom: 8 }}>{resumeFiles.length} file(s) selected:</div>
                  {resumeFiles.map((f, i) => <div key={i} style={{ fontSize: 12, color: "#64748b" }}>📄 {f.name}</div>)}
                  <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 8 }}>Click to change</div>
                </div>
              )}
            </div>

            <button style={s.btn("#0f1e3c", loading || resumeFiles.length === 0 || !selectedJdId)} onClick={handleUpload} disabled={loading || resumeFiles.length === 0 || !selectedJdId}>
              {loading ? `🤖 Agent processing ${resumeFiles.length} file(s)…` : `⬆️ Upload & Score ${resumeFiles.length > 0 ? resumeFiles.length + " Resume(s)" : ""}`}
            </button>

            {uploadResults.length > 0 && (
              <div style={{ marginTop: 24 }}>
                <h3 style={{ ...s.cardTitle, fontSize: 15 }}>Upload Results</h3>
                {uploadResults.map((r, i) => (
                  <div key={i} style={{
                    border: `1px solid ${r.status === "Shortlisted" ? "#86efac" : "#e2e8f0"}`,
                    borderRadius: 10, padding: 20, marginBottom: 12,
                    background: r.status === "Shortlisted" ? "#f0fdf4" : "#fff",
                    borderLeft: `4px solid ${r.status === "Shortlisted" ? "#16a34a" : r.recommendation === "Reject" ? "#dc2626" : r.recommendation === "Maybe" ? "#d97706" : "#94a3b8"}`,
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: 16, color: "#0f1e3c" }}>{r.name}</div>
                        <div style={{ fontSize: 12, color: "#64748b", marginTop: 2 }}>{r.email}</div>
                      </div>
                      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        {badge(r.score)}
                        {statusChip(r.status === "Duplicate" ? "Duplicate" : r.recommendation === "Not a Resume" ? "Rejected" : r.status)}
                      </div>
                    </div>

                    {/* Skills Analysis FIRST */}
                    {(r.matched_skills?.length > 0 || r.missing_skills?.length > 0) && (
                      <div style={{ marginBottom: 10 }}>
                        <div style={{ fontSize: 12, fontWeight: 600, color: "#374151", marginBottom: 4 }}>Skills Analysis:</div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                          {r.matched_skills?.map(sk => skillTag(sk, true))}
                          {r.missing_skills?.map(sk => skillTag(sk, false))}
                        </div>
                      </div>
                    )}

                    {/* AI Explanation AFTER */}
                    {r.rejection_reason && (
                      <div style={{ fontSize: 13, color: "#374151", background: "#f8fafc", padding: "8px 12px", borderRadius: 8, borderLeft: "3px solid #94a3b8" }}>
                        💡 <strong>AI Assessment:</strong> {r.rejection_reason}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: Ranking Dashboard */}
        {tab === 2 && (
          <div>
            <div style={s.card}>
              <h2 style={s.cardTitle}>🏆 Candidate Ranking Dashboard</h2>
              <p style={s.cardSub}>Select a Job Description to view ranked candidates.</p>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <select style={{ ...s.input, marginBottom: 0, flex: 2 }} value={selectedCandidateJdId} onChange={e => { setSelectedCandidateJdId(e.target.value); handleLoadCandidates(e.target.value); setFilterStatus("All"); }}>
                  <option value="">-- Select a Job Description --</option>
                  {jds.map((jd, i) => <option key={i} value={jd.jd_id}>{jd.role_title} — {jd.department}</option>)}
                </select>
                <select style={{ ...s.input, marginBottom: 0, flex: 1 }} value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
                  <option>All</option><option>Shortlisted</option><option>Maybe</option><option>Reject</option>
                </select>
              </div>

              {/* Outreach Button */}
              {selectedCandidateJdId && candidates.filter(c => c.status === "Shortlisted").length > 0 && (
                <div style={{ marginTop: 16, padding: 16, background: "#f0fdf4", borderRadius: 10, border: "1px solid #86efac", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 14, color: "#15803d" }}>🤖 Automated Outreach</div>
                    <div style={{ fontSize: 12, color: "#16a34a", marginTop: 2 }}>
                      {candidates.filter(c => c.status === "Shortlisted").length} shortlisted candidate(s) — Agent will send emails + schedule Google Meet interviews
                    </div>
                  </div>
                  <button
                    style={{ background: outreachLoading ? "#94a3b8" : "#16a34a", color: "#fff", border: "none", borderRadius: 8, padding: "10px 20px", fontWeight: 600, cursor: outreachLoading ? "not-allowed" : "pointer", fontSize: 13, whiteSpace: "nowrap" }}
                    onClick={handleRunOutreach}
                    disabled={outreachLoading}
                  >
                    {outreachLoading ? "🤖 Agent running…" : "📧 Run Outreach Agent"}
                  </button>
                </div>
              )}

              {/* Outreach Result */}
              {outreachResult && (
                <div style={{ marginTop: 12, padding: "12px 16px", background: "#f0f4ff", borderRadius: 8, border: "1px solid #bfdbfe", fontSize: 13, color: "#1d4ed8" }}>
                  🎉 <strong>Agent Report:</strong> {outreachResult.message}
                </div>
              )}
            </div>

            {!selectedCandidateJdId ? (
              <div style={{ ...s.card, textAlign: "center", padding: 48 }}>
                <div style={{ fontSize: 40, marginBottom: 12 }}>📋</div>
                <p style={{ color: "#94a3b8", fontSize: 14 }}>Select a Job Description above to view candidates.</p>
              </div>
            ) : candidates.length === 0 ? (
              <div style={{ ...s.card, textAlign: "center", padding: 48 }}>
                <div style={{ fontSize: 40, marginBottom: 12 }}>👥</div>
                <p style={{ color: "#94a3b8", fontSize: 14 }}>No candidates yet for this JD. Upload resumes to get started.</p>
              </div>
            ) : (
              <>
                {/* Stats */}
                <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
                  {[
                    { label: "Total", value: candidates.length, color: "#0f1e3c", icon: "👥" },
        { label: "Shortlisted", value: candidates.filter(
  c => ["Shortlisted", "Interview Scheduled", "Confirmed"].includes(c.status)
).length },
                    { label: "Maybe", value: candidates.filter(c => c.recommendation === "Maybe").length, color: "#d97706", icon: "🤔" },
                    { label: "Rejected", value: candidates.filter(c => c.recommendation === "Reject").length, color: "#dc2626", icon: "❌" },
                  ].map((item, i) => (
                    <div key={i} style={{ background: "#fff", borderRadius: 10, padding: "14px 20px", borderLeft: `4px solid ${item.color}`, flex: 1, boxShadow: "0 1px 4px rgba(0,0,0,.07)", cursor: "pointer" }} onClick={() => setFilterStatus(item.label === "Total" ? "All" : item.label)}>
                      <div style={{ fontSize: 24, fontWeight: 700, color: item.color }}>{item.value}</div>
                      <div style={{ fontSize: 12, color: "#64748b" }}>{item.icon} {item.label}</div>
                    </div>
                  ))}
                </div>

                {/* Candidate list */}
                {(() => {
                  shortlistRank = 0;
                  return rankedCandidates
                    .filter(c => {
  if (filterStatus === "All") return true;

  if (filterStatus === "Shortlisted") {
    return ["Shortlisted", "Interview Scheduled", "Confirmed"].includes(c.status);
  }

  return c.recommendation === filterStatus || c.status === filterStatus;
})
                    .map((c, i) => {
                      const isShortlisted = ["Shortlisted", "Interview Scheduled", "Confirmed"].includes(c.status);
                      if (isShortlisted) shortlistRank++;
                      const rank = shortlistRank;

                      return (
                        <div key={i} style={{ background: "#fff", borderRadius: 10, marginBottom: 12, boxShadow: "0 1px 4px rgba(0,0,0,.07)", border: `1px solid ${isShortlisted ? "#86efac" : "#e2e8f0"}`, overflow: "hidden" }}>
                          <div style={{ padding: "16px 20px", cursor: "pointer", background: isShortlisted ? "#f0fdf4" : "#fff", display: "flex", alignItems: "center", gap: 16 }} onClick={() => setExpandedCandidate(expandedCandidate === i ? null : i)}>

                            {/* Rank badge — only for shortlisted */}
                            <div style={{
                              width: 40, height: 40, borderRadius: "50%", flexShrink: 0,
                              background: isShortlisted ? (rank === 1 ? "#f0c040" : rank === 2 ? "#e2e8f0" : rank === 3 ? "#fed7aa" : "#dcfce7") : "#fee2e2",
                              color: isShortlisted ? (rank === 1 ? "#92400e" : "#475569") : "#dc2626",
                              display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: 13
                            }}>
                             {isShortlisted ? `#${rank}` : (c.recommendation === "Maybe" ? "🤔" : "✗")}
                            </div>

                            <div style={{ flex: 1 }}>
                              <div style={{ fontWeight: 700, fontSize: 15, color: "#0f1e3c" }}>{c.name}</div>
                              <div style={{ fontSize: 12, color: "#64748b" }}>{c.email} {c.years_experience ? `• ${c.years_experience}y exp` : ""}</div>
                            </div>

                            <div style={{ width: 120, flexShrink: 0 }}>
                              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                                <span style={{ fontSize: 11, color: "#64748b" }}>Match Score</span>
                                <span style={{ fontSize: 12, fontWeight: 700 }}>{parseFloat(c.overall_score || 0).toFixed(0)}%</span>
                              </div>
                              <div style={{ height: 6, background: "#e2e8f0", borderRadius: 3 }}>
                                <div style={{ height: 6, borderRadius: 3, width: `${Math.min(100, parseFloat(c.overall_score || 0))}%`, background: parseFloat(c.overall_score) >= 70 ? "#16a34a" : parseFloat(c.overall_score) >= 50 ? "#d97706" : "#dc2626" }} />
                              </div>
                            </div>

                            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                              {statusChip(c.status)}
                              <button
                                onClick={(e) => { e.stopPropagation(); handleDeleteCandidate(c.candidate_id); }}
                                style={{ background: "#fee2e2", border: "none", color: "#dc2626", borderRadius: 6, padding: "4px 8px", cursor: "pointer", fontSize: 12 }}>
                                🗑️
                              </button>
                              <span style={{ fontSize: 16, color: "#94a3b8" }}>{expandedCandidate === i ? "▲" : "▼"}</span>
                            </div>
                          </div>
{expandedCandidate === i && (
  <div style={{ padding: "16px 20px", borderTop: "1px solid #e2e8f0", background: "#f8fafc" }}>

    {/* 🔥 SELECTED SLOT (NEW) */}
    {c.selected_slot && c.status === "Confirmed" && (
      <div style={{
        marginBottom: 12,
        padding: "10px 14px",
        background: "#ecfeff",
        borderRadius: 8,
        border: "1px solid #67e8f9",
        fontSize: 13,
        color: "#0e7490",
        fontWeight: 600
      }}>
        📅 <strong>Selected Slot:</strong> {c.selected_slot}
      </div>
    )}

    {/* Score breakdown */}
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginBottom: 16 }}>
      {[
        { label: "Skills Match", value: c.skills_match, color: "#3b82f6" },
        { label: "Experience Match", value: c.experience_match, color: "#8b5cf6" },
        { label: "Education Match", value: c.education_match, color: "#06b6d4" },
      ].map((item, j) => (
        <div key={j} style={{ background: "#fff", borderRadius: 8, padding: "10px 14px" }}>
          <div style={{ fontSize: 11, color: "#64748b", marginBottom: 6 }}>{item.label}</div>
          <div style={{ height: 6, background: "#e2e8f0", borderRadius: 3, marginBottom: 4 }}>
            <div style={{
              height: 6,
              borderRadius: 3,
              width: `${Math.min(100, parseFloat(item.value || 0))}%`,
              background: item.color
            }} />
          </div>
          <div style={{ fontSize: 12, fontWeight: 700, color: item.color }}>
            {parseFloat(item.value || 0).toFixed(0)}%
          </div>
        </div>
      ))}
    </div>

    {/* Skills */}
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
      <div style={{ background: "#fff", borderRadius: 8, padding: "10px 14px" }}>
        <div style={{ fontWeight: 600, fontSize: 12, marginBottom: 6, color: "#16a34a" }}>
          ✅ Matched Skills
        </div>
        <div>
          {c.matched_skills
            ? c.matched_skills.split(", ").map(sk => skillTag(sk, true))
            : <span style={{ fontSize: 12, color: "#94a3b8" }}>None</span>}
        </div>
      </div>

      <div style={{ background: "#fff", borderRadius: 8, padding: "10px 14px" }}>
        <div style={{ fontWeight: 600, fontSize: 12, marginBottom: 6, color: "#dc2626" }}>
          ❌ Missing Skills
        </div>
        <div>
          {c.missing_skills
            ? c.missing_skills.split(", ").map(sk => skillTag(sk, false))
            : <span style={{ fontSize: 12, color: "#94a3b8" }}>None</span>}
        </div>
      </div>
    </div>

    {/* AI Assessment */}
    {c.rejection_reason && (
      <div style={{
        background: "#fff",
        borderRadius: 8,
        padding: "10px 14px",
        fontSize: 13,
        color: "#374151",
        border: "1px solid #e2e8f0"
      }}>
        💡 <strong>AI Assessment:</strong> {c.rejection_reason}
      </div>
    )}

  </div>
)}
                        </div>
                      );
                    });
                })()}
              </>
            )}
          </div>
        )}

        {/* TAB 3: LinkedIn */}
        {tab === 3 && (
          <div>
            <div style={s.card}>
              <h2 style={s.cardTitle}>🔗 LinkedIn Candidate Sourcing</h2>
              <p style={s.cardSub}>Search LinkedIn for candidates, scrape profiles and score them automatically.</p>

              <label style={s.label}>Search Keywords *</label>
              <input style={s.input} placeholder="e.g. Python Developer Bangalore" value={linkedInKeywords} onChange={e => setLinkedInKeywords(e.target.value)} />

              <label style={s.label}>Select Job Description *</label>
              <select style={s.input} value={linkedInJdId} onChange={e => setLinkedInJdId(e.target.value)}>
                <option value="">-- Select a JD --</option>
                {jds.map((jd, i) => <option key={i} value={jd.jd_id}>{jd.role_title} — {jd.department}</option>)}
              </select>

              <label style={s.label}>Max Profiles to Scrape</label>
              <select style={s.input} value={linkedInMax} onChange={e => setLinkedInMax(Number(e.target.value))}>
                <option value={2}>2 profiles</option>
                <option value={10}>10 profiles</option>
                <option value={20}>20 profiles</option>
              </select>

              <button
                style={s.btn("#0f1e3c", loading || !linkedInKeywords || !linkedInJdId)}
                disabled={loading || !linkedInKeywords || !linkedInJdId}
                onClick={async () => {
                  setLoading(true); setLinkedInResults([]);
                  try {
                    const r = await scrapeLinkedIn(linkedInKeywords, linkedInJdId, linkedInMax);

setLinkedInResults(r.data.results || []);

// ✅ ADD THIS (AUTO REFRESH)
await handleLoadCandidates(linkedInJdId);

notify(`✅ Scraped and scored ${r.data.processed} LinkedIn profiles!`);
                  } catch (e) { notify("❌ " + (e.response?.data?.detail || e.message), "error"); }
                  setLoading(false);
                }}
              >
                {loading ? "Scraping LinkedIn…" : "🔍 Search & Score LinkedIn Profiles"}
              </button>
            </div>

            {linkedInResults.length > 0 && (
              <div style={s.card}>
                <h3 style={{ ...s.cardTitle, fontSize: 15 }}>LinkedIn Results ({linkedInResults.length})</h3>
                {linkedInResults.map((r, i) => (
                  <div key={i} style={{ border: "1px solid #e2e8f0", borderRadius: 8, padding: 16, marginBottom: 10, background: r.status === "Shortlisted" ? "#f0fdf4" : "#fff", borderLeft: `4px solid ${r.recommendation === "Shortlist" ? "#16a34a" : r.recommendation === "Maybe" ? "#d97706" : "#dc2626"}` }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: 15 }}>{r.name}</div>
                        <div style={{ fontSize: 12, color: "#64748b" }}>{r.current_title}</div>
                        {r.linkedin_url && <a href={r.linkedin_url} target="_blank" rel="noreferrer" style={{ fontSize: 11, color: "#3b82f6" }}>View Profile →</a>}
                      </div>
                      <div style={{ display: "flex", gap: 8 }}>{badge(r.score)}{statusChip(r.status)}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

      </div>

      {msg.text && (
        <div style={{ ...s.toast, background: msg.type === "error" ? "#dc2626" : "#0f1e3c" }}>
          {msg.text}
        </div>
      )}
    </div>
  );
}