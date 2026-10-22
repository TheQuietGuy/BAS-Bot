import type { ReactNode } from "react";

interface StateMessageProps {
  kind: "error" | "empty" | "loading";
  children: ReactNode;
}

export function StateMessage({ kind, children }: StateMessageProps) {
  const color = kind === "error" ? "text-hanko" : "text-muted";
  return <p className={`text-sm ${color}`}>{children}</p>;
}
