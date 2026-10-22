import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export function AuthCallback() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { completeLogin } = useAuth();

  useEffect(() => {
    const token = params.get("token");
    if (token) {
      completeLogin(token);
    }
    navigate("/settings", { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex items-center justify-center h-full text-muted text-sm">
      Logging you in…
    </div>
  );
}
