interface CricketWicketProps {
  size?: number;
  fallen?: boolean;
  className?: string;
}

export function CricketWicketIcon({ size = 24, fallen = false, className = '' }: CricketWicketProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      {/* Left stump */}
      <rect x="6" y="7" width="2" height="15" rx="1" fill="currentColor" />
      {/* Mid stump */}
      <rect x="11" y="7" width="2" height="15" rx="1" fill="currentColor" />
      {/* Right stump */}
      <rect x="16" y="7" width="2" height="15" rx="1" fill="currentColor" />

      {fallen ? (
        /* Bails knocked off — shown scattered to the side */
        <>
          <rect x="3" y="3.5" width="5" height="1.5" rx="0.75" fill="currentColor" transform="rotate(-30 3 3.5)" />
          <rect x="14" y="2" width="5" height="1.5" rx="0.75" fill="currentColor" transform="rotate(20 14 2)" />
        </>
      ) : (
        /* Bails sitting on top of stumps */
        <>
          <rect x="7" y="5" width="5" height="2" rx="1" fill="currentColor" />
          <rect x="12" y="5" width="5" height="2" rx="1" fill="currentColor" />
        </>
      )}
    </svg>
  );
}
