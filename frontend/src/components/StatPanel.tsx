interface StatPanelProps {
  value: string | number;
  label: string;
}

export function StatPanel({ value, label }: StatPanelProps) {
  return (
    <div className="panel px-5 py-4">
      <div className="font-display text-3xl text-ivory leading-none">{value}</div>
      <div className="mt-1.5 text-xs text-muted">{label}</div>
    </div>
  );
}
