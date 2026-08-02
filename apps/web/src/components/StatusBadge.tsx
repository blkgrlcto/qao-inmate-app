const STYLES: Record<string, string> = {
  open: "bg-blue-100 text-blue-800",
  active: "bg-emerald-100 text-emerald-800",
  awaiting_decision: "bg-amber-100 text-amber-800",
  closed: "bg-gray-200 text-gray-600",
};

export function statusLabel(status: string): string {
  return status
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs font-medium ${STYLES[status] || "bg-gray-200 text-gray-600"}`}
    >
      {statusLabel(status)}
    </span>
  );
}
