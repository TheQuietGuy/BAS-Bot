import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { Dashboard } from "./pages/Dashboard";
import { Leaderboard } from "./pages/Leaderboard";
import { Members } from "./pages/Members";
import { Anime } from "./pages/Anime";
import { Announcements } from "./pages/Announcements";
import { Events } from "./pages/Events";
import { Achievements } from "./pages/Achievements";
import { Settings } from "./pages/Settings";
import { AuthCallback } from "./pages/AuthCallback";

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-ink">
        <Sidebar />
        <main className="flex-1 overflow-y-auto px-8 py-8">
          <div className="max-w-5xl">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/leaderboard" element={<Leaderboard />} />
              <Route path="/members" element={<Members />} />
              <Route path="/anime" element={<Anime />} />
              <Route path="/announcements" element={<Announcements />} />
              <Route path="/events" element={<Events />} />
              <Route path="/achievements" element={<Achievements />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/auth/callback" element={<AuthCallback />} />
            </Routes>
          </div>
        </main>
      </div>
    </BrowserRouter>
  );
}
