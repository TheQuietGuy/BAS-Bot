import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { DiscordChannel, DiscordMember } from "../types";

// Fetched once per page load and shared, so several pickers on one page
// don't each hit Discord.
let cache: Promise<{ channels: DiscordChannel[]; members: DiscordMember[] }> | null = null;

function loadDirectory() {
  if (!cache) {
    cache = Promise.all([
      api.listDiscordChannels().catch(() => [] as DiscordChannel[]),
      api.listDiscordMembers().catch(() => [] as DiscordMember[]),
    ]).then(([channels, members]) => ({ channels, members }));
  }
  return cache;
}

export function useDiscordDirectory() {
  const [channels, setChannels] = useState<DiscordChannel[]>([]);
  const [members, setMembers] = useState<DiscordMember[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let active = true;
    loadDirectory().then((dir) => {
      if (!active) return;
      setChannels(dir.channels);
      setMembers(dir.members);
      setLoaded(true);
    });
    return () => {
      active = false;
    };
  }, []);

  return { channels, members, loaded };
}
