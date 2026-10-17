import { useState } from "react";
import { ArrowRight, Shield, X } from "lucide-react";
import { api, send, type User, type Incident } from "./api";
export const statuses = ["open", "investigating", "resolved"];
export const severities = ["critical", "high", "medium", "low"];
export const categories = [
  "Phishing",
  "Identity & Access",
  "Malware Report",
  "Data Exposure",
  "Suspicious Login",
  "Endpoint",
  "Other",
];
export function Login({ onLogin }: { onLogin: (u: User) => void }) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  return (
    <div className="login">
      <div className="login-brand">
        <Shield size={24} /> IncidentOps <span>Security operations</span>
      </div>
      <main className="login-form">
        <p className="eyebrow">WORKSPACE ACCESS</p>
        <h1>Welcome back</h1>
        <p>Sign in to your incident workspace.</p>
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            setError("");
            setBusy(true);
            const f = new FormData(e.currentTarget);
            try {
              onLogin(
                await api<User>("/auth/login", send(Object.fromEntries(f))),
              );
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <label>
            Username
            <input name="username" autoComplete="username" required />
          </label>
          <label>
            Password
            <input
              name="password"
              type="password"
              autoComplete="current-password"
              required
            />
          </label>
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
          <button disabled={busy}>
            {busy ? "Signing in…" : "Sign in"} <ArrowRight size={16} />
          </button>
        </form>
        <small>
          Use an account provisioned by your administrator.
          <br />
          Contact your administrator if you need access.
        </small>
      </main>
    </div>
  );
}
export function IncidentForm({
  onCreated,
  onCancel,
}: {
  onCreated: (i: Incident) => void;
  onCancel: () => void;
}) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  return (
    <section className="form-panel">
      <div className="section-heading">
        <div>
          <h2>Report an incident</h2>
          <p>Capture what you know. Investigation comes next.</p>
        </div>
        <button
          className="icon secondary"
          aria-label="Cancel new incident"
          onClick={onCancel}
        >
          <X />
        </button>
      </div>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          setError("");
          const f = new FormData(e.currentTarget);
          try {
            onCreated(
              await api<Incident>("/incidents", send(Object.fromEntries(f))),
            );
          } catch (e) {
            setError((e as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        <label>
          Incident title
          <input
            name="title"
            minLength={3}
            maxLength={120}
            required
            placeholder="Describe the suspected issue"
          />
        </label>
        <div className="form-grid">
          <label>
            Severity
            <select aria-label="Severity" name="severity" defaultValue="medium">
              {severities.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
          <label>
            Category
            <select aria-label="Category" name="category">
              {categories.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
        </div>
        <label>
          Description
          <textarea
            name="description"
            maxLength={3000}
            rows={6}
            placeholder="What happened, what was observed, and what needs review?"
          />
        </label>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        <button disabled={busy}>
          {busy ? "Creating…" : "Create incident"} <ArrowRight size={16} />
        </button>
      </form>
    </section>
  );
}
