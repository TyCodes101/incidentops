import { useEffect, useState } from "react";
import { ArrowRight, CheckCircle2, Search } from "lucide-react";
import {
  api,
  incidentPage,
  send,
  type User,
  type Incident,
  type Audit,
  type Note,
} from "./api";
import { statuses, severities, categories } from "./forms";
export const date = (s: string) =>
  new Date(
    s.endsWith("Z") || /[+-]\d\d:\d\d$/.test(s) ? s : s + "Z",
  ).toLocaleString();
export function Pill({ value }: { value: string }) {
  return <span className={"pill " + value}>{value.replaceAll("_", " ")}</span>;
}
export function Timeline({
  events,
  open,
}: {
  events: Audit[];
  open: (id: number) => void;
}) {
  return (
    <div className="timeline">
      {events.length === 0 ? (
        <p className="empty">
          No activity yet. New case activity will appear here.
        </p>
      ) : (
        events.map((e) => (
          <div className="event" key={e.id}>
            <span className="event-dot" />
            <div>
              <button
                className="text-button"
                onClick={() => open(e.incident_id)}
              >
                INC-{String(e.incident_id).padStart(4, "0")} ·{" "}
                {e.action.replaceAll("_", " ")}
              </button>
              <p>{e.detail}</p>
              <small>
                {e.actor} · {date(e.occurred_at)}
              </small>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
function EditSummary({
  item,
  save,
}: {
  item: Incident;
  save: (body: unknown) => Promise<boolean>;
}) {
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  if (!editing)
    return (
      <button className="text-button" onClick={() => setEditing(true)}>
        Edit incident summary
      </button>
    );
  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        setSaving(true);
        if (await save(Object.fromEntries(new FormData(e.currentTarget))))
          setEditing(false);
        setSaving(false);
      }}
    >
      <label>
        Title
        <input
          name="title"
          defaultValue={item.title}
          required
          minLength={3}
          maxLength={120}
        />
      </label>
      <label>
        Description
        <textarea
          name="description"
          defaultValue={item.description}
          maxLength={3000}
          rows={4}
        />
      </label>
      <label>
        Category
        <input
          name="category"
          defaultValue={item.category}
          required
          minLength={2}
          maxLength={40}
        />
      </label>
      <button disabled={saving}>{saving ? "Saving..." : "Save summary"}</button>{" "}
      <button
        type="button"
        className="secondary"
        onClick={() => setEditing(false)}
      >
        Cancel
      </button>
    </form>
  );
}
export function Detail({
  id,
  user,
  users,
  onChange,
}: {
  id: number;
  user: User;
  users: User[];
  onChange: () => void;
}) {
  const [item, setItem] = useState<Incident>();
  const [notes, setNotes] = useState<Note[]>([]);
  const [events, setEvents] = useState<Audit[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [version, setVersion] = useState(0);
  useEffect(() => {
    let active = true;
    Promise.all([
      api<Incident>("/incidents/" + id),
      api<Note[]>(`/incidents/${id}/notes`),
      api<Audit[]>(`/incidents/${id}/history`),
    ])
      .then(([i, n, h]) => {
        if (active) {
          setItem(i);
          setNotes(n);
          setEvents(h);
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [id, version]);
  const patch = async (body: unknown) => {
    setBusy(true);
    setError("");
    try {
      await api("/incidents/" + id, send(body, "PATCH"));
      setVersion((v) => v + 1);
      onChange();
      return true;
    } catch (e) {
      setError((e as Error).message);
      return false;
    } finally {
      setBusy(false);
    }
  };
  if (!item)
    return error ? (
      <div className="error" role="alert">
        {error}
        <button
          className="secondary"
          onClick={() => {
            setError("");
            setVersion((v) => v + 1);
          }}
        >
          Retry investigation
        </button>
      </div>
    ) : (
      <div className="empty" role="status">
        Loading investigation...
      </div>
    );
  return (
    <>
      <div className="case-heading">
        <div>
          <p className="eyebrow">
            INC-{String(id).padStart(4, "0")} / {item.category}
          </p>
          <h2>{item.title}</h2>
          <p>
            Reported {date(item.created_at)} · Updated {date(item.updated_at)}
          </p>
        </div>
        <Pill value={item.severity} />
      </div>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <div className="detail-grid">
        <section>
          <div className="panel">
            <h3>Incident summary</h3>
            <p className="description">
              {item.description || "No additional description provided."}
            </p>
            {user.role !== "viewer" && <EditSummary item={item} save={patch} />}
          </div>
          <div className="panel">
            <h3>
              Investigation notes <span className="muted">{notes.length}</span>
            </h3>
            {notes.map((n) => (
              <article className="note" key={n.id}>
                <small>
                  {n.author} · {date(n.created_at)}
                </small>
                <p>{n.body}</p>
              </article>
            ))}
            {notes.length === 0 && (
              <p className="muted">
                Document observations, actions, and decisions here.
              </p>
            )}
            {user.role !== "viewer" && (
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  const form = e.currentTarget;
                  setBusy(true);
                  setError("");
                  try {
                    await api(
                      `/incidents/${id}/notes`,
                      send({ body: new FormData(form).get("body") }),
                    );
                    form.reset();
                    setVersion((v) => v + 1);
                    onChange();
                  } catch (e) {
                    setError((e as Error).message);
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                <label>
                  Add a note
                  <textarea name="body" required maxLength={3000} rows={3} />
                </label>
                <button disabled={busy}>Add investigation note</button>
              </form>
            )}
          </div>
          <div className="panel">
            <h3>Chronological history</h3>
            <Timeline
              events={events}
              open={() =>
                document
                  .querySelector(".case-heading")
                  ?.scrollIntoView({ behavior: "smooth" })
              }
            />
          </div>
        </section>
        <aside className="panel inspector">
          <h3>Case properties</h3>
          <label>
            Status
            <select
              aria-label="Status"
              value={item.status}
              disabled={busy || user.role === "viewer"}
              onChange={(e) => void patch({ status: e.target.value })}
            >
              {statuses.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
          <label>
            Severity
            <select
              aria-label="Severity"
              value={item.severity}
              disabled={busy || user.role === "viewer"}
              onChange={(e) => void patch({ severity: e.target.value })}
            >
              {severities.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
          <label>
            Assigned analyst
            <select
              aria-label="Assigned analyst"
              value={item.assignee_id ?? ""}
              disabled={busy || user.role !== "admin"}
              onChange={(e) =>
                void patch({
                  assignee_id: e.target.value ? Number(e.target.value) : null,
                })
              }
            >
              <option value="">Unassigned</option>
              {users
                .filter((u) => u.role !== "viewer")
                .map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.username}
                  </option>
                ))}
            </select>
          </label>
          <p className="muted">
            Changes are saved immediately and recorded in the audit history.
          </p>
          {user.role !== "viewer" && (
            <button
              className="secondary"
              disabled={busy}
              onClick={() => {
                if (
                  window.confirm(
                    item.status === "resolved"
                      ? "Reopen this incident?"
                      : "Mark this investigation as resolved?",
                  )
                )
                  void patch({
                    status: item.status === "resolved" ? "open" : "resolved",
                  });
              }}
            >
              <CheckCircle2 size={16} />
              {item.status === "resolved"
                ? "Reopen incident"
                : "Resolve incident"}
            </button>
          )}
        </aside>
      </div>
    </>
  );
}
export function IncidentList({
  open,
  refresh,
  initialSeverity = "",
  users = [],
  compact = false,
}: {
  open: (id: number) => void;
  refresh: number;
  initialSeverity?: string;
  users?: User[];
  compact?: boolean;
}) {
  const [q, setQ] = useState("");
  const [status, setStatus] = useState(compact ? "open" : "");
  const [severity, setSeverity] = useState(initialSeverity);
  const [category, setCategory] = useState("");
  const [sort, setSort] = useState("newest");
  const [offset, setOffset] = useState(0);
  const [rows, setRows] = useState<Incident[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    const timer = setTimeout(() => {
      const params = new URLSearchParams({
        q,
        status,
        severity,
        category,
        sort,
        offset: String(offset),
        limit: compact ? "5" : "10",
      });
      for (const k of ["status", "severity", "category"])
        if (!params.get(k)) params.delete(k);
      incidentPage(params.toString())
        .then((r) => {
          if (active) {
            setRows(r.items);
            setTotal(r.total);
          }
        })
        .catch((e) => {
          if (active) setError(e.message);
        })
        .finally(() => {
          if (active) setLoading(false);
        });
    }, 200);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [q, status, severity, category, sort, offset, refresh, retry, compact]);
  return (
    <section className={"panel queue" + (compact ? " compact-queue" : "")}>
      <div className="section-heading">
        <h3>
          {compact ? "Awaiting triage" : "Incident queue"}{" "}
          <span className="count">{total}</span>
        </h3>
        <span className="muted">
          {compact ? "Newest open reports" : "All reported cases"}
        </span>
      </div>
      {!compact && (
        <div className="filters">
          <label className="search">
            <Search size={17} />
            <input
              aria-label="Search incidents"
              placeholder="Search incidents…"
              value={q}
              onChange={(e) => {
                setQ(e.target.value);
                setOffset(0);
              }}
            />
          </label>
          <select
            aria-label="Filter status"
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setOffset(0);
            }}
          >
            <option value="">All statuses</option>
            {statuses.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
          <select
            aria-label="Filter severity"
            value={severity}
            onChange={(e) => {
              setSeverity(e.target.value);
              setOffset(0);
            }}
          >
            <option value="">All severities</option>
            {severities.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
          <select
            aria-label="Filter category"
            value={category}
            onChange={(e) => {
              setCategory(e.target.value);
              setOffset(0);
            }}
          >
            <option value="">All categories</option>
            {categories.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
          <select
            aria-label="Sort incidents"
            value={sort}
            onChange={(e) => {
              setSort(e.target.value);
              setOffset(0);
            }}
          >
            <option value="newest">Newest first</option>
            <option value="oldest">Oldest first</option>
            <option value="title">Title A–Z</option>
          </select>
        </div>
      )}
      {!compact && (q || status || severity || category) && (
        <button
          className="text-button clear-filters"
          onClick={() => {
            setQ("");
            setStatus("");
            setSeverity("");
            setCategory("");
            setOffset(0);
          }}
        >
          Clear filters
        </button>
      )}
      {error ? (
        <p role="alert" className="error">
          {error}{" "}
          <button
            className="text-button"
            onClick={() => setRetry((v) => v + 1)}
          >
            Retry
          </button>
        </p>
      ) : loading ? (
        <p className="empty" role="status">
          Loading incidents…
        </p>
      ) : rows.length === 0 ? (
        <p className="empty">
          No incidents match. Adjust your filters or report a new incident.
        </p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Incident / category</th>
                <th>Severity</th>
                <th>Status</th>
                {!compact && <th>Assigned to</th>}
                <th>Updated</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {rows.map((i) => (
                <tr key={i.id}>
                  <td>
                    <button className="case-link" onClick={() => open(i.id)}>
                      <small>INC-{String(i.id).padStart(4, "0")}</small>
                      <strong>{i.title}</strong>
                    </button>
                    <span className="category">{i.category}</span>
                  </td>
                  <td data-label="Severity">
                    <Pill value={i.severity} />
                  </td>
                  <td data-label="Status">
                    <Pill value={i.status} />
                  </td>
                  {!compact && (
                    <td data-label="Assigned to" className="muted">
                      {users.find((u) => u.id === i.assignee_id)?.username ||
                        "Unassigned"}
                    </td>
                  )}
                  <td data-label="Updated" className="muted timestamp">
                    {date(i.updated_at)}
                  </td>
                  <td>
                    <button
                      className="icon secondary"
                      aria-label={"Open " + i.title}
                      onClick={() => open(i.id)}
                    >
                      <ArrowRight size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="pagination">
        <small>
          {total === 0
            ? "0 incidents"
            : `${offset + 1}–${Math.min(offset + (compact ? 5 : 10), total)} of ${total} incidents`}
        </small>
        <div>
          <button
            className="secondary"
            disabled={offset === 0 || loading}
            onClick={() => setOffset(offset - (compact ? 5 : 10))}
          >
            Previous
          </button>
          <button
            className="secondary"
            disabled={offset + (compact ? 5 : 10) >= total || loading}
            onClick={() => setOffset(offset + (compact ? 5 : 10))}
          >
            Next
          </button>
        </div>
      </div>
    </section>
  );
}
