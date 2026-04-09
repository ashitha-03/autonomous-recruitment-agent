// frontend/src/pages/Confirmed.jsx
import { useEffect, useState } from "react";

export default function Confirmed() {
  const [params, setParams] = useState({});

  useEffect(() => {
    const p = Object.fromEntries(new URLSearchParams(window.location.search));
    setParams(p);
  }, []);

  const status = params.status;
  const name = params.name || "Candidate";
  const slot = params.slot || "";
  const meet = params.meet || "";

  const config = {
    confirmed: {
      icon: "✅",
      color: "#16a34a",
      bg: "#f0fdf4",
      border: "#86efac",
      title: "Interview Confirmed!",
      message: `Dear ${name}, your interview has been successfully scheduled.`,
    },
    reschedule: {
      icon: "🔄",
      color: "#d97706",
      bg: "#fffbeb",
      border: "#fcd34d",
      title: "Reschedule Requested",
      message: `Dear ${name}, your reschedule request has been received. Our HR team will contact you shortly with new slots.`,
    },
    declined: {
      icon: "👋",
      color: "#6b7280",
      bg: "#f9fafb",
      border: "#e5e7eb",
      title: "Application Withdrawn",
      message: `Dear ${name}, we respect your decision. Thank you for your time and interest. We wish you all the best!`,
    },
    already: {
      icon: "ℹ️",
      color: "#1d4ed8",
      bg: "#eff6ff",
      border: "#93c5fd",
      title: "Already Confirmed",
      message: `You have already selected a slot: ${slot}. No changes can be made.`,
    },
    error: {
      icon: "❌",
      color: "#dc2626",
      bg: "#fef2f2",
      border: "#fca5a5",
      title: "Something went wrong",
      message: params.message || "An error occurred. Please contact HR.",
    },
  };

  const c = config[status] || config.error;

  return (
    <div style={styles.page}>
      {/* Left branding panel */}
      <div style={styles.left}>
        <div style={styles.leftInner}>
          <div style={styles.logo}>
            <span style={{ fontSize: 28, color: "#f0c040" }}>⬡</span>
            <span style={styles.logoText}>RecruitAI</span>
          </div>
          <h1 style={styles.headline}>
            Hire smarter.<br />
            <span style={{ color: "#f0c040" }}>Not harder.</span>
          </h1>
          <p style={styles.subtext}>AI-powered recruitment pipeline</p>
          <div style={styles.circle1} />
          <div style={styles.circle2} />
        </div>
      </div>

      {/* Right content panel */}
      <div style={styles.right}>
        <div style={styles.card}>

          {/* Status icon */}
          <div style={{ fontSize: 64, marginBottom: 16, textAlign: "center" }}>
            {c.icon}
          </div>

          {/* Title */}
          <h2 style={{ ...styles.title, color: c.color }}>
            {c.title}
          </h2>

          {/* Message */}
          <p style={styles.message}>{c.message}</p>

          {/* ✅ CONFIRMED: Show slot + Meet link */}
          {status === "confirmed" && (
            <div style={{ ...styles.infoBox, background: c.bg, border: `1px solid ${c.border}` }}>

              {slot && (
                <div style={styles.infoRow}>
                  <span style={styles.infoIcon}>📅</span>
                  <div>
                    <div style={styles.infoLabel}>Interview Scheduled</div>
                    <div style={{ ...styles.infoValue, color: c.color }}>{slot}</div>
                  </div>
                </div>
              )}

              {meet && (
                <div style={{ ...styles.infoRow, marginTop: 16 }}>
                  <span style={styles.infoIcon}>🎥</span>
                  <div>
                    <div style={styles.infoLabel}>Google Meet Link</div>
                    <a
                      href={meet}
                      target="_blank"
                      rel="noreferrer"
                      style={styles.meetLink}
                    >
                      Join Meeting →
                    </a>
                  </div>
                </div>
              )}

              {!meet && (
                <div style={{ ...styles.infoRow, marginTop: 16 }}>
                  <span style={styles.infoIcon}>📍</span>
                  <div>
                    <div style={styles.infoLabel}>Location</div>
                    <div style={styles.infoValue}>Office – Kochi</div>
                  </div>
                </div>
              )}

              <div style={styles.note}>
                📧 A calendar invite has been sent to your email.
              </div>
            </div>
          )}

          {/* Footer */}
          <div style={styles.footer}>
            <span style={{ color: "#94a3b8" }}>⬡</span>{" "}
            <span style={{ color: "#64748b", fontSize: 13 }}>
              10xDS – Exponential Digital Solutions
            </span>
          </div>

        </div>
      </div>
    </div>
  );
}

const styles = {
  page: {
    display: "flex",
    minHeight: "100vh",
    fontFamily: "'Georgia', 'Times New Roman', serif",
  },
  left: {
    flex: 1,
    background: "linear-gradient(135deg, #0f1e3c 0%, #1a3a6b 60%, #0d2d5e 100%)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    position: "relative",
    overflow: "hidden",
  },
  leftInner: {
    position: "relative",
    zIndex: 2,
    padding: 48,
    maxWidth: 420,
  },
  logo: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    marginBottom: 48,
  },
  logoText: {
    color: "#fff",
    fontSize: 22,
    fontWeight: 700,
    letterSpacing: "0.05em",
  },
  headline: {
    color: "#fff",
    fontSize: 42,
    fontWeight: 700,
    lineHeight: 1.2,
    margin: "0 0 20px",
  },
  subtext: {
    color: "rgba(255,255,255,0.6)",
    fontSize: 15,
    lineHeight: 1.7,
  },
  circle1: {
    position: "absolute",
    width: 300,
    height: 300,
    borderRadius: "50%",
    background: "rgba(255,255,255,0.03)",
    bottom: -80,
    right: -80,
  },
  circle2: {
    position: "absolute",
    width: 200,
    height: 200,
    borderRadius: "50%",
    background: "rgba(255,255,255,0.03)",
    top: 40,
    right: 40,
  },
  right: {
    width: 520,
    background: "#fafaf8",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "40px 32px",
  },
  card: {
    width: "100%",
    maxWidth: 420,
    textAlign: "center",
  },
  title: {
    fontSize: 26,
    fontWeight: 700,
    margin: "0 0 12px",
    fontFamily: "'Georgia', serif",
  },
  message: {
    fontSize: 15,
    color: "#4b5563",
    lineHeight: 1.6,
    margin: "0 0 24px",
    fontFamily: "system-ui, sans-serif",
  },
  infoBox: {
    borderRadius: 12,
    padding: "20px 24px",
    textAlign: "left",
    marginBottom: 24,
  },
  infoRow: {
    display: "flex",
    gap: 14,
    alignItems: "flex-start",
  },
  infoIcon: {
    fontSize: 22,
    flexShrink: 0,
    marginTop: 2,
  },
  infoLabel: {
    fontSize: 11,
    color: "#6b7280",
    fontFamily: "system-ui, sans-serif",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    marginBottom: 4,
  },
  infoValue: {
    fontSize: 15,
    fontWeight: 600,
    color: "#0f1e3c",
    fontFamily: "system-ui, sans-serif",
  },
  meetLink: {
    fontSize: 15,
    fontWeight: 600,
    color: "#1d4ed8",
    textDecoration: "none",
    fontFamily: "system-ui, sans-serif",
  },
  note: {
    marginTop: 16,
    fontSize: 12,
    color: "#6b7280",
    fontFamily: "system-ui, sans-serif",
    borderTop: "1px solid rgba(0,0,0,0.06)",
    paddingTop: 12,
  },
  footer: {
    marginTop: 32,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
};