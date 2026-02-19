type EmptyStateProps = {
  icon: string;
  title: string;
  message: string;
  action?: { label: string; href: string };
};

export function EmptyState({ icon, title, message, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-stone-200 bg-white p-8 text-center">
      <span className="mb-4 block text-5xl" aria-hidden>
        {icon}
      </span>
      <h3 className="mb-2 text-lg font-semibold text-stone-800">{title}</h3>
      <p className="mb-6 max-w-sm text-base text-stone-600">{message}</p>
      {action && (
        <a
          href={action.href}
          className="min-h-[48px] inline-flex items-center justify-center rounded-xl bg-amber-500 px-6 py-3 text-base font-medium text-white shadow-sm transition hover:bg-amber-600 active:scale-[0.98]"
        >
          {action.label}
        </a>
      )}
    </div>
  );
}
