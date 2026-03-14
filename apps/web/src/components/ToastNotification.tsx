interface ToastNotificationProps {
  message: string | null;
}

export function ToastNotification({ message }: ToastNotificationProps) {
  return (
    <div
      className={[
        'pointer-events-none flex justify-center transition-opacity duration-300',
        message ? 'opacity-100' : 'opacity-0',
      ].join(' ')}
      aria-live="polite"
    >
      <div className="bg-gray-900/90 text-white text-sm font-medium px-5 py-2 rounded-full shadow-lg">
        {message ?? '\u00a0'}
      </div>
    </div>
  );
}
