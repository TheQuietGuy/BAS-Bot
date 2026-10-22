import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import { Panel } from "../components/Panel";
import { ChannelSelect } from "../components/ChannelSelect";
import { StateMessage } from "../components/StateMessage";
import { useConfirm } from "../hooks/useConfirm";
import { useAuth } from "../hooks/useAuth";
import type { AnnouncementOut } from "../types";

const STATUS_LABEL: Record<string, string> = {
  posted: "Posted",
  scheduled: "Scheduled",
  cancelled: "Cancelled",
};

function toDatetimeLocalValue(iso: string): string {
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function Announcements() {
  const { isCommittee, user } = useAuth();
  const { confirm, dialog } = useConfirm();
  const [items, setItems] = useState<AnnouncementOut[]>([]);
  const [error, setError] = useState("");
  const [title, setTitle] = useState("");
  const [message, setMessage] = useState("");
  const [channelId, setChannelId] = useState("");
  const [scheduledFor, setScheduledFor] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState("");

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editMessage, setEditMessage] = useState("");
  const [editScheduledFor, setEditScheduledFor] = useState("");

  const load = () => {
    api.listAnnouncements().then(setItems).catch((e) => setError(e.message));
  };

  useEffect(load, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setFeedback("");
    if (!title || !message || !channelId || !user) {
      setError("Fill in every field before logging an announcement.");
      return;
    }
    setSubmitting(true);
    try {
      await api.createAnnouncement({
        title,
        message,
        channel_id: Number(channelId),
        author_discord_id: user.discord_id,
        scheduled_for: scheduledFor ? new Date(scheduledFor).toISOString() : undefined,
      });
      setFeedback(
        scheduledFor
          ? "Scheduled — the bot will post it automatically."
          : "Logged. Post it live with /announce in Discord."
      );
      setTitle("");
      setMessage("");
      setScheduledFor("");
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't log that announcement.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCancel(id: number) {
    const ok = await confirm({
      title: "Cancel this announcement?",
      body: "It won't be posted. You can bring it back later by giving it a new time.",
      confirmLabel: "Cancel announcement",
    });
    if (!ok) return;
    try {
      await api.cancelAnnouncement(id);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't cancel that announcement.");
    }
  }

  function startEdit(a: AnnouncementOut) {
    setEditingId(a.id);
    setEditTitle(a.title);
    setEditMessage(a.message);
    setEditScheduledFor(a.scheduled_for ? toDatetimeLocalValue(a.scheduled_for) : "");
  }

  async function saveEdit(id: number) {
    try {
      await api.editAnnouncement(id, {
        title: editTitle,
        message: editMessage,
        scheduled_for: editScheduledFor ? new Date(editScheduledFor).toISOString() : undefined,
      });
      setEditingId(null);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't update that announcement.");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl text-ivory">Announcements</h1>
        <p className="mt-1 text-sm text-muted">
          Scheduled announcements post automatically. Immediate ones still need{" "}
          <code className="text-ai">/announce</code> in Discord to actually send — this only logs them.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Panel title="History" className="lg:col-span-2">
          {error && <StateMessage kind="error">{error}</StateMessage>}
          {items.length > 0 ? (
            <ul className="space-y-4">
              {items.map((a) => (
                <li key={a.id} className="border-b border-rule pb-4 last:border-0 last:pb-0">
                  {editingId === a.id ? (
                    <div className="space-y-2">
                      <input
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        className="w-full bg-ink border border-rule rounded-panel px-2 py-1 text-sm text-ivory"
                      />
                      <textarea
                        value={editMessage}
                        onChange={(e) => setEditMessage(e.target.value)}
                        rows={3}
                        className="w-full bg-ink border border-rule rounded-panel px-2 py-1 text-sm text-ivory resize-none"
                      />
                      <div>
                        <label className="block text-xs text-muted mb-1">
                          Scheduled for (leave blank if already posted)
                        </label>
                        <input
                          type="datetime-local"
                          value={editScheduledFor}
                          onChange={(e) => setEditScheduledFor(e.target.value)}
                          className="w-full bg-ink border border-rule rounded-panel px-2 py-1 text-sm text-ivory"
                        />
                      </div>
                      <div className="flex gap-2">
                        <button onClick={() => saveEdit(a.id)} className="text-xs text-murasaki hover:underline">
                          Save
                        </button>
                        <button onClick={() => setEditingId(null)} className="text-xs text-muted hover:text-ivory">
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="flex items-baseline justify-between gap-2">
                        <span className="text-ivory">{a.title}</span>
                        <span className="flex items-center gap-2 text-xs text-muted shrink-0">
                          {STATUS_LABEL[a.status] ?? a.status}
                          {isCommittee && (
                            <button onClick={() => startEdit(a)} className="text-muted hover:text-ivory">
                              Edit
                            </button>
                          )}
                          {a.status === "scheduled" && isCommittee && (
                            <button
                              onClick={() => handleCancel(a.id)}
                              className="text-hanko hover:underline"
                            >
                              Cancel
                            </button>
                          )}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-muted">{a.message}</p>
                      {a.scheduled_for && (
                        <p className="mt-1 text-xs text-muted">
                          For {new Date(a.scheduled_for).toLocaleString()}
                        </p>
                      )}
                    </>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            !error && <StateMessage kind="empty">No announcements logged yet.</StateMessage>
          )}
        </Panel>

        <Panel title="Log an announcement">
          {!isCommittee ? (
            <StateMessage kind="empty">
              Log in with a committee Discord account to log announcements.
            </StateMessage>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-3">
              <div>
                <label className="block text-xs text-muted mb-1">Title</label>
                <input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full bg-ink border border-rule rounded-panel px-3 py-2 text-sm text-ivory"
                />
              </div>
              <div>
                <label className="block text-xs text-muted mb-1">Message</label>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  rows={4}
                  className="w-full bg-ink border border-rule rounded-panel px-3 py-2 text-sm text-ivory resize-none"
                />
              </div>
              <div>
                <label className="block text-xs text-muted mb-1">Channel</label>
                <ChannelSelect value={channelId} onChange={setChannelId} />
              </div>
              <div>
                <label className="block text-xs text-muted mb-1">
                  Schedule for (optional, leave blank to post now)
                </label>
                <input
                  type="datetime-local"
                  value={scheduledFor}
                  onChange={(e) => setScheduledFor(e.target.value)}
                  className="w-full bg-ink border border-rule rounded-panel px-3 py-2 text-sm text-ivory"
                />
              </div>
              {feedback && <StateMessage kind="empty">{feedback}</StateMessage>}
              <button
                type="submit"
                disabled={submitting}
                className="w-full bg-murasaki hover:bg-murasaki-soft transition-colors text-ivory text-sm py-2 rounded-panel disabled:opacity-50"
              >
                {submitting ? "Saving…" : scheduledFor ? "Schedule" : "Log announcement"}
              </button>
            </form>
          )}
        </Panel>
      </div>
      {dialog}
    </div>
  );
}
