import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api/client";
import { Panel } from "../components/Panel";
import { StatPanel } from "../components/StatPanel";
import { StateMessage } from "../components/StateMessage";
import type { AnnouncementOut, CompetitionOut, EventOut, LeaderboardOut } from "../types";

export function Dashboard() {
  const [leaderboard, setLeaderboard] = useState<LeaderboardOut | null>(null);
  const [announcements, setAnnouncements] = useState<AnnouncementOut[]>([]);
  const [competitions, setCompetitions] = useState<CompetitionOut[]>([]);
  const [events, setEvents] = useState<EventOut[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      api.getLeaderboard(undefined, 5),
      api.listAnnouncements(3),
      api.listCompetitions(),
      api.listEvents(3),
    ])
      .then(([lb, ann, comps, evs]) => {
        setLeaderboard(lb);
        setAnnouncements(ann);
        setCompetitions(comps);
        setEvents(evs);
      })
      .catch((e) => setError(e.message));
  }, []);

  const leader = leaderboard?.entries[0];
  const openCompetitions = competitions.filter((c) => c.status === "open").length;

  const chartData = (leaderboard?.entries ?? []).map((entry) => ({
    name: entry.user.display_name,
    points: entry.points,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl text-ivory">Good to see you</h1>
        <p className="mt-1 text-sm text-muted">Here's where things stand.</p>
      </div>

      {error && <StateMessage kind="error">{error}</StateMessage>}

      {/* Asymmetric hero: one large "leader" panel + a stacked column of stats,
          rather than three identical cards. */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Panel title="Current leader" className="lg:col-span-2 rise-in">
          {leader ? (
            <div className="flex items-baseline gap-4">
              <span className="font-display text-5xl text-murasaki">{leader.points}</span>
              <div>
                <div className="text-ivory text-lg">{leader.user.display_name}</div>
                <div className="text-xs text-muted">points in {leaderboard?.competition}</div>
              </div>
            </div>
          ) : (
            <StateMessage kind="empty">No scores recorded yet.</StateMessage>
          )}
        </Panel>

        <div className="grid grid-cols-2 lg:grid-cols-1 gap-4">
          <StatPanel value={openCompetitions} label="Open competitions" />
          <StatPanel value={events.length} label="Upcoming events" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Panel title="Top 5">
          {chartData.length > 0 ? (
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 16 }}>
                  <CartesianGrid horizontal={false} stroke="#2A2E3A" />
                  <XAxis type="number" hide />
                  <YAxis
                    type="category"
                    dataKey="name"
                    width={90}
                    tick={{ fill: "#8A8FA6", fontSize: 12 }}
                    axisLine={{ stroke: "#2A2E3A" }}
                    tickLine={false}
                  />
                  <Tooltip
                    cursor={{ fill: "#1D212B" }}
                    contentStyle={{
                      background: "#171A22",
                      border: "1.5px solid #2A2E3A",
                      borderRadius: 3,
                      color: "#ECE9F5",
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="points" fill="#7C6FE0" radius={[0, 3, 3, 0]} barSize={16} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <StateMessage kind="empty">Nothing to rank yet — award some points.</StateMessage>
          )}
        </Panel>

        <Panel title="Latest announcements">
          {announcements.length > 0 ? (
            <ul className="space-y-3">
              {announcements.map((a) => (
                <li key={a.id} className="text-sm">
                  <div className="text-ivory">{a.title}</div>
                  <div className="text-muted text-xs mt-0.5 line-clamp-2">{a.message}</div>
                </li>
              ))}
            </ul>
          ) : (
            <StateMessage kind="empty">
              No announcements logged yet — post one with /announce in Discord.
            </StateMessage>
          )}
        </Panel>
      </div>
    </div>
  );
}
