import type {
  AchievementOut,
  AnimeOut,
  AnnouncementOut,
  CompetitionOut,
  CurrentUserOut,
  DiscordChannel,
  DiscordMember,
  EventOut,
  LeaderboardOut,
  ScoreOut,
  UserOut,
} from "../types";

const BASE_URL = "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

const SESSION_TOKEN_KEY = "bas-dashboard-session-token";

export function getStoredApiKey(): string {
  return localStorage.getItem(SESSION_TOKEN_KEY) ?? "";
}

export function setStoredApiKey(key: string) {
  localStorage.setItem(SESSION_TOKEN_KEY, key);
}

export function clearStoredApiKey() {
  localStorage.removeItem(SESSION_TOKEN_KEY);
}

export function discordLoginUrl(): string {
  return `${BASE_URL}/api/auth/login`;
}

async function request<T>(
  path: string,
  options: RequestInit & { auth?: boolean } = {}
): Promise<T> {
  const { auth, headers, ...rest } = options;
  const finalHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...(headers as Record<string, string>),
  };

  if (auth) {
    const key = getStoredApiKey();
    if (key) finalHeaders["Authorization"] = `Bearer ${key}`;
  }

  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, { ...rest, headers: finalHeaders });
  } catch {
    throw new ApiError(0, "Can't reach the BAS Bot API. Is it running on localhost:8000?");
  }

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // response wasn't JSON -- keep the status text
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/api/health"),

  getLeaderboard: (competition?: string, limit = 10) => {
    const params = new URLSearchParams();
    if (competition) params.set("competition", competition);
    params.set("limit", String(limit));
    return request<LeaderboardOut>(`/api/leaderboard?${params}`);
  },

  listCompetitions: () => request<CompetitionOut[]>("/api/leaderboard/competitions"),

  adjustPoints: (body: {
    discord_id: number;
    username: string;
    display_name: string;
    amount: number;
    reason?: string;
    competition_name?: string;
  }) =>
    request<{ discord_id: number; new_total: number; competition: string }>(
      "/api/leaderboard/points",
      { method: "POST", body: JSON.stringify(body), auth: true }
    ),

  resetLeaderboard: (newName: string) =>
    request<CompetitionOut>(`/api/leaderboard/reset?new_name=${encodeURIComponent(newName)}`, {
      method: "POST",
      auth: true,
    }),

  searchAnime: (q: string) => request<AnimeOut>(`/api/anime/search?q=${encodeURIComponent(q)}`),

  randomAnime: () => request<AnimeOut>("/api/anime/random"),

  topAnime: (limit = 5) => request<AnimeOut[]>(`/api/anime/top?limit=${limit}`),

  listAnnouncements: (limit = 20) =>
    request<AnnouncementOut[]>(`/api/announcements?limit=${limit}`),

  createAnnouncement: (body: {
    title: string;
    message: string;
    author_discord_id: number;
    channel_id: number;
    scheduled_for?: string;
  }) =>
    request<AnnouncementOut>("/api/announcements", {
      method: "POST",
      body: JSON.stringify(body),
      auth: true,
    }),

  editAnnouncement: (id: number, body: { title?: string; message?: string; scheduled_for?: string }) =>
    request<AnnouncementOut>(`/api/announcements/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
      auth: true,
    }),

  cancelAnnouncement: (id: number) =>
    request<{ cancelled: number }>(`/api/announcements/${id}`, { method: "DELETE", auth: true }),

  getMe: () => request<CurrentUserOut>("/api/auth/me", { auth: true }),

  listEvents: (limit = 10) => request<EventOut[]>(`/api/events?limit=${limit}`),

  createEvent: (body: {
    name: string;
    description?: string;
    location?: string;
    event_time: string;
    channel_id: number;
    created_by_discord_id: number;
    reminder_minutes_before?: number;
  }) => request<EventOut>("/api/events", { method: "POST", body: JSON.stringify(body), auth: true }),

  editEvent: (
    id: number,
    body: {
      name?: string;
      description?: string;
      location?: string;
      event_time?: string;
      reminder_minutes_before?: number;
    }
  ) => request<EventOut>(`/api/events/${id}`, { method: "PATCH", body: JSON.stringify(body), auth: true }),

  deleteEvent: (id: number) =>
    request<{ deleted: number }>(`/api/events/${id}`, { method: "DELETE", auth: true }),

  listAchievements: (discordId?: number) => {
    const params = discordId ? `?discord_id=${discordId}` : "";
    return request<AchievementOut[]>(`/api/achievements${params}`);
  },

  createAchievement: (body: { key: string; name: string; description: string; emoji?: string }) =>
    request<AchievementOut>("/api/achievements", { method: "POST", body: JSON.stringify(body), auth: true }),

  editAchievement: (key: string, body: { name?: string; description?: string; emoji?: string }) =>
    request<AchievementOut>(`/api/achievements/${key}`, {
      method: "PATCH",
      body: JSON.stringify(body),
      auth: true,
    }),

  deleteAchievement: (key: string) =>
    request<{ deleted: string }>(`/api/achievements/${key}`, { method: "DELETE", auth: true }),

  awardAchievement: (
    key: string,
    body: { discord_id: number; username: string; display_name: string }
  ) =>
    request<{ discord_id: number; achievement: string; newly_awarded: boolean }>(
      `/api/achievements/${key}/award`,
      { method: "POST", body: JSON.stringify(body), auth: true }
    ),

  revokeAchievement: (key: string, discordId: number) =>
    request<{ discord_id: number; achievement: string; revoked: boolean }>(
      `/api/achievements/${key}/award/${discordId}`,
      { method: "DELETE", auth: true }
    ),

  // ---- Discord directory (for pickers) ----
  listDiscordChannels: () => request<DiscordChannel[]>("/api/discord/channels"),
  listDiscordMembers: () => request<DiscordMember[]>("/api/discord/members"),

  // ---- Users ----
  listUsers: () => request<UserOut[]>("/api/leaderboard/users"),

  editUser: (id: number, body: { display_name?: string; is_committee?: boolean }) =>
    request<UserOut>(`/api/leaderboard/users/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
      auth: true,
    }),

  // ---- Competitions ----
  createCompetition: (body: { name: string; description?: string }) =>
    request<CompetitionOut>("/api/leaderboard/competitions", {
      method: "POST",
      body: JSON.stringify(body),
      auth: true,
    }),

  editCompetition: (id: number, body: { name?: string; description?: string; status?: string }) =>
    request<CompetitionOut>(`/api/leaderboard/competitions/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
      auth: true,
    }),

  deleteCompetition: (id: number) =>
    request<{ deleted: number }>(`/api/leaderboard/competitions/${id}`, {
      method: "DELETE",
      auth: true,
    }),

  // ---- Individual score entries ----
  listScores: (competitionId?: number, userId?: number) => {
    const params = new URLSearchParams();
    if (competitionId) params.set("competition_id", String(competitionId));
    if (userId) params.set("user_id", String(userId));
    return request<ScoreOut[]>(`/api/leaderboard/scores?${params}`);
  },

  editScore: (id: number, body: { points?: number; reason?: string }) =>
    request<ScoreOut>(`/api/leaderboard/scores/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
      auth: true,
    }),

  deleteScore: (id: number) =>
    request<{ deleted: number }>(`/api/leaderboard/scores/${id}`, { method: "DELETE", auth: true }),
};
