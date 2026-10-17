import { useState } from "react";
import { api, send, type Incident } from "./api";
type Flag = {
  username: string;
  failure_count: number;
  window_minutes: number;
  success_after_failures: boolean;
  source_ips: string[];
  timestamp: string;
  rule: string;
};
type Result = { records: number; flags: Flag[]; notice: string };
export default function Analyzer({ open }: { open: (id: number) => void }) {
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [result, setResult] = useState<Result>();
  const [busy, setBusy] = useState(false);
  return (
    <section className="panel">
      <h3>Login event analyzer</h3>
      <p className="muted">
        Use synthetic or authorized example records only. Five failed logins for
        an account within ten minutes create an informational flag. A flag does
        not prove an intrusion.
      </p>
      <label>
        Import example CSV
        <input
          type="file"
          accept=".csv,text/csv"
          onChange={async (e) => {
            const file = e.target.files?.[0];
            setError("");
            setResult(undefined);
            if (!file) return;
            if (
              !file.name.toLowerCase().endsWith(".csv") ||
              file.size > 50000
            ) {
              setError("Choose a CSV file under 50 KB.");
              return;
            }
            setText(await file.text());
          }}
        />
      </label>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          setError("");
          setResult(undefined);
          try {
            setResult(await api<Result>("/analyzer", send({ csv_text: text })));
          } catch (e) {
            setError((e as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        <label>
          CSV records
          <textarea
            aria-label="CSV records"
            rows={10}
            value={text}
            required
            maxLength={50000}
            onChange={(e) => setText(e.target.value)}
            placeholder="timestamp,username,source_ip,success"
          />
        </label>
        <p className="muted">
          Exact header: timestamp,username,source_ip,success · timezone required
          · success is true or false · up to 1,000 rows
        </p>
        <button disabled={busy}>
          {busy ? "Analyzing…" : "Analyze example records"}
        </button>
      </form>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {result && (
        <>
          <h3 className="analyzer-results">
            {result.records} records analyzed · {result.flags.length} flagged
            accounts
          </h3>
          <p className="muted">{result.notice}</p>
          {result.flags.length === 0 && (
            <p>No patterns matched the documented rule.</p>
          )}
          {result.flags.map((f) => (
            <article className="note" key={f.username}>
              <h3>
                {f.username} · {f.failure_count} failures
              </h3>
              <p>
                {f.rule}.{" "}
                {f.success_after_failures
                  ? "A success followed the failures."
                  : "No subsequent success identified in the flagged window."}
              </p>
              <small>
                {f.timestamp} · {f.source_ips.join(", ")}
              </small>
              <p>
                <button
                  disabled={busy}
                  onClick={async () => {
                    setBusy(true);
                    setError("");
                    try {
                      const i = await api<Incident>(
                        "/incidents",
                        send({
                          title: "Review login pattern for " + f.username,
                          severity: "medium",
                          category: "Suspicious Login",
                          description: `Informational rule match, not proof of intrusion. ${f.rule}. ${f.failure_count} failures. Sources: ${f.source_ips.join(", ")}. Flag observed ${f.timestamp}. Success after failures: ${f.success_after_failures}. Validate with the account owner before containment.`,
                        }),
                      );
                      open(i.id);
                    } catch (e) {
                      setError((e as Error).message);
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  Create investigation incident
                </button>
              </p>
            </article>
          ))}
        </>
      )}
    </section>
  );
}
