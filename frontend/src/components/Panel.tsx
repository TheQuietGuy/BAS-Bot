import type { ReactNode } from "react";

interface PanelProps {
  title?: string;
  children: ReactNode;
  className?: string;
  action?: ReactNode;
}

export function Panel({ title, children, className = "", action }: PanelProps) {
  return (
    <div className={`panel p-5 ${className}`}>
      {title && (
        <div className="flex items-center justify-between mb-4">
          <h3 className="panel-title">{title}</h3>
          {action}
        </div>
      )}
      {children}
    </div>
  );
}
