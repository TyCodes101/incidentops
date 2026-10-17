export type User = {
  id: number;
  username: string;
  role: "admin" | "analyst" | "viewer";
};
export type Incident = {
  id: number;
  title: string;
  description: string;
  status: string;
  severity: string;
  category: string;
  assignee_id: number | null;
  created_at: string;
  updated_at: string;
};
export type Audit = {
  id: number;
  incident_id: number;
  actor: string;
  action: string;
  detail: string;
  occurred_at: string;
};
export type Note = {
  id: number;
  body: string;
  author: string;
  created_at: string;
};
export type Metrics = {
  total: number;
  unresolved: number;
  by_severity: Record<string, number>;
  by_status: Record<string, number>;
  trends: { date: string; count: number }[];
};
export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const csrf =
    document.cookie
      .split("; ")
      .find((c) => c.startsWith("csrf="))
      ?.slice(5) ?? "";
  const response = await fetch("/api" + path, {
    ...init,
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrf,
      ...init.headers,
    },
  });
  if (!response.ok) {
    const data = await response
      .json()
      .catch(() => ({ detail: "Service unavailable" }));
    if (
      response.status === 401 &&
      path !== "/auth/login" &&
      path !== "/auth/me"
    )
      window.dispatchEvent(new Event("session-expired"));
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "Check the form values and try again",
    );
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
export async function incidentPage(query: string) {
  const response = await fetch("/api/incidents?" + query, {
    credentials: "same-origin",
  });
  if (!response.ok) {
    if (response.status === 401)
      window.dispatchEvent(new Event("session-expired"));
    throw new Error("Unable to load incidents. Sign in again or retry.");
  }
  return {
    items: (await response.json()) as Incident[],
    total: Number(response.headers.get("X-Total-Count")),
  };
}
export const send = (body: unknown, method = "POST") => ({
  method,
  body: JSON.stringify(body),
});
