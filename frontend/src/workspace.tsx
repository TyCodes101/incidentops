import { useState } from "react";
import { ArrowRight, Plus } from "lucide-react";
import { api, send, type User, type Metrics, type Audit } from "./api";
import { IncidentList, Timeline, Pill } from "./incidents";
import { severities } from "./forms";
export function Overview({
  metrics,
  events,
  users,
  refresh,
  open,
  filter,
  activity,
}: {
  metrics?: Metrics;
  events: Audit[];
  users: User[];
  refresh: number;
  open: (id: number) => void;
  filter: (s: string) => void;
  activity: () => void;
}) {
  if (!metrics)
    return (
      <div className="empty" role="status">
        Loading workspace metrics…
      </div>
    );
  return (
    <>
      <div className="workload">
        <div>
          <span>Unresolved workload</span>
          <strong>
            {metrics.unresolved}
            <small>cases</small>
          </strong>
        </div>
        <dl>
          {["open", "investigating", "resolved"].map((s) => (
            <div key={s}>
              <dt>
                {s === "open"
                  ? "Awaiting triage"
                  : s === "investigating"
                    ? "In investigation"
                    : "Resolved"}
              </dt>
              <dd>{metrics.by_status[s]}</dd>
            </div>
          ))}
        </dl>
        <span className="scope">All {metrics.total} recorded incidents</span>
      </div>
      <div className="overview-grid">
        <div>
          <IncidentList open={open} users={users} refresh={refresh} compact />
          <section className="panel distribution">
            <div className="section-heading">
              <div>
                <h3>Severity distribution</h3>
                <p>All recorded cases, including resolved</p>
              </div>
            </div>
            <div className="severity-scale">
              {severities.map((s) => (
                <button
                  key={s}
                  className="severity-row"
                  onClick={() => filter(s)}
                >
                  <Pill value={s} />
                  <strong>{metrics.by_severity[s]}</strong>
                  <span className="meter">
                    <i
                      style={{
                        width: `${metrics.total ? (metrics.by_severity[s] / metrics.total) * 100 : 0}%`,
                      }}
                    />
                  </span>
                </button>
              ))}
            </div>
          </section>
        </div>
        <aside className="evidence-rail">
          <section className="panel">
            <div className="section-heading">
              <h3>Recent activity</h3>
              <button
                className="icon secondary"
                aria-label="View all activity"
                onClick={activity}
              >
                <ArrowRight size={16} />
              </button>
            </div>
            <Timeline events={events.slice(0, 3)} open={open} />
          </section>
          <section className="panel trend">
            <div className="section-heading">
              <div>
                <h3>Incident reporting trend</h3>
                <p>Last 7 calendar days · UTC</p>
              </div>
            </div>
            <div
              className="bars"
              role="img"
              aria-label="Daily incident reports over the last seven UTC dates"
            >
              {Array.from({ length: 7 }, (_, i) => {
                const d = new Date();
                d.setUTCDate(d.getUTCDate() - 6 + i);
                const key = d.toISOString().slice(0, 10);
                const count =
                  metrics.trends.find((t) => t.date === key)?.count ?? 0;
                const max = Math.max(1, ...metrics.trends.map((t) => t.count));
                return (
                  <div className="bar-column" key={key}>
                    <span>{count}</span>
                    <div
                      title={`${key}: ${count} reports`}
                      style={{ height: `${(count / max) * 80}px` }}
                    />
                    <small>{key.slice(5)}</small>
                  </div>
                );
              })}
            </div>
          </section>
        </aside>
      </div>
    </>
  );
}
export function Team({
  users,
  user,
  changed,
}: {
  users: User[];
  user: User;
  changed: () => void;
}) {
  const [adding, setAdding] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [role, setRole] = useState("viewer");
  return (
    <div className="team-grid">
      <section className="panel">
        <div className="section-heading">
          <h3>
            Workspace members <span className="count">{users.length}</span>
          </h3>
          {user.role === "admin" && (
            <button className="secondary" onClick={() => setAdding(!adding)}>
              <Plus size={16} />
              {adding ? "Close form" : "Add member"}
            </button>
          )}
        </div>
        <div className="member-table">
          {users.map((u) => (
            <div className="member" key={u.id}>
              <span className="avatar">
                {u.username.slice(0, 2).toUpperCase()}
              </span>
              <div>
                <strong>{u.username}</strong>
                <small>
                  {u.id === user.id ? "Current account" : `Member #${u.id}`}
                </small>
              </div>
              <Pill value={u.role} />
            </div>
          ))}
        </div>
        {adding && (
          <form
            className="member-form"
            onSubmit={async (e) => {
              e.preventDefault();
              const form = e.currentTarget;
              setBusy(true);
              setError("");
              try {
                await api(
                  "/users",
                  send(Object.fromEntries(new FormData(form))),
                );
                form.reset();
                setAdding(false);
                changed();
              } catch (e) {
                setError((e as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            <h3>Add workspace member</h3>
            <label>
              Username
              <input
                name="username"
                required
                maxLength={80}
                autoComplete="off"
              />
            </label>
            <label>
              Initial password
              <input
                name="password"
                type="password"
                required
                minLength={12}
                maxLength={200}
                autoComplete="new-password"
              />
              <small>
                At least 12 characters. Share through your approved secure
                channel.
              </small>
            </label>
            <label>
              Role
              <select
                name="role"
                aria-label="Role"
                value={role}
                onChange={(e) => setRole(e.target.value)}
              >
                <option>viewer</option>
                <option>analyst</option>
                <option>admin</option>
              </select>
            </label>
            <p className="permission-note">
              {role === "admin"
                ? "Administrators can create accounts, assign cases, and investigate."
                : role === "analyst"
                  ? "Analysts can create and update incidents, add notes, and analyze records."
                  : "Viewers have read-only access to cases, activity, and the member directory."}
            </p>
            {error && (
              <p role="alert" className="error">
                {error}
              </p>
            )}
            <button disabled={busy}>
              {busy ? "Creating…" : "Create account"}
            </button>
          </form>
        )}
      </section>
      <aside className="panel role-guide">
        <h3>Role permissions</h3>
        <p>Access is enforced by the API.</p>
        {[
          [
            "Viewer",
            "Read incidents, notes, audit activity, and the member directory.",
          ],
          [
            "Analyst",
            "Viewer access, plus incident reporting, investigation updates, notes, and login analysis.",
          ],
          [
            "Admin",
            "Analyst access, plus account provisioning and incident assignment.",
          ],
        ].map(([title, body]) => (
          <div key={title}>
            <h4>{title}</h4>
            <p>{body}</p>
          </div>
        ))}
        <p className="permission-note">
          Existing roles are read only. Contact your administrator for account
          access changes.
        </p>
      </aside>
    </div>
  );
}
