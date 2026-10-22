import { useState } from "react";
import { api, ApiError } from "../api/client";
import { Panel } from "../components/Panel";
import { StateMessage } from "../components/StateMessage";
import type { AnimeOut } from "../types";

function AnimeDetail({ anime }: { anime: AnimeOut }) {
  return (
    <div className="flex gap-4">
      {anime.image_url && (
        <img
          src={anime.image_url}
          alt={anime.title}
          className="w-28 h-40 object-cover border border-rule rounded-panel shrink-0"
        />
      )}
      <div>
        <a
          href={anime.mal_url}
          target="_blank"
          rel="noreferrer"
          className="text-ivory font-display text-xl hover:text-murasaki transition-colors"
        >
          {anime.title}
        </a>
        <div className="mt-1 flex flex-wrap gap-2 text-xs text-muted">
          {anime.genres.map((g) => (
            <span key={g} className="border border-rule rounded-panel px-2 py-0.5">
              {g}
            </span>
          ))}
        </div>
        <p className="mt-2 text-sm text-muted leading-relaxed">{anime.description}</p>
        <div className="mt-3 flex gap-4 text-xs text-muted">
          {anime.score && <span>⭐ {anime.score}</span>}
          {anime.episodes && <span>{anime.episodes} episodes</span>}
          {anime.status && <span>{anime.status}</span>}
        </div>
      </div>
    </div>
  );
}

export function Anime() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<AnimeOut | null>(null);
  const [topList, setTopList] = useState<AnimeOut[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function runSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    try {
      setResult(await api.searchAnime(query.trim()));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Search failed.");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  async function runRandom() {
    setLoading(true);
    setError("");
    try {
      setResult(await api.randomAnime());
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't fetch a random anime.");
    } finally {
      setLoading(false);
    }
  }

  async function loadTop() {
    setLoading(true);
    setError("");
    try {
      setTopList(await api.topAnime(5));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Couldn't load the top list.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl text-ivory">Anime</h1>
        <p className="mt-1 text-sm text-muted">Search MyAnimeList via the bot's cache.</p>
      </div>

      <Panel>
        <form onSubmit={runSearch} className="flex gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search for an anime…"
            className="flex-1 bg-ink border border-rule rounded-panel px-3 py-2 text-sm text-ivory placeholder:text-muted/50"
          />
          <button
            type="submit"
            className="bg-murasaki hover:bg-murasaki-soft transition-colors text-ivory text-sm px-4 py-2 rounded-panel"
          >
            Search
          </button>
          <button
            type="button"
            onClick={runRandom}
            className="border border-rule hover:border-ai transition-colors text-ivory text-sm px-4 py-2 rounded-panel"
          >
            Random
          </button>
        </form>
      </Panel>

      {error && <StateMessage kind="error">{error}</StateMessage>}
      {loading && <StateMessage kind="loading">Looking that up…</StateMessage>}

      {result && (
        <Panel title="Result" className="rise-in">
          <AnimeDetail anime={result} />
        </Panel>
      )}

      <Panel
        title="Top rated right now"
        action={
          <button onClick={loadTop} className="text-xs text-ai hover:text-murasaki transition-colors">
            Refresh
          </button>
        }
      >
        {topList.length > 0 ? (
          <ol className="space-y-2">
            {topList.map((a, i) => (
              <li key={a.mal_id} className="border-b border-rule last:border-0">
                <button
                  onClick={() => setResult(a)}
                  className="w-full flex items-center gap-3 py-2 text-left hover:bg-raised/50 transition-colors rounded-panel px-1 -mx-1"
                >
                  <span className="font-mono text-muted w-5 shrink-0">{i + 1}</span>
                  {a.image_url ? (
                    <img
                      src={a.image_url}
                      alt={a.title}
                      className="w-9 h-12 object-cover border border-rule rounded-panel shrink-0"
                    />
                  ) : (
                    <div className="w-9 h-12 bg-raised border border-rule rounded-panel shrink-0" />
                  )}
                  <span className="text-ivory text-sm flex-1 min-w-0 truncate">{a.title}</span>
                  <span className="text-muted text-xs shrink-0">⭐ {a.score ?? "—"}</span>
                </button>
              </li>
            ))}
          </ol>
        ) : (
          <StateMessage kind="empty">Nothing loaded yet — hit refresh.</StateMessage>
        )}
      </Panel>
    </div>
  );
}
