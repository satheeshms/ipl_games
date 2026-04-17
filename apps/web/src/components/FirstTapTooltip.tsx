import { useEffect } from 'react';

interface FirstTapTooltipProps {
  visible: boolean;
  onDismiss: () => void;
}

const AUTO_DISMISS_MS = 4000;

export function FirstTapTooltip({ visible, onDismiss }: FirstTapTooltipProps) {
  useEffect(() => {
    if (!visible) return;
    const timer = setTimeout(onDismiss, AUTO_DISMISS_MS);
    return () => clearTimeout(timer);
  }, [visible, onDismiss]);

  if (!visible) return null;

  return (
    <div className="relative flex justify-start pl-2 mt-1">
      {/* Arrow pointing up */}
      <div className="absolute -top-2 left-6 w-0 h-0 border-l-[6px] border-r-[6px] border-b-[8px] border-l-transparent border-r-transparent border-b-white" />
      <button
        onClick={onDismiss}
        aria-label="Dismiss tip"
        className="bg-white text-[#1a1a2e] text-xs font-semibold rounded-lg px-3 py-2 shadow-lg leading-snug text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-white/50"
      >
        Tap 3 more players, then hit <strong>Submit</strong> →
      </button>
    </div>
  );
}
