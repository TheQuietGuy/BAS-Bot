import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import { Panel } from "../components/Panel";
import { MemberPicker } from "../components/MemberPicker";
import type { PickedMember } from "../components/MemberPicker";
import { StateMessage } from "../components/StateMessage";
import { useConfirm } from "../hooks/useConfirm";
import { useAuth } from "../hooks/useAuth";
import type { CompetitionOut, LeaderboardOut, ScoreOut } from "../types";

const MEDALS = ["🥇", "🥈", "🥉"];

export function Leaderboard() {
  const { isCommittee } = useAuth();
  const { confirm, dialog } = useConfirm();
  const [leaderboard, setLeaderboard] = useState<LeaderboardOut | null>(null);
  const [competitions, setCompetitions] = useState<CompetitionOut[]>([]);
  const [scores, setScores] = useState<ScoreOut[]>([]);
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState("");

  const [member, setMember] = useState<PickedMember | null>(null);
  const [pickerKey, setPickerKey] = useState(0); // bump to clear the picker after saving
  const [amount, setAmount] = useState("");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [newCompName, setNewCompName] = useState("");
  const [editingCompId, setEditingCompId] = useState<number | null>(null);
  const [compDraft, setCompDraft] = useState("");

  const [editingScoreId, setEditingScoreId] = useState<number | null>(null);
  const [scoreDraftPoints, setScoreDraftPoints] = useState("");
  const [scoreDraftReason, setScoreDraftReason] = useState("");

  const load = () => {
    api.getLeaderboard(undefined, 15).then(setLeaderboard).catch((e) => setError(e.message));
    api.listCompetitions().then(setCompetitions).catch((e) => setError(e.message));
    api.listScores().then(setScores).catch((e) => setError(e.message));
  };

  useEffect(load, []);

  async function handleAdjust(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setFeedback("");
    const amountNum = Number(amount);
    if (!member) {
      setError("Choose a member first.");
      return;
    }
    if (!amountNum) {
      setError("Enter a points amount other than 0. Use a negative number to remove points.");
      return;
    }
    setSubmitting(true);
    try {
      const result = await api.adjustPoints({
        discord_id: member.discord_id,
        username: member.username,
        display_name: member.display_name,
        amount: amountNum,
        reason,
      });
      setFeedback(`${member.display_name} now has ${result.new_total} points in ${result.competition}.`);
      setMember(null);
      setPickerKey((k) => k + 1);
      setAmount("");
      setReason("");
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCreateCompetition(e: React.FormEvent) {
    e.preventDefault();
    if (!newCompName.trim()) return;
    try {
      await api.createCompetition({ name: newCompName.trim() });
      setNewCompName("");
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't create that competition.");
    }
  }

  function startEditComp(comp: CompetitionOut) {
    setEditingCompId(comp.id);
    setCompDraft(comp.name);
  }

  async function saveComp(id: number) {
    try {
      await api.editCompetition(id, { name: compDraft });
      setEditingCompId(null);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't rename that competition.");
    }
  }

  async function handleDeleteComp(id: number) {
    const name = competitions.find((c) => c.id === id)?.name ?? "this competition";
    const ok = await confirm({
      title: `Delete ${name}?`,
      body: "This also deletes every score logged under it. It can't be undone.",
      confirmLabel: "Delete competition",
    });
    if (!ok) return;
    try {
      await api.deleteCompetition(id);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't delete that competition.");
    }
  }

  async function toggleCompStatus(comp: CompetitionOut) {
    try {
      await api.editCompetition(comp.id, { status: comp.status === "open" ? "closed" : "open" });
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't update that competition's status.");
    }
  }

  function startEditScore(score: ScoreOut) {
    setEditingScoreId(score.id);
    setScoreDraftPoints(String(score.points));
    setScoreDraftReason(score.reason);
  }

  async function saveScore(id: number) {
    try {
      await api.editScore(id, { points: Number(scoreDraftPoints), reason: scoreDraftReason });
      setEditingScoreId(null);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't update that score entry.");
    }
  }

  async function handleDeleteScore(id: number) {
    const entry = scores.find((s) => s.id === id);
    const ok = await confirm({
      title: "Delete this score entry?",
      body: entry
        ? `${entry.user_display_name}'s ${entry.points} points will be removed and the leaderboard will change.`
        : "The leaderboard will change. This can't be undone.",
      confirmLabel: "Delete entry",
    });
    if (!ok) return;
    try {
      await api.deleteScore(id);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't delete that score entry.");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl text-ivory">Leaderboard</h1>
        <p className="mt-1 text-sm text-muted">{leaderboard?.competition ?? "Loading…"}</p>
      </div>

      {error && <StateMessage kind="error">{error}</StateMessage>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Panel title="Standings" className="lg:col-span-2">
          {leaderboard && leaderboard.entries.length > 0 ? (
            <ol className="space-y-1">
              {leaderboard.entries.map((entry, i) => (
                <li
                  key={entry.user.discord_id}
                  className="flex items-center justify-between text-sm py-2 border-b border-rule last:border-0"
                >
                  <span className="text-ivory flex items-center gap-2">
                    <span className="w-6 text-center">
                      {i < 3 ? MEDALS[i] : <span className="font-mono text-muted">{i + 1}</span>}
                    </span>
                    {entry.user.display_name}
                  </span>
                  <span className="font-mono text-murasaki">{entry.points} pts</span>
                </li>
              ))}
            </ol>
          ) : (
            <StateMessage kind="empty">No scores yet.</StateMessage>
          )}
        </Panel>

        <Panel title="Award or remove points">
          {!isCommittee ? (
            <StateMessage kind="empty">
              Log in with a committee Discord account to manage points.
            </StateMessage>
          ) : (
            <form onSubmit={handleAdjust} className="space-y-3">
              <div>
                <label className="block text-xs text-muted mb-1">Member</label>
                <MemberPicker key={pickerKey} value={member} onChange={setMember} />
              </div>
              <div>
                <label className="block text-xs text-muted mb-1">
                  Amount (negative to remove)
                </label>
                <input
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="50"
                  inputMode="numeric"
                  className="w-full bg-ink border border-rule rounded-panel px-3 py-2 text-sm text-ivory placeholder:text-muted/50"
                />
              </div>
              <div>
                <label className="block text-xs text-muted mb-1">Reason (optional)</label>
                <input
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Quiz night win"
                  className="w-full bg-ink border border-rule rounded-panel px-3 py-2 text-sm text-ivory placeholder:text-muted/50"
                />
              </div>
              {feedback && <StateMessage kind="empty">{feedback}</StateMessage>}
              <button
                type="submit"
                disabled={submitting}
                className="w-full bg-murasaki hover:bg-murasaki-soft transition-colors text-ivory text-sm py-2 rounded-panel disabled:opacity-50"
              >
                {submitting ? "Saving…" : "Update points"}
              </button>
            </form>
          )}
        </Panel>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Panel title="Competitions">
          <ul className="space-y-2 mb-3">
            {competitions.map((c) => (
              <li key={c.id} className="flex items-center justify-between text-sm py-1.5 border-b border-rule last:border-0">
                {editingCompId === c.id ? (
                  <input
                    value={compDraft}
                    onChange={(e) => setCompDraft(e.target.value)}
                    className="bg-ink border border-rule rounded-panel px-2 py-1 text-sm text-ivory flex-1 mr-2"
                    autoFocus
                  />
                ) : (
                  <span className="text-ivory">
                    {c.name}{" "}
                    <span className="text-xs text-muted">
                      ({c.status})
                    </span>
                  </span>
                )}
                {isCommittee && (
                  <span className="flex gap-2 text-xs shrink-0">
                    {editingCompId === c.id ? (
                      <button onClick={() => saveComp(c.id)} className="text-murasaki hover:underline">
                        Save
                      </button>
                    ) : (
                      <button onClick={() => startEditComp(c)} className="text-muted hover:text-ivory">
                        Rename
                      </button>
                    )}
                    <button onClick={() => toggleCompStatus(c)} className="text-ai hover:underline">
                      {c.status === "open" ? "Close" : "Reopen"}
                    </button>
                    <button onClick={() => handleDeleteComp(c.id)} className="text-hanko hover:underline">
                      Delete
                    </button>
                  </span>
                )}
              </li>
            ))}
          </ul>
          {isCommittee && (
            <form onSubmit={handleCreateCompetition} className="flex gap-2">
              <input
                value={newCompName}
                onChange={(e) => setNewCompName(e.target.value)}
                placeholder="New competition name"
                className="flex-1 bg-ink border border-rule rounded-panel px-3 py-2 text-sm text-ivory placeholder:text-muted/50"
              />
              <button
                type="submit"
                className="bg-murasaki hover:bg-murasaki-soft transition-colors text-ivory text-sm px-4 py-2 rounded-panel"
              >
                Add
              </button>
            </form>
          )}
        </Panel>

        <Panel title="Recent score entries">
          {scores.length > 0 ? (
            <ul className="space-y-2">
              {scores.map((s) => (
                <li key={s.id} className="text-sm py-1.5 border-b border-rule last:border-0">
                  {editingScoreId === s.id ? (
                    <div className="flex gap-2 items-center">
                      <input
                        value={scoreDraftPoints}
                        onChange={(e) => setScoreDraftPoints(e.target.value)}
                        inputMode="numeric"
                        className="w-16 bg-ink border border-rule rounded-panel px-2 py-1 text-sm text-ivory"
                      />
                      <input
                        value={scoreDraftReason}
                        onChange={(e) => setScoreDraftReason(e.target.value)}
                        className="flex-1 bg-ink border border-rule rounded-panel px-2 py-1 text-sm text-ivory"
                      />
                      <button onClick={() => saveScore(s.id)} className="text-xs text-murasaki hover:underline shrink-0">
                        Save
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between">
                      <span className="text-ivory">
                        {s.user_display_name}
                        <span className="text-muted text-xs"> · {s.competition_name}</span>
                        <span className="text-muted"> — {s.reason || "no reason"}</span>
                      </span>
                      <span className="flex items-center gap-2 shrink-0">
                        <span className="font-mono text-murasaki">{s.points}</span>
                        {isCommittee && (
                          <>
                            <button onClick={() => startEditScore(s)} className="text-xs text-muted hover:text-ivory">
                              Edit
                            </button>
                            <button onClick={() => handleDeleteScore(s.id)} className="text-xs text-hanko hover:underline">
                              Delete
                            </button>
                          </>
                        )}
                      </span>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <StateMessage kind="empty">No score entries yet.</StateMessage>
          )}
        </Panel>
      </div>
      {dialog}
    </div>
  );
}
