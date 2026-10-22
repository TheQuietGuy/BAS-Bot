import { useId, useState } from "react";
import { useDiscordDirectory } from "../hooks/useDiscordDirectory";

export interface PickedMember {
  discord_id: number;
  username: string;
  display_name: string;
}

interface MemberPickerProps {
  value: PickedMember | null;
  onChange: (member: PickedMember | null) => void;
}

const FIELD =
  "w-full bg-ink border border-rule rounded-panel px-3 py-2 text-sm text-ivory placeholder:text-muted/50";

export function MemberPicker({ value, onChange }: MemberPickerProps) {
  const { members, loaded } = useDiscordDirectory();
  const listId = useId();
  const [text, setText] = useState(value?.display_name ?? "");
  const [manualId, setManualId] = useState(value ? String(value.discord_id) : "");

  // Directory unavailable: fall back to typing the ID and name by hand.
  if (loaded && members.length === 0) {
    return (
      <div className="space-y-2">
        <input
          value={manualId}
          inputMode="numeric"
          placeholder="Discord ID"
          onChange={(e) => {
            setManualId(e.target.value);
            const id = Number(e.target.value);
            onChange(id ? { discord_id: id, username: text || String(id), display_name: text || String(id) } : null);
          }}
          className={FIELD}
        />
        <input
          value={text}
          placeholder="Display name"
          onChange={(e) => {
            setText(e.target.value);
            const id = Number(manualId);
            onChange(id ? { discord_id: id, username: e.target.value || String(id), display_name: e.target.value || String(id) } : null);
          }}
          className={FIELD}
        />
        <p className="text-xs text-muted">
          Couldn't load the member list from Discord. Enable the Server Members intent for the bot,
          or enter the member by hand.
        </p>
      </div>
    );
  }

  function handleChange(next: string) {
    setText(next);
    const match = members.find(
      (m) => `${m.display_name} (@${m.username})` === next || m.display_name === next
    );
    onChange(match ?? null);
  }

  return (
    <div>
      <input
        value={text}
        list={listId}
        disabled={!loaded}
        placeholder={loaded ? "Start typing a name" : "Loading members…"}
        onChange={(e) => handleChange(e.target.value)}
        className={FIELD}
      />
      <datalist id={listId}>
        {members.map((m) => (
          <option key={m.discord_id} value={`${m.display_name} (@${m.username})`} />
        ))}
      </datalist>
      {text && !value && loaded && (
        <p className="mt-1 text-xs text-muted">Pick a member from the suggestions.</p>
      )}
    </div>
  );
}
