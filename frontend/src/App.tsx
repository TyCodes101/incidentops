import { useEffect, useState } from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowRight,
  CheckCircle2,
  CircleAlert,
  ClipboardList,
  LayoutDashboard,
  LogOut,
  Plus,
  Shield,
  Users,
} from "lucide-react";
import { api, send, type User, type Audit, type Metrics } from "./api";
import { Login, IncidentForm, severities } from "./forms";
import Analyzer from "./Analyzer";
import { Detail, IncidentList, Pill, Timeline } from "./incidents";
export default function App() {
  const [user, setUser] = useState<User | null>();
  const [view, setView] = useState("Dashboard");
  const [id, setId] = useState(0);
  const [refresh, setRefresh] = useState(0);
  const [metrics, setMetrics] = useState<Metrics>();
  const [events, setEvents] = useState<Audit[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [activityOffset, setActivityOffset] = useState(0);
  const [filterSeverity, setFilterSeverity] = useState("");
  useEffect(() => {
    api<User>("/auth/me")
      .then(setUser)
      .catch(() => setUser(null));
    const expire = () => setUser(null);
    window.addEventListener("session-expired", expire);
    return () => window.removeEventListener("session-expired", expire);
  }, []);
  useEffect(() => {
    if (!user) return;
    let active = true;
    setError("");
    Promise.all([
      api<Metrics>("/metrics"),
      api<Audit[]>(
        "/activity?limit=20&offset=" +
          (view === "Activity" ? activityOffset : 0),
      ),
      api<User[]>("/users"),
    ])
      .then(([m, e, u]) => {
        if (active) {
          setMetrics(m);
          setEvents(e);
          setUsers(u);
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [user, refresh, activityOffset, view]);
  const open = (n: number) => {
    setId(n);
    setView("Incident detail");
    setNotice("");
  };
  if (user === undefined)
    return (
      <div className="empty" role="status">
        Opening IncidentOps…
      </div>
    );
  if (!user)
    return (
      <Login
        onLogin={(u) => {
          setUser(u);
          setView("Dashboard");
        }}
      />
    );
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a
          href="#"
          className="brand"
          onClick={(e) => {
            e.preventDefault();
            setView("Dashboard");
          }}
        >
          <Shield /> IncidentOps
          <span className="brand-dot" />
        </a>
        <div className="workspace">
          <span className="workspace-icon">IO</span>
          <div>
            Security workspace<small>Incident command center</small>
          </div>
        </div>
        <small className="nav-label">WORKSPACE</small>
        <nav>
          {[
            { name: "Dashboard", icon: LayoutDashboard },
            { name: "Incidents", icon: ClipboardList },
            { name: "Activity", icon: Activity },
            { name: "Team", icon: Users },
            ...(user.role !== "viewer"
              ? [{ name: "Analyzer", icon: Shield }]
              : []),
          ].map(({ name, icon: Icon }) => (
            <button
              key={name}
              className={view === name ? "active" : ""}
              onClick={() => {
                setView(name);
                setFilterSeverity("");
                setNotice("");
              }}
            >
              <Icon size={18} />
              {name}
              {name === "Incidents" && (
                <span>{metrics?.unresolved ?? "–"}</span>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="response-note">
            <Shield size={20} />
            <strong>Every action accounted for.</strong>
            <p>Keep the investigation and its history together.</p>
          </div>
          <div className="profile">
            <span className="avatar">
              {user.username.slice(0, 2).toUpperCase()}
            </span>
            <div>
              {user.username}
              <small>{user.role}</small>
            </div>
            <button
              aria-label="Sign out"
              className="icon"
              onClick={async () => {
                try {
                  await api("/auth/logout", { method: "POST" });
                  setUser(null);
                } catch (e) {
                  setError((e as Error).message);
                }
              }}
            >
              <LogOut size={17} />
            </button>
          </div>
        </div>
      </aside>
      <main className="main">
        <header className="topbar">
          <span>
            Workspace <span className="muted">/</span> <strong>{view}</strong>
          </span>
          <span className="session-label">
            <span className="online-dot" />
            {user.username.startsWith("demo.")
              ? "Synthetic demo workspace"
              : "Authenticated session"}
          </span>
        </header>
        <div className="content">
          <div className="page-heading">
            <div>
              <p className="eyebrow">INCIDENTOPS / OPERATIONS</p>
              <h1>{view === "Dashboard" ? "Security overview" : view}</h1>
              <p>
                {view === "Dashboard"
                  ? "A clear view of your incident response workload."
                  : "Security incidents, under control."}
              </p>
            </div>
            {user.role !== "viewer" && view !== "New incident" && (
              <button onClick={() => setView("New incident")}>
                <Plus size={17} />
                Report incident
              </button>
            )}
          </div>
          {notice && (
            <div role="status" className="notice">
              {notice}
            </div>
          )}
          {error && (
            <div role="alert" className="error">
              {error}
              <button
                className="text-button"
                onClick={() => setRefresh((r) => r + 1)}
              >
                Retry
              </button>
            </div>
          )}
          {view === "Dashboard" && (
            <>
              {!metrics ? (
                <p role="status">Loading workspace metrics…</p>
              ) : (
                <>
                  <div className="stats">
                    {[
                      {
                        name: "Total incidents",
                        value: metrics.total,
                        caption: "All recorded cases",
                        icon: ClipboardList,
                      },
                      {
                        name: "Open",
                        value: metrics.by_status.open,
                        caption: "Awaiting triage",
                        icon: CircleAlert,
                      },
                      {
                        name: "Investigating",
                        value: metrics.by_status.investigating,
                        caption: "Active response",
                        icon: Activity,
                      },
                      {
                        name: "Resolved",
                        value: metrics.by_status.resolved,
                        caption: "Investigation complete",
                        icon: CheckCircle2,
                      },
                    ].map(({ name, value, caption, icon: Icon }) => (
                      <div className="stat" key={name}>
                        <div>
                          {name}
                          <Icon size={18} />
                        </div>
                        <strong>{value}</strong>
                        <small>{caption}</small>
                      </div>
                    ))}
                  </div>
                  <div className="charts">
                    <section className="panel trend">
                      <div className="section-heading">
                        <div>
                          <h3>Incident reporting trend</h3>
                          <p>Reports by creation date · UTC</p>
                        </div>
                        <span className="legend">
                          <i />
                          Reported
                        </span>
                      </div>
                      {metrics.trends.length === 0 ? (
                        <p className="empty">
                          Trend data appears after your first report.
                        </p>
                      ) : (
                        <div
                          className="bars"
                          role="img"
                          aria-label="Incident reports by date"
                        >
                          {metrics.trends.slice(-14).map((t) => (
                            <div className="bar-column" key={t.date}>
                              <span>{t.count}</span>
                              <div
                                title={`${t.date}: ${t.count} reports`}
                                style={{
                                  height: `${Math.max(8, (t.count / Math.max(...metrics.trends.map((t) => t.count))) * 120)}px`,
                                }}
                              />
                              <small>{t.date.slice(5)}</small>
                            </div>
                          ))}
                        </div>
                      )}
                    </section>
                    <section className="panel severity">
                      <div className="section-heading">
                        <div>
                          <h3>Severity distribution</h3>
                          <p>
                            {metrics.by_severity.critical +
                              metrics.by_severity.high}{" "}
                            high or critical cases
                          </p>
                        </div>
                        <ArrowDownRight size={20} />
                      </div>
                      {severities.map((s) => (
                        <button
                          key={s}
                          className="severity-row"
                          onClick={() => {
                            setFilterSeverity(s);
                            setView("Incidents");
                          }}
                          aria-label={`${s}: ${metrics.by_severity[s]} incidents. Filter incident queue.`}
                        >
                          <span>
                            <i className={s} />
                            {s}
                          </span>
                          <div>
                            <b
                              style={{
                                width: `${metrics.total ? (metrics.by_severity[s] / metrics.total) * 100 : 0}%`,
                              }}
                            />
                          </div>
                          <strong>{metrics.by_severity[s]}</strong>
                        </button>
                      ))}
                    </section>
                  </div>
                  <IncidentList open={open} refresh={refresh} />
                  <section className="panel">
                    <div className="section-heading">
                      <h3>Recent activity</h3>
                      <button
                        className="text-button"
                        onClick={() => {
                          setActivityOffset(0);
                          setView("Activity");
                        }}
                      >
                        View all activity <ArrowRight size={14} />
                      </button>
                    </div>
                    <Timeline events={events.slice(0, 4)} open={open} />
                  </section>
                </>
              )}
            </>
          )}
          {view === "Incidents" && (
            <IncidentList
              key={filterSeverity}
              open={open}
              refresh={refresh}
              initialSeverity={filterSeverity}
            />
          )}
          {view === "New incident" && (
            <IncidentForm
              onCancel={() => setView("Incidents")}
              onCreated={(i) => {
                setRefresh((r) => r + 1);
                open(i.id);
                setNotice("Incident created. Your investigation is ready.");
              }}
            />
          )}
          {view === "Incident detail" && (
            <Detail
              key={id}
              id={id}
              user={user}
              users={users}
              onChange={() => setRefresh((r) => r + 1)}
            />
          )}
          {view === "Activity" && (
            <section className="panel">
              <h3>Audit activity</h3>
              <p className="muted">
                Read-only records of case actions and responsible users.
              </p>
              <Timeline events={events} open={open} />
              <div className="pagination">
                <button
                  className="secondary"
                  disabled={!activityOffset}
                  onClick={() => setActivityOffset((o) => o - 20)}
                >
                  Previous
                </button>
                <button
                  className="secondary"
                  disabled={events.length < 20}
                  onClick={() => setActivityOffset((o) => o + 20)}
                >
                  Next
                </button>
              </div>
            </section>
          )}
          {view === "Analyzer" && (
            <Analyzer
              open={(n) => {
                setRefresh((r) => r + 1);
                open(n);
              }}
            />
          )}
          {view === "Team" && (
            <section className="panel">
              <h3>Workspace members</h3>
              <p className="muted">
                Viewers can read. Analysts investigate. Admins provision users
                and assign cases.
              </p>
              {users.map((u) => (
                <div className="member" key={u.id}>
                  <span className="avatar">
                    {u.username.slice(0, 2).toUpperCase()}
                  </span>
                  <strong>{u.username}</strong>
                  <Pill value={u.role} />
                </div>
              ))}
              {user.role === "admin" && (
                <form
                  className="member-form"
                  onSubmit={async (e) => {
                    e.preventDefault();
                    const form = e.currentTarget;
                    try {
                      await api(
                        "/users",
                        send(Object.fromEntries(new FormData(form))),
                      );
                      form.reset();
                      setNotice("Workspace member created.");
                      setRefresh((r) => r + 1);
                    } catch (e) {
                      setError((e as Error).message);
                    }
                  }}
                >
                  <h3>Add workspace member</h3>
                  <label>
                    Username
                    <input name="username" required maxLength={80} />
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
                  </label>
                  <label>
                    Role
                    <select name="role">
                      <option>viewer</option>
                      <option>analyst</option>
                      <option>admin</option>
                    </select>
                  </label>
                  <button>Create account</button>
                </form>
              )}
            </section>
          )}
          <footer>
            IncidentOps <span>Security incidents, under control.</span>
            <span>Times displayed in your local timezone</span>
          </footer>
        </div>
      </main>
    </div>
  );
}
