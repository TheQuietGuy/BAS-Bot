import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import { Panel } from "../components/Panel";
import { StateMessage } from "../components/StateMessage";
import { useAuth } from "../hooks/useAuth";
import type { UserOut } from "../types";

export function Members() {
  const { isCommittee } = useAuth();
  const [users, setUsers] = useState<UserOut[]>([]);
  const [error, setError] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draftName, setDraftName] = useState("");

  const load = () => {
    api.listUsers().then(setUsers).catch((e) => setError(e.message));
  };

  useEffect(load, []);

  function startEdit(user: UserOut) {
    setEditingId(user.id);
    setDraftName(user.display_name);
  }

  async function saveName(id: number) {
    try {
      await api.editUser(id, { display_name: draftName });
      setEditingId(null);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't update that member.");
    }
  }

  async function toggleCommittee(user: UserOut) {
    try {
      await api.editUser(user.id, { is_committee: !user.is_committee });
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't update that member.");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl text-ivory">Members</h1>
        <p className="mt-1 text-sm text-muted">
          Every member the bot has seen. Committee status here is a manual override on top of
          Discord roles — mainly useful for testing.
        </p>
      </div>

      <Panel>
        {error && <StateMessage kind="error">{error}</StateMessage>}
        {users.length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted border-b border-rule">
                <th className="pb-2 font-normal">Name</th>
                <th className="pb-2 font-normal">Discord ID</th>
                <th className="pb-2 font-normal">Committee</th>
                {isCommittee && <th className="pb-2 font-normal"></th>}
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-rule last:border-0">
                  <td className="py-2 text-ivory">
                    {editingId === u.id ? (
                      <input
                        value={draftName}
                        onChange={(e) => setDraftName(e.target.value)}
                        className="bg-ink border border-rule rounded-panel px-2 py-1 text-sm text-ivory w-40"
                        autoFocus
                      />
                    ) : (
                      u.display_name
                    )}
                  </td>
                  <td className="py-2 font-mono text-muted text-xs">{u.discord_id}</td>
                  <td className="py-2">
                    {isCommittee ? (
                      <button
                        onClick={() => toggleCommittee(u)}
                        className={u.is_committee ? "text-murasaki" : "text-muted hover:text-ivory"}
                      >
                        {u.is_committee ? "Yes" : "No"}
                      </button>
                    ) : u.is_committee ? (
                      "Yes"
                    ) : (
                      "No"
                    )}
                  </td>
                  {isCommittee && (
                    <td className="py-2 text-right">
                      {editingId === u.id ? (
                        <button
                          onClick={() => saveName(u.id)}
                          className="text-xs text-murasaki hover:underline"
                        >
                          Save
                        </button>
                      ) : (
                        <button
                          onClick={() => startEdit(u)}
                          className="text-xs text-muted hover:text-ivory"
                        >
                          Rename
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          !error && <StateMessage kind="empty">No members recorded yet.</StateMessage>
        )}
      </Panel>
    </div>
  );
}
