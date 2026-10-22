import { useCallback, useEffect, useState } from "react";
import { api, ApiError, clearStoredApiKey, discordLoginUrl, getStoredApiKey, setStoredApiKey } from "../api/client";
import type { CurrentUserOut } from "../types";

export function useAuth() {
  const [token, setToken] = useState(getStoredApiKey());
  const [user, setUser] = useState<CurrentUserOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const refresh = useCallback(() => {
    const current = getStoredApiKey();
    if (!current) {
      setUser(null);
      return;
    }
    setLoading(true);
    setError("");
    api
      .getMe()
      .then(setUser)
      .catch((e) => {
        setUser(null);
        // An expired/invalid token shouldn't linger forever.
        if (e instanceof ApiError && e.status === 401) {
          clearStoredApiKey();
          setToken("");
        }
        setError(e.message);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(refresh, [refresh, token]);

  const login = () => {
    window.location.href = discordLoginUrl();
  };

  const completeLogin = (newToken: string) => {
    setStoredApiKey(newToken);
    setToken(newToken);
  };

  const logout = () => {
    clearStoredApiKey();
    setToken("");
    setUser(null);
  };

  return {
    token,
    user,
    isLoggedIn: !!user,
    isCommittee: user?.is_committee ?? false,
    loading,
    error,
    login,
    completeLogin,
    logout,
  };
}
