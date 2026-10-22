import { NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", chapter: "01" },
  { to: "/leaderboard", label: "Leaderboard", chapter: "02" },
  { to: "/members", label: "Members", chapter: "03" },
  { to: "/anime", label: "Anime", chapter: "04" },
  { to: "/announcements", label: "Announcements", chapter: "05" },
  { to: "/events", label: "Events", chapter: "06" },
  { to: "/achievements", label: "Achievements", chapter: "07" },
  { to: "/settings", label: "Settings", chapter: "08" },
];

export function Sidebar() {
  return (
    <aside className="w-60 shrink-0 border-r border-rule flex flex-col h-full">
      <div className="px-6 py-7">
        <div className="font-display text-2xl leading-none text-ivory">BAS Bot</div>
        <div className="mt-1 text-xs text-muted">Brunel Anime Society</div>
      </div>

      <div className="screentone-rule mx-6" />

      <nav className="flex-1 py-4">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              `group flex items-center gap-3 px-6 py-3 border-l-2 transition-colors ${
                isActive
                  ? "border-murasaki text-ivory bg-raised/60"
                  : "border-transparent text-muted hover:text-ivory hover:border-rule"
              }`
            }
          >
            <span className="font-mono text-[11px] text-muted group-hover:text-murasaki">
              {item.chapter}
            </span>
            <span className="text-sm">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="px-6 py-5 text-xs text-muted border-t border-rule">
        Connected to
        <br />
        <span className="text-ivory">localhost:8000</span>
      </div>
    </aside>
  );
}
