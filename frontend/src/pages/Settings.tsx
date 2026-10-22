import { useState } from "react";
import { api, ApiError } from "../api/client";
import { Panel } from "../components/Panel";
import { StateMessage } from "../components/StateMessage";
import { useAuth } from "../hooks/useAuth";

export function Settings() {
  const { user, isLoggedIn, isCommittee, login, logout } = useAuth();
  const [newCompName, setNewCompName] = useState("");
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState("");
  const [resetting, setResetting] = useState(false);

  async function handleReset(e: React.FormEvent) {
    e.preventDefault();
    if (!newCompName.trim()) return;
    setResetting(true);
    setError("");
    setFeedback("");
    try {
      const comp = await api.resetLeaderboard(newCompName.trim());
      setFeedback(`Started a new leaderboard: ${comp.name}.`);
      setNewCompName("");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't reset the leaderboard.");
    } finally {
      setResetting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl text-ivory">Settings</h1>
        <p className="mt-1 text-sm text-muted">Dashboard configuration for this browser.</p>
      </div>

      {feedback && <StateMessage kind="empty">{feedback}</StateMessage>}
      {error && <StateMessage kind="error">{error}</StateMessage>}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Panel title="Account">
          {isLoggedIn && user ? (
            <div className="space-y-3">
              <div className="text-sm">
                <div className="text-ivory">{user.display_name}</div>
                <div className="text-muted text-xs mt-0.5">
                  {isCommittee ? "Committee member" : "General member"} · Discord ID {user.discord_id}
                </div>
              </div>
              <button
                onClick={logout}
                className="border border-rule hover:border-hanko hover:text-hanko transition-colors text-ivory text-sm px-4 py-2 rounded-panel"
              >
                Log out
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-muted">
                Log in with Discord to manage points and announcements. Committee actions
                are unlocked automatically if your Discord roles match the society's
                committee roles.
              </p>
              <button
                onClick={login}
                className="bg-murasaki hover:bg-murasaki-soft transition-colors text-ivory text-sm px-4 py-2 rounded-panel"
              >
                Log in with Discord
              </button>
            </div>
          )}
        </Panel>

        <Panel title="Start a new leaderboard">
          <p className="text-sm text-muted mb-3">
            Closes the current competition (recording its winner) and opens a fresh one.
            Committee only.
          </p>
          <form onSubmit={handleReset} className="flex gap-2">
            <input
              value={newCompName}
              onChange={(e) => setNewCompName(e.target.value)}
              placeholder="e.g. Fresher Week"
              disabled={!isCommittee}
              className="flex-1 bg-ink border border-rule rounded-panel px-3 py-2 text-sm text-ivory placeholder:text-muted/50 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={resetting || !isCommittee}
              className="border border-rule hover:border-hanko hover:text-hanko transition-colors text-ivory text-sm px-4 py-2 rounded-panel disabled:opacity-50"
            >
              {resetting ? "Resetting…" : "Reset"}
            </button>
          </form>
        </Panel>
      </div>
    </div>
  );
}
