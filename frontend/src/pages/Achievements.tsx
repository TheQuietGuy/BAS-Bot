import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import { Panel } from "../components/Panel";
import { MemberPicker } from "../components/MemberPicker";
import type { PickedMember } from "../components/MemberPicker";
import { StateMessage } from "../components/StateMessage";
import { useAuth } from "../hooks/useAuth";
import { useConfirm } from "../hooks/useConfirm";
import type { AchievementOut } from "../types";

export function Achievements() {
  const { user, isCommittee } = useAuth();
  const { confirm, dialog } = useConfirm();
  const [member, setMember] = useState<PickedMember | null>(null);
  const [achievements, setAchievements] = useState<AchievementOut[]>([]);
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState("");

  const [newKey, setNewKey] = useState("");
  const [newName, setNewName] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newEmoji, setNewEmoji] = useState("🏆");

  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editEmoji, setEditEmoji] = useState("");

  const load = (discordId?: number) => {
    api
      .listAchievements(discordId)
      .then(setAchievements)
      .catch((e) => setError(e.message));
  };

  useEffect(() => {
    load(user?.discord_id);
    if (user) {
      setMember({ discord_id: user.discord_id, username: user.username, display_name: user.display_name });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  function currentLookup(): number | undefined {
    return member?.discord_id;
  }

  function pickMember(m: PickedMember | null) {
    setMember(m);
    if (m) load(m.discord_id);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setFeedback("");
    if (!newKey || !newName || !newDescription) {
      setError("Key, name, and description are required.");
      return;
    }
    try {
      await api.createAchievement({ key: newKey, name: newName, description: newDescription, emoji: newEmoji });
      setNewKey("");
      setNewName("");
      setNewDescription("");
      setNewEmoji("🏆");
      load(currentLookup());
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't create that achievement.");
    }
  }

  function startEdit(a: AchievementOut) {
    setEditingKey(a.key);
    setEditName(a.name);
    setEditDescription(a.description);
    setEditEmoji(a.emoji);
  }

  async function saveEdit(key: string) {
    try {
      await api.editAchievement(key, { name: editName, description: editDescription, emoji: editEmoji });
      setEditingKey(null);
      load(currentLookup());
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't update that achievement.");
    }
  }

  async function handleDelete(key: string) {
    const name = achievements.find((a) => a.key === key)?.name ?? key;
    const ok = await confirm({
      title: `Delete the ${name} badge?`,
      body: "Every member who earned it loses it too. It can't be undone.",
      confirmLabel: "Delete badge",
    });
    if (!ok) return;
    try {
      await api.deleteAchievement(key);
      load(currentLookup());
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't delete that achievement.");
    }
  }

  async function handleAward(key: string) {
    if (!member) {
      setError("Choose a member above first.");
      return;
    }
    try {
      await api.awardAchievement(key, {
        discord_id: member.discord_id,
        username: member.username,
        display_name: member.display_name,
      });
      setFeedback(`Awarded ${achievements.find((a) => a.key === key)?.name ?? key} to ${member.display_name}.`);
      load(member.discord_id);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't award that achievement.");
    }
  }

  async function handleRevoke(key: string) {
    if (!member) {
      setError("Choose a member above first.");
      return;
    }
    try {
      await api.revokeAchievement(key, member.discord_id);
      setFeedback(`Revoked ${achievements.find((a) => a.key === key)?.name ?? key} from ${member.display_name}.`);
      load(member.discord_id);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't revoke that achievement.");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl text-ivory">Achievements</h1>
        <p className="mt-1 text-sm text-muted">Badges earned across every competition.</p>
      </div>

      <Panel title="Viewing badges for">
        <MemberPicker key={user?.discord_id ?? "anon"} value={member} onChange={pickMember} />
        {isCommittee && (
          <p className="mt-2 text-xs text-muted">
            Award and revoke below apply to this member.
          </p>
        )}
      </Panel>

      {error && <StateMessage kind="error">{error}</StateMessage>}
      {feedback && <StateMessage kind="empty">{feedback}</StateMessage>}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {achievements.map((a) => (
          <div key={a.key} className={`panel p-5 text-center ${a.earned ? "" : "opacity-40"}`}>
            {editingKey === a.key ? (
              <div className="space-y-2 text-left">
                <input
                  value={editEmoji}
                  onChange={(e) => setEditEmoji(e.target.value)}
                  className="w-full bg-ink border border-rule rounded-panel px-2 py-1 text-sm text-ivory text-center"
                />
                <input
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="w-full bg-ink border border-rule rounded-panel px-2 py-1 text-sm text-ivory"
                />
                <textarea
                  value={editDescription}
                  onChange={(e) => setEditDescription(e.target.value)}
                  rows={2}
                  className="w-full bg-ink border border-rule rounded-panel px-2 py-1 text-sm text-ivory resize-none"
                />
                <div className="flex gap-2 justify-center">
                  <button onClick={() => saveEdit(a.key)} className="text-xs text-murasaki hover:underline">
                    Save
                  </button>
                  <button onClick={() => setEditingKey(null)} className="text-xs text-muted hover:text-ivory">
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="text-4xl">{a.emoji}</div>
                <div className="mt-2 font-display text-lg text-ivory">{a.name}</div>
                <div className="mt-1 text-xs text-muted">{a.description}</div>
                <div className="mt-3 text-xs">
                  {a.earned ? (
                    <span className="text-murasaki">Earned</span>
                  ) : (
                    <span className="text-muted">Locked</span>
                  )}
                </div>
                {isCommittee && (
                  <div className="mt-3 flex flex-wrap gap-2 justify-center text-xs">
                    <button onClick={() => handleAward(a.key)} className="text-murasaki hover:underline">
                      Award
                    </button>
                    <button onClick={() => handleRevoke(a.key)} className="text-muted hover:text-ivory">
                      Revoke
                    </button>
                    <button onClick={() => startEdit(a)} className="text-muted hover:text-ivory">
                      Edit
                    </button>
                    <button onClick={() => handleDelete(a.key)} className="text-hanko hover:underline">
                      Delete
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        ))}
      </div>

      {isCommittee && (
        <Panel title="Create a custom achievement">
          <form onSubmit={handleCreate} className="grid grid-cols-1 sm:grid-cols-4 gap-2 items-end">
            <div className="sm:col-span-1">
              <label className="block text-xs text-muted mb-1">Emoji</label>
              <input
                value={newEmoji}
                onChange={(e) => setNewEmoji(e.target.value)}
                className="w-full bg-ink border border-rule rounded-panel px-3 py-2 text-sm text-ivory"
              />
            </div>
            <div className="sm:col-span-1">
              <label className="block text-xs text-muted mb-1">Key</label>
              <input
                value={newKey}
                onChange={(e) => setNewKey(e.target.value)}
                placeholder="night_owl"
                className="w-full bg-ink border border-rule rounded-panel px-3 py-2 text-sm text-ivory placeholder:text-muted/50"
              />
            </div>
            <div className="sm:col-span-1">
              <label className="block text-xs text-muted mb-1">Name</label>
              <input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Night Owl"
                className="w-full bg-ink border border-rule rounded-panel px-3 py-2 text-sm text-ivory placeholder:text-muted/50"
              />
            </div>
            <div className="sm:col-span-1">
              <label className="block text-xs text-muted mb-1">Description</label>
              <input
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
                placeholder="Active after midnight"
                className="w-full bg-ink border border-rule rounded-panel px-3 py-2 text-sm text-ivory placeholder:text-muted/50"
              />
            </div>
            <div className="sm:col-span-4">
              <button
                type="submit"
                className="bg-murasaki hover:bg-murasaki-soft transition-colors text-ivory text-sm px-4 py-2 rounded-panel"
              >
                Create
              </button>
            </div>
          </form>
        </Panel>
      )}
      {dialog}
    </div>
  );
}
