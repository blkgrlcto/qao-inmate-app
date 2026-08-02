"use client";

import { useEffect, useState } from "react";
import type { AdminUser, ShareRow } from "@/lib/api";
import * as api from "@/lib/api";

const ROLES = ["attorney", "paralegal", "inmate", "admin"];

export default function AdminPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [userError, setUserError] = useState("");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState("attorney");
  const [creatingUser, setCreatingUser] = useState(false);

  const [revokingId, setRevokingId] = useState<string | null>(null);
  const [revokeMessage, setRevokeMessage] = useState("");

  const [shareCaseId, setShareCaseId] = useState("");
  const [shareUserId, setShareUserId] = useState("");
  const [shareRole, setShareRole] = useState("viewer");
  const [shares, setShares] = useState<ShareRow[]>([]);
  const [shareError, setShareError] = useState("");
  const [creatingShare, setCreatingShare] = useState(false);

  function loadUsers() {
    setLoadingUsers(true);
    api
      .adminListUsers()
      .then(setUsers)
      .catch((e) => setUserError(e instanceof Error ? e.message : "Failed to load users"))
      .finally(() => setLoadingUsers(false));
  }

  useEffect(loadUsers, []);

  async function handleCreateUser(e: React.FormEvent) {
    e.preventDefault();
    setCreatingUser(true);
    setUserError("");
    try {
      await api.adminCreateUser({ email, password, full_name: fullName, role });
      setEmail("");
      setPassword("");
      setFullName("");
      setRole("attorney");
      loadUsers();
    } catch (err) {
      setUserError(err instanceof Error ? err.message : "Failed to create user");
    } finally {
      setCreatingUser(false);
    }
  }

  async function handleRevoke(userId: string) {
    setRevokingId(userId);
    setRevokeMessage("");
    try {
      await api.adminRevokeUserSessions(userId);
      setRevokeMessage("Sessions revoked — that user will need to log in again.");
    } catch (err) {
      setRevokeMessage(err instanceof Error ? err.message : "Failed to revoke sessions");
    } finally {
      setRevokingId(null);
    }
  }

  function loadShares(caseId: string) {
    if (!caseId.trim()) return;
    api
      .adminListShares(caseId.trim())
      .then(setShares)
      .catch((e) => setShareError(e instanceof Error ? e.message : "Failed to load shares"));
  }

  async function handleCreateShare(e: React.FormEvent) {
    e.preventDefault();
    setCreatingShare(true);
    setShareError("");
    try {
      await api.adminCreateShare({
        case_id: shareCaseId.trim(),
        user_id: shareUserId.trim(),
        role: shareRole,
      });
      setShareUserId("");
      loadShares(shareCaseId);
    } catch (err) {
      setShareError(err instanceof Error ? err.message : "Failed to grant access");
    } finally {
      setCreatingShare(false);
    }
  }

  return (
    <div className="p-6">
      <h1 className="mb-6 text-xl font-semibold">Admin</h1>

      <section className="mb-10">
        <h2 className="mb-3 text-lg font-medium">Users</h2>

        <form
          onSubmit={handleCreateUser}
          className="mb-4 flex flex-wrap items-end gap-3 rounded border border-gray-200 p-4"
        >
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="rounded border border-gray-300 px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="rounded border border-gray-300 px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Full name</label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="rounded border border-gray-300 px-3 py-2"
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Role</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="rounded border border-gray-300 px-3 py-2"
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            disabled={creatingUser}
            className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {creatingUser ? "Creating…" : "Create user"}
          </button>
        </form>

        {userError && <p className="mb-2 text-red-600">{userError}</p>}

        {loadingUsers ? (
          <p className="text-gray-500">Loading…</p>
        ) : (
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-gray-500">
                <th className="py-2 pr-4">Email</th>
                <th className="py-2 pr-4">Name</th>
                <th className="py-2 pr-4">Role</th>
                <th className="py-2 pr-4">ID</th>
                <th className="py-2 pr-4"></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-gray-100">
                  <td className="py-2 pr-4">{u.email}</td>
                  <td className="py-2 pr-4">{u.full_name}</td>
                  <td className="py-2 pr-4">{u.role}</td>
                  <td className="py-2 pr-4 font-mono text-xs text-gray-400">{u.id}</td>
                  <td className="py-2 pr-4">
                    <button
                      onClick={() => handleRevoke(u.id)}
                      disabled={revokingId === u.id}
                      className="rounded border border-red-300 px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
                    >
                      {revokingId === u.id ? "Revoking…" : "Revoke sessions"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {revokeMessage && <p className="mt-2 text-sm text-gray-500">{revokeMessage}</p>}
      </section>

      <section>
        <h2 className="mb-3 text-lg font-medium">Case access</h2>
        <p className="mb-3 text-sm text-gray-500">
          Grant a user access to a case, or look up who already has access. Copy IDs from the
          table above and the Cases list.
        </p>

        <form
          onSubmit={handleCreateShare}
          className="mb-4 flex flex-wrap items-end gap-3 rounded border border-gray-200 p-4"
        >
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Case ID</label>
            <input
              type="text"
              value={shareCaseId}
              onChange={(e) => setShareCaseId(e.target.value)}
              onBlur={() => loadShares(shareCaseId)}
              className="w-72 rounded border border-gray-300 px-3 py-2 font-mono text-xs"
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">User ID</label>
            <input
              type="text"
              value={shareUserId}
              onChange={(e) => setShareUserId(e.target.value)}
              className="w-72 rounded border border-gray-300 px-3 py-2 font-mono text-xs"
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Role</label>
            <select
              value={shareRole}
              onChange={(e) => setShareRole(e.target.value)}
              className="rounded border border-gray-300 px-3 py-2"
            >
              <option value="viewer">viewer</option>
              <option value="editor">editor</option>
              <option value="owner">owner</option>
            </select>
          </div>
          <button
            type="submit"
            disabled={creatingShare}
            className="rounded bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {creatingShare ? "Granting…" : "Grant access"}
          </button>
          <button
            type="button"
            onClick={() => loadShares(shareCaseId)}
            className="rounded border border-gray-300 px-4 py-2 hover:bg-gray-50"
          >
            View access for case
          </button>
        </form>

        {shareError && <p className="mb-2 text-red-600">{shareError}</p>}

        {shares.length > 0 && (
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-gray-500">
                <th className="py-2 pr-4">User</th>
                <th className="py-2 pr-4">Email</th>
                <th className="py-2 pr-4">Role</th>
              </tr>
            </thead>
            <tbody>
              {shares.map((s) => (
                <tr key={s.id} className="border-b border-gray-100">
                  <td className="py-2 pr-4">{s.user_full_name}</td>
                  <td className="py-2 pr-4">{s.user_email}</td>
                  <td className="py-2 pr-4">{s.role}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
