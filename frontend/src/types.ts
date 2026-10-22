export interface UserOut {
  id: number;
  discord_id: number;
  username: string;
  display_name: string;
  is_committee: boolean;
}

export interface LeaderboardEntry {
  rank: number;
  user: UserOut;
  points: number;
}

export interface LeaderboardOut {
  competition: string;
  entries: LeaderboardEntry[];
}

export interface CompetitionOut {
  id: number;
  name: string;
  description: string;
  status: string;
  winner_user_id: number | null;
  created_at: string;
}

export interface ScoreOut {
  id: number;
  competition_id: number;
  competition_name: string;
  user_id: number;
  user_display_name: string;
  points: number;
  reason: string;
  created_at: string;
}

export interface AnimeOut {
  mal_id: number;
  title: string;
  description: string;
  score: number | null;
  episodes: number | null;
  status: string;
  genres: string[];
  image_url: string;
  mal_url: string;
}

export interface AnnouncementOut {
  id: number;
  title: string;
  message: string;
  author_discord_id: number;
  channel_id: number;
  status: string;
  scheduled_for: string | null;
  created_at: string;
  edited_at: string | null;
}

export interface EventOut {
  id: number;
  name: string;
  description: string;
  location: string;
  event_time: string;
  channel_id: number;
  reminder_minutes_before: number;
  reminder_sent: boolean;
  created_at: string;
}

export interface AchievementOut {
  key: string;
  name: string;
  description: string;
  emoji: string;
  earned: boolean;
}

export interface CurrentUserOut {
  discord_id: number;
  username: string;
  display_name: string;
  is_committee: boolean;
}

export interface DiscordChannel {
  id: string;
  name: string;
}

export interface DiscordMember {
  discord_id: number;
  username: string;
  display_name: string;
}
