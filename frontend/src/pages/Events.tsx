import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import { Panel } from "../components/Panel";
import { ChannelSelect } from "../components/ChannelSelect";
import { StateMessage } from "../components/StateMessage";
import { useConfirm } from "../hooks/useConfirm";
import { useAuth } from "../hooks/useAuth";
import type { EventOut } from "../types";

export function Events() {
  const { isCommittee, user } = useAuth();
  const { confirm, dialog } = useConfirm();
  const [events, setEvents] = useState<EventOut[]>([]);
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [description, setDescription] = useState("");
  const [eventTime, setEventTime] = useState("");
  const [channelId, setChannelId] = useState("");
  const [reminderMinutes, setReminderMinutes] = useState("60");

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [editLocation, setEditLocation] = useState("");
  const [editDescription, setEditDescription] = useState("");

  const load = () => {
    api.listEvents().then(setEvents).catch((e) => setError(e.message));
  };

  useEffect(load, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setFeedback("");
    if (!name || !eventTime || !channelId || !user) {
      setError("Name, time, and channel ID are required.");
      return;
    }
    setSubmitting(true);
    try {
      await api.createEvent({
        name,
        description,
        location,
        event_time: new Date(eventTime).toISOString(),
        channel_id: Number(channelId),
        created_by_discord_id: user.discord_id,
        reminder_minutes_before: Number(reminderMinutes) || 60,
      });
      setFeedback(`Added ${name}.`);
      setName("");
      setLocation("");
      setDescription("");
      setEventTime("");
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't create that event.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: number) {
    const ok = await confirm({
      title: "Remove this event?",
      body: "Members will no longer see it, and its reminder won't be sent.",
      confirmLabel: "Remove event",
    });
    if (!ok) return;
    try {
      await api.deleteEvent(id);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't remove that event.");
    }
  }

  function startEdit(event: EventOut) {
    setEditingId(event.id);
    setEditName(event.name);
    setEditLocation(event.location);
    setEditDescription(event.description);
  }

  async function saveEdit(id: number) {
    try {
      await api.editEvent(id, { name: editName, location: editLocation, description: editDescription });
      setEditingId(null);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't update that event.");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl text-ivory">Events</h1>
        <p className="mt-1 text-sm text-muted">
          The bot posts an automatic reminder in the event's channel before it starts.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Panel title="Upcoming" className="lg:col-span-2">
          {error && <StateMessage kind="error">{error}</StateMessage>}
          {events.length > 0 ? (
            <ul className="space-y-4">
              {events.map((event) => (
                <li key={event.id} className="border-b border-rule pb-4 last:border-0 last:pb-0">
                  {editingId === event.id ? (
                    <div className="space-y-2">
                      <input
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        className="w-full bg-ink border border-rule rounded-panel px-2 py-1 text-sm text-ivory"
                      />
                      <input
                        value={editLocation}
                        onChange={(e) => setEditLocation(e.target.value)}
                        placeholder="Location"
                        className="w-full bg-ink border border-rule rounded-panel px-2 py-1 text-sm text-ivory placeholder:text-muted/50"
                      />
                      <textarea
                        value={editDescription}
                        onChange={(e) => setEditDescription(e.target.value)}
                        rows={2}
                        className="w-full bg-ink border border-rule rounded-panel px-2 py-1 text-sm text-ivory resize-none"
                      />
                      <div className="flex gap-2">
                        <button
                          onClick={() => saveEdit(event.id)}
                          className="text-xs text-murasaki hover:underline"
                        >
                          Save
                        </button>
                        <button
                          onClick={() => setEditingId(null)}
                          className="text-xs text-muted hover:text-ivory"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="flex items-baseline justify-between gap-2">
                        <span className="text-ivory">{event.name}</span>
                        {isCommittee && (
                          <span className="flex gap-2 text-xs shrink-0">
                            <button
                              onClick={() => startEdit(event)}
                              className="text-muted hover:text-ivory"
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => handleDelete(event.id)}
                              className="text-hanko hover:underline"
                            >
                              Remove
                            </button>
                          </span>
                        )}
                      </div>
                      <p className="mt-1 text-xs text-muted">
                        {new Date(event.event_time).toLocaleString()}
                        {event.location && ` · ${event.location}`}
                      </p>
                      {event.description && (
                        <p className="mt-1 text-sm text-muted">{event.description}</p>
                      )}
                    </>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            !error && <StateMessage kind="empty">No upcoming events yet.</StateMessage>
          )}
        </Panel>

        <Panel title="Add an event">
          {!isCommittee ? (
            <StateMessage kind="empty">
              Log in with a committee Discord account to add events.
            </StateMessage>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-3">
              <div>
                <label className="block text-xs text-muted mb-1">Name</label>
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-ink border border-rule rounded-panel px-3 py-2 text-sm text-ivory"
                />
              </div>
              <div>
                <label className="block text-xs text-muted mb-1">When</label>
                <input
                  type="datetime-local"
                  value={eventTime}
                  onChange={(e) => setEventTime(e.target.value)}
                  className="w-full bg-ink border border-rule rounded-panel px-3 py-2 text-sm text-ivory"
                />
              </div>
              <div>
                <label className="block text-xs text-muted mb-1">Location</label>
                <input
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="Lecture Centre"
                  className="w-full bg-ink border border-rule rounded-panel px-3 py-2 text-sm text-ivory placeholder:text-muted/50"
                />
              </div>
              <div>
                <label className="block text-xs text-muted mb-1">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                  className="w-full bg-ink border border-rule rounded-panel px-3 py-2 text-sm text-ivory resize-none"
                />
              </div>
              <div>
                <label className="block text-xs text-muted mb-1">Channel</label>
                <ChannelSelect value={channelId} onChange={setChannelId} />
              </div>
              <div>
                <label className="block text-xs text-muted mb-1">Remind (minutes before)</label>
                <input
                  value={reminderMinutes}
                  onChange={(e) => setReminderMinutes(e.target.value)}
                  inputMode="numeric"
                  className="w-full bg-ink border border-rule rounded-panel px-3 py-2 text-sm text-ivory"
                />
              </div>
              {feedback && <StateMessage kind="empty">{feedback}</StateMessage>}
              <button
                type="submit"
                disabled={submitting}
                className="w-full bg-murasaki hover:bg-murasaki-soft transition-colors text-ivory text-sm py-2 rounded-panel disabled:opacity-50"
              >
                {submitting ? "Saving…" : "Add event"}
              </button>
            </form>
          )}
        </Panel>
      </div>
      {dialog}
    </div>
  );
}
