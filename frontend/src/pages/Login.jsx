// frontend/src/pages/Login.jsx
import { useState } from "react";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPass, setShowPass] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const form = new URLSearchParams();
      form.append("username", email.trim().toLowerCase());
      form.append("password", password.trim());

      const res = await fetch(
  `${process.env.REACT_APP_API_URL || "http://127.0.0.1:8000"}/auth/login`,
  {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
      email: email.trim().toLowerCase(), 
      password: password.trim() 
    }),
  }
);
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Login failed");
      }

      const { access_token, user_name, user_email, user_role } = data;

      localStorage.setItem("token", access_token);
      localStorage.setItem(
        "user",
        JSON.stringify({
          name: user_name,
          email: user_email,
          role: user_role,
        })
      );

      onLogin({
        name: user_name,
        email: user_email,
        role: user_role,
      });

    } catch (err) {
      setError(err.message || "Login failed. Check your credentials.");
    }

    setLoading(false);
  };

  return (
    <div style={styles.page}>
      {/* Left panel — branding */}
      <div style={styles.left}>
        <div style={styles.leftInner}>
          <div style={styles.logo}>
            <span style={styles.logoIcon}>⬡</span>
            <span style={styles.logoText}>RecruitAI</span>
          </div>
          <h1 style={styles.headline}>
            Hire smarter.<br />
            <span style={styles.headlineAccent}>Not harder.</span>
          </h1>
          <p style={styles.subtext}>
            AI-powered recruitment pipeline <br />
          </p>

          <div style={styles.circle1} />
          <div style={styles.circle2} />
        </div>
      </div>

      {/* Right panel — form */}
      <div style={styles.right}>
        <div style={styles.formCard}>
          <div style={styles.formHeader}>
            <h2 style={styles.formTitle}>Welcome back</h2>
            <p style={styles.formSub}>Sign in to your HR dashboard</p>
          </div>

          <form onSubmit={handleLogin} style={styles.form}>
            <div style={styles.field}>
              <label style={styles.label}>Email address</label>
              <div style={styles.inputWrap}>
                <span style={styles.inputIcon}>✉</span>
                <input
                  style={styles.input}
                  type="email"
                  placeholder="hr@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoFocus
                />
              </div>
            </div>

            <div style={styles.field}>
              <label style={styles.label}>Password</label>
              <div style={styles.inputWrap}>
                <span style={styles.inputIcon}>⬤</span>
                <input
                  style={{ ...styles.input, paddingRight: 44 }}
                  type={showPass ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  style={styles.eyeBtn}
                  onClick={() => setShowPass((v) => !v)}
                  tabIndex={-1}
                >
                  {showPass ? "🙈" : "👁"}
                </button>
              </div>
            </div>

            {error && (
              <div style={styles.errorBox}>
                <span>⚠</span> {error}
              </div>
            )}

            <button style={styles.btn} type="submit" disabled={loading}>
              {loading ? (
                <span style={styles.spinner}>↻ Signing in…</span>
              ) : (
                "Sign in →"
              )}
            </button>
          </form>
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
    padding: "48px",
    maxWidth: 420,
  },
  logo: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    marginBottom: 48,
  },
  logoIcon: {
    fontSize: 28,
    color: "#f0c040",
  },
  logoText: {
    color: "#fff",
    fontSize: 22,
    fontWeight: 700,
    letterSpacing: "0.05em",
    fontFamily: "'Georgia', serif",
  },
  headline: {
    color: "#fff",
    fontSize: 42,
    fontWeight: 700,
    lineHeight: 1.2,
    margin: "0 0 20px",
    letterSpacing: "-0.01em",
  },
  headlineAccent: {
    color: "#f0c040",
  },
  subtext: {
    color: "rgba(255,255,255,0.6)",
    fontSize: 15,
    lineHeight: 1.7,
    margin: "0 0 32px",
  },
  right: {
    width: 480,
    background: "#fafaf8",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "40px 32px",
  },
  formCard: {
    width: "100%",
    maxWidth: 360,
  },
  formHeader: {
    marginBottom: 36,
  },
  formTitle: {
    fontSize: 28,
    fontWeight: 700,
    color: "#0f1e3c",
    margin: "0 0 6px",
    fontFamily: "'Georgia', serif",
  },
  formSub: {
    color: "#6b7280",
    fontSize: 14,
    margin: 0,
    fontFamily: "system-ui, sans-serif",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: 20,
  },
  field: {
    display: "flex",
    flexDirection: "column",
    gap: 7,
  },
  label: {
    fontSize: 13,
    fontWeight: 600,
    color: "#374151",
    fontFamily: "system-ui, sans-serif",
    letterSpacing: "0.02em",
  },
  inputWrap: {
    position: "relative",
    display: "flex",
    alignItems: "center",
  },
  inputIcon: {
    position: "absolute",
    left: 12,
    fontSize: 13,
    color: "#9ca3af",
    pointerEvents: "none",
    zIndex: 1,
  },
  input: {
    width: "100%",
    padding: "11px 12px 11px 36px",
    border: "1.5px solid #e5e7eb",
    borderRadius: 8,
    fontSize: 14,
    color: "#111827",
    background: "#fff",
    outline: "none",
    boxSizing: "border-box",
    fontFamily: "system-ui, sans-serif",
    transition: "border-color 0.15s",
  },
  eyeBtn: {
    position: "absolute",
    right: 10,
    background: "none",
    border: "none",
    cursor: "pointer",
    fontSize: 14,
    padding: 4,
  },
  errorBox: {
    background: "#fef2f2",
    border: "1px solid #fecaca",
    color: "#b91c1c",
    borderRadius: 8,
    padding: "10px 14px",
    fontSize: 13,
    display: "flex",
    gap: 8,
    alignItems: "center",
    fontFamily: "system-ui, sans-serif",
  },
  btn: {
    background: "#0f1e3c",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    padding: "13px",
    fontSize: 15,
    fontWeight: 600,
    cursor: "pointer",
    letterSpacing: "0.02em",
    fontFamily: "'Georgia', serif",
    transition: "background 0.15s",
    marginTop: 4,
  },
  spinner: {
    display: "inline-block",
  },
};