import { useDiscordDirectory } from "../hooks/useDiscordDirectory";

interface ChannelSelectProps {
  value: string;
  onChange: (channelId: string) => void;
}

const FIELD =
  "w-full bg-ink border border-rule rounded-panel px-3 py-2 text-sm text-ivory placeholder:text-muted/50";

export function ChannelSelect({ value, onChange }: ChannelSelectProps) {
  const { channels, loaded } = useDiscordDirectory();

  if (loaded && channels.length === 0) {
    return (
      <div>
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          inputMode="numeric"
          placeholder="Channel ID"
          className={FIELD}
        />
        <p className="mt-1 text-xs text-muted">
          Couldn't load channels from Discord. Check that GUILD_ID is set and the bot is in the
          server, or paste the channel ID.
        </p>
      </div>
    );
  }

  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={!loaded}
      className={FIELD}
    >
      <option value="">{loaded ? "Choose a channel" : "Loading channels…"}</option>
      {channels.map((c) => (
        <option key={c.id} value={c.id}>
          #{c.name}
        </option>
      ))}
    </select>
  );
}
