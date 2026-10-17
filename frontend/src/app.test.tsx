import { afterEach, describe, it, expect, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { Login, IncidentForm } from "./forms";
import { IncidentList, Detail } from "./incidents";
import type { User } from "./api";
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
const ok = (data: unknown, total = 1) =>
  Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve(data),
    headers: new Headers({ "X-Total-Count": String(total) }),
  });
const item = {
  id: 1,
  title: "Suspected account compromise",
  description: "Review authorized demo records",
  severity: "high",
  status: "open",
  category: "Identity & Access",
  assignee_id: null,
  created_at: "2026-10-16T12:00:00Z",
  updated_at: "2026-10-16T12:00:00Z",
};
const user: User = { id: 1, username: "analyst", role: "analyst" };
describe("incident workflows", () => {
  it("shows login errors returned by the API", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({
          ok: false,
          status: 401,
          json: () =>
            Promise.resolve({ detail: "Incorrect username or password" }),
        }),
      ),
    );
    render(<Login onLogin={vi.fn()} />);
    fireEvent.change(screen.getByLabelText("Username"), {
      target: { value: "demo" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "wrong" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Incorrect username or password",
    );
  });
  it("creates an incident from form values", async () => {
    const fetcher = vi.fn((_path: string, _init?: RequestInit) => ok(item));
    vi.stubGlobal("fetch", fetcher);
    const created = vi.fn();
    render(<IncidentForm onCreated={created} onCancel={vi.fn()} />);
    fireEvent.change(screen.getByLabelText("Incident title"), {
      target: { value: item.title },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create incident" }));
    await waitFor(() => expect(created).toHaveBeenCalledWith(item));
    expect(JSON.parse(fetcher.mock.calls[0]![1]!.body as string)).toMatchObject(
      { title: item.title, severity: "medium" },
    );
  });
  it("filters through the server and opens a case", async () => {
    const fetcher = vi.fn((_path: string) => ok([item]));
    vi.stubGlobal("fetch", fetcher);
    const open = vi.fn();
    render(<IncidentList open={open} refresh={0} />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading");
    await screen.findByText(item.title);
    fireEvent.change(screen.getByLabelText("Filter severity"), {
      target: { value: "high" },
    });
    await waitFor(() =>
      expect(fetcher.mock.calls.at(-1)?.[0]).toContain("severity=high"),
    );
    await screen.findByText(item.title);
    fireEvent.click(screen.getByText(item.title));
    expect(open).toHaveBeenCalledWith(1);
  });
  it("shows service errors and permits retry", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve({ ok: false, status: 500 })),
    );
    render(<IncidentList open={vi.fn()} refresh={0} />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Unable to load",
    );
    expect(screen.getByRole("button", { name: "Retry" })).toBeEnabled();
  });
  it("updates status using PATCH and refreshes the case", async () => {
    const fetcher = vi.fn((path: string, init?: RequestInit) =>
      ok(
        path.endsWith("/notes") || path.endsWith("/history")
          ? []
          : init?.method === "PATCH"
            ? { ...item, status: "investigating" }
            : item,
      ),
    );
    vi.stubGlobal("fetch", fetcher);
    const changed = vi.fn();
    render(<Detail id={1} user={user} users={[user]} onChange={changed} />);
    await screen.findByText(item.title);
    fireEvent.change(screen.getByLabelText("Status"), {
      target: { value: "investigating" },
    });
    await waitFor(() => expect(changed).toHaveBeenCalled());
    expect(
      fetcher.mock.calls.some(
        ([path, init]) =>
          path === "/api/incidents/1" &&
          init?.method === "PATCH" &&
          init.body === '{"status":"investigating"}',
      ),
    ).toBe(true);
  });
  it("disables all case mutations for viewers", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((path: string) =>
        ok(path.endsWith("/notes") || path.endsWith("/history") ? [] : item),
      ),
    );
    render(
      <Detail
        id={1}
        user={{ ...user, role: "viewer" }}
        users={[user]}
        onChange={vi.fn()}
      />,
    );
    await screen.findByText(item.title);
    expect(screen.getByLabelText("Status")).toBeDisabled();
    expect(
      screen.queryByRole("button", { name: "Add investigation note" }),
    ).not.toBeInTheDocument();
  });
});

it("preserves summary drafts after a rejected mutation", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((path: string, init?: RequestInit) =>
      init?.method === "PATCH"
        ? Promise.resolve({
            ok: false,
            status: 500,
            json: () => Promise.resolve({ detail: "Save failed" }),
          })
        : ok(path.endsWith("/notes") || path.endsWith("/history") ? [] : item),
    ),
  );
  render(<Detail id={1} user={user} users={[user]} onChange={vi.fn()} />);
  await screen.findByText(item.title);
  fireEvent.click(
    screen.getByRole("button", { name: "Edit incident summary" }),
  );
  fireEvent.change(screen.getByLabelText("Title"), {
    target: { value: "Unsaved investigation draft" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Save summary" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Save failed");
  expect(screen.getByLabelText("Title")).toHaveValue(
    "Unsaved investigation draft",
  );
  expect(screen.getByRole("button", { name: "Save summary" })).toBeEnabled();
});
it("limits overview requests to open incidents", async () => {
  const fetcher = vi.fn((_path: string) => ok([item]));
  vi.stubGlobal("fetch", fetcher);
  render(<IncidentList open={vi.fn()} refresh={0} compact />);
  await screen.findByText(item.title);
  expect(fetcher.mock.calls[0][0]).toContain("status=open");
  expect(fetcher.mock.calls[0][0]).toContain("limit=5");
});
