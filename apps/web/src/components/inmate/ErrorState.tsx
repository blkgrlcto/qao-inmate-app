type ErrorStateProps = {
  title?: string;
  message: string;
  onRetry?: () => void;
};

export function ErrorState({
  title = "Something went wrong",
  message,
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-amber-200 bg-amber-50/50 p-8 text-center">
      <span className="mb-4 block text-4xl" aria-hidden>
        ⚠️
      </span>
      <h3 className="mb-2 text-lg font-semibold text-stone-800">{title}</h3>
      <p className="mb-6 max-w-sm text-base text-stone-600">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="min-h-[48px] min-w-[120px] rounded-xl border-2 border-amber-600 bg-white px-6 py-3 text-base font-medium text-amber-700 transition hover:bg-amber-50 active:scale-[0.98]"
        >
          Try again
        </button>
      )}
    </div>
  );
}
