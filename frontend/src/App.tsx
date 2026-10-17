import { useEffect, useRef, useState } from "react";
import {
  Activity,
  ClipboardList,
  LayoutDashboard,
  LogOut,
  Menu,
  Plus,
  Shield,
  Users,
  X,
} from "lucide-react";
import { api, type User, type Audit, type Metrics } from "./api";
import { Login, IncidentForm } from "./forms";
import Analyzer from "./Analyzer";
import { Detail, IncidentList, Timeline } from "./incidents";
import { Overview, Team } from "./workspace";
const navigation = [
  { name: "Dashboard", icon: LayoutDashboard },
  { name: "Incidents", icon: ClipboardList },
  { name: "Activity", icon: Activity },
  { name: "Analyzer", icon: Shield },
  { name: "Team", icon: Users },
];
const route = () => {
  const [name, id] = location.hash.slice(1).split("/");
  return {
    view:
      name === "incident" && /^\d+$/.test(id || "")
        ? "Incident detail"
        : navigation.find((n) => n.name.toLowerCase() === name)?.name ||
          (name === "new" ? "New incident" : "Dashboard"),
    id: Number(id) || 0,
  };
};
export default function App() {
  const [user, setUser] = useState<User | null>();
  const [page, setPage] = useState(route);
  const [refresh, setRefresh] = useState(0);
  const [metrics, setMetrics] = useState<Metrics>();
  const [events, setEvents] = useState<Audit[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const noticePath = useRef(location.hash);
  const showNotice = (message: string, expectedPath: string) => {
    if (location.hash !== expectedPath) return;
    noticePath.current = expectedPath;
    setNotice(message);
  };
  const [offset, setOffset] = useState(0);
  const [severity, setSeverity] = useState("");
  const [menu, setMenu] = useState(false);
  const drawer = useRef<HTMLDialogElement>(null);
  const go = (view: string, id = 0) => {
    location.hash =
      view === "Incident detail"
        ? `incident/${id}`
        : view === "New incident"
          ? "new"
          : view.toLowerCase();
    setMenu(false);
    setNotice("");
  };
  useEffect(() => {
    const change = () => {
      setPage(route());
      if (noticePath.current !== location.hash) setNotice("");
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", change);
    return () => window.removeEventListener("hashchange", change);
  }, []);
  useEffect(() => {
    api<User>("/auth/me")
      .then(setUser)
      .catch(() => setUser(null));
    const expire = () => setUser(null);
    window.addEventListener("session-expired", expire);
    return () => window.removeEventListener("session-expired", expire);
  }, []);
  useEffect(() => {
    if (menu) drawer.current?.showModal();
    else drawer.current?.close();
  }, [menu]);
  useEffect(() => {
    if (!user) return;
    let active = true;
    Promise.all([
      api<Metrics>("/metrics"),
      api<Audit[]>(
        `/activity?limit=20&offset=${page.view === "Activity" ? offset : 0}`,
      ),
      api<User[]>("/users"),
    ])
      .then(([m, e, u]) => {
        if (active) {
          setMetrics(m);
          setEvents(e);
          setUsers(u);
          setError("");
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [user, refresh, page.view, offset]);
  const open = (id: number) => go("Incident detail", id);
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
          setMetrics(undefined);
          setEvents([]);
          setUsers([]);
        }}
      />
    );
  const view = page.view;
  const nav = (
    <>
      <a className="brand" href="#dashboard" onClick={() => setMenu(false)}>
        <Shield size={23} />
        IncidentOps
      </a>
      <div className="workspace">
        <span className="workspace-icon">IO</span>
        <div>
          Security operations<small>Incident workspace</small>
        </div>
      </div>
      <p className="nav-label">WORKSPACE</p>
      <nav aria-label="Workspace">
        {navigation
          .filter((n) => n.name !== "Analyzer" || user.role !== "viewer")
          .map(({ name, icon: Icon }) => (
            <a
              key={name}
              href={`#${name.toLowerCase()}`}
              aria-current={
                view === name ||
                (name === "Incidents" && view === "Incident detail")
                  ? "page"
                  : undefined
              }
              onClick={() => {
                setMenu(false);
                setSeverity("");
                setNotice("");
              }}
            >
              <Icon size={17} />
              {name}
              {name === "Incidents" && (
                <span className="nav-count">{metrics?.unresolved ?? "–"}</span>
              )}
            </a>
          ))}
      </nav>
      <div className="sidebar-bottom">
        <div className="profile">
          <span className="avatar">
            {user.username.slice(0, 2).toUpperCase()}
          </span>
          <div>
            {user.username}
            <small>{user.role}</small>
          </div>
          <button
            className="icon secondary"
            aria-label="Sign out"
            onClick={async () => {
              try {
                await api("/auth/logout", { method: "POST" });
                setUser(null);
                setMenu(false);
              } catch (e) {
                setError((e as Error).message);
              }
            }}
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </>
  );
  return (
    <div
      className="app-shell"
      data-styleseed-recipe="enterprise-workbench"
      data-styleseed-artifact="incidentops"
    >
      <a
        href="#main-content"
        className="skip-link"
        onClick={(e) => {
          e.preventDefault();
          document.getElementById("main-content")?.focus();
        }}
      >
        Skip to content
      </a>
      <aside className="sidebar">{nav}</aside>
      <dialog
        ref={drawer}
        className="mobile-drawer"
        aria-label="Workspace navigation"
        onCancel={() => setMenu(false)}
      >
        <button
          className="icon secondary drawer-close"
          aria-label="Close navigation"
          onClick={() => setMenu(false)}
        >
          <X />
        </button>
        {menu && nav}
      </dialog>
      <main className="main" id="main-content" tabIndex={-1}>
        <header className="topbar">
          <button
            className="icon secondary mobile-menu"
            aria-label="Open navigation"
            onClick={() => setMenu(true)}
          >
            <Menu size={20} />
          </button>
          <span>
            Workspace <span className="breadcrumb">/</span>{" "}
            <strong>{view}</strong>
          </span>
          <span className="session-label">
            {user.username.startsWith("demo.")
              ? "Synthetic demo data"
              : "Security operations"}
          </span>
        </header>
        <div className="content">
          <div className="page-heading">
            <div>
              {user.username.startsWith("demo.") && (
                <small className="mobile-demo">Synthetic demo data</small>
              )}
              <h1>
                {view === "Dashboard"
                  ? "Security overview"
                  : view === "Analyzer"
                    ? "Suspicious-login analyzer"
                    : view === "Team"
                      ? "Team & permissions"
                      : view}
              </h1>
              <p>
                {
                  {
                    Dashboard:
                      "Triage incoming reports and keep investigations moving.",
                    Incidents:
                      "Search, prioritize, and manage reported incidents.",
                    Activity:
                      "A traceable record of case changes and analyst actions.",
                    Analyzer:
                      "Review login evidence before opening an investigation.",
                    Team: "Workspace access and responsibilities.",
                    "Incident detail":
                      "Review evidence, document decisions, and coordinate response.",
                    "New incident": "Record the initial facts for triage.",
                  }[view]
                }
              </p>
            </div>
            {user.role !== "viewer" &&
              (view === "Dashboard" || view === "Incidents") && (
                <button onClick={() => go("New incident")}>
                  <Plus size={16} />
                  Report incident
                </button>
              )}
          </div>
          {notice && (
            <div className="notice" role="status">
              {notice}
            </div>
          )}
          {error && (
            <div role="alert" className="error">
              {error}
              <button
                className="text-button"
                onClick={() => setRefresh((v) => v + 1)}
              >
                Retry
              </button>
            </div>
          )}
          {view === "Dashboard" && (
            <Overview
              metrics={metrics}
              events={events}
              users={users}
              refresh={refresh}
              open={open}
              filter={(s) => {
                setSeverity(s);
                go("Incidents");
              }}
              activity={() => go("Activity")}
            />
          )}
          {view === "Incidents" && (
            <IncidentList
              key={severity}
              open={open}
              users={users}
              refresh={refresh}
              initialSeverity={severity}
            />
          )}
          {view === "New incident" &&
            (user.role === "viewer" ? (
              <p className="empty">
                Analyst permission is required to report incidents.
              </p>
            ) : (
              <IncidentForm
                onCancel={() => go("Incidents")}
                onCreated={(i) => {
                  setRefresh((r) => r + 1);
                  open(i.id);
                  showNotice(
                    "Incident created. Ready for triage.",
                    `#incident/${i.id}`,
                  );
                }}
              />
            ))}
          {view === "Incident detail" && (
            <Detail
              key={page.id}
              id={page.id}
              user={user}
              users={users}
              onChange={() => setRefresh((r) => r + 1)}
            />
          )}
          {view === "Activity" && (
            <section className="panel audit-stream">
              <div className="section-heading">
                <h3>Audit activity</h3>
                <span className="muted">Newest first · read only</span>
              </div>
              <Timeline events={events} open={open} />
              <div className="pagination">
                <span>
                  Events {events.length ? offset + 1 : 0}–
                  {offset + events.length}
                </span>
                <div>
                  <button
                    className="secondary"
                    disabled={!offset}
                    onClick={() => setOffset((o) => o - 20)}
                  >
                    Previous
                  </button>
                  <button
                    className="secondary"
                    disabled={events.length < 20}
                    onClick={() => setOffset((o) => o + 20)}
                  >
                    Next
                  </button>
                </div>
              </div>
            </section>
          )}
          {view === "Analyzer" &&
            (user.role === "viewer" ? (
              <p className="empty">
                Analyst permission is required to analyze records.
              </p>
            ) : (
              <Analyzer
                open={(id) => {
                  setRefresh((r) => r + 1);
                  open(id);
                }}
              />
            ))}
          {view === "Team" && (
            <Team
              users={users}
              user={user}
              changed={() => {
                setRefresh((r) => r + 1);
                showNotice("Workspace member created.", "#team");
              }}
            />
          )}
          <footer>
            <span>IncidentOps / Security operations</span>
            <span>Times in your local timezone unless marked UTC</span>
          </footer>
        </div>
      </main>
    </div>
  );
}
