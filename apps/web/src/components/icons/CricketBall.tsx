interface CricketBallProps {
  size?: number;
  className?: string;
}

export function CricketBallIcon({ size = 24, className = '' }: CricketBallProps) {
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
      {/* Ball body */}
      <circle cx="12" cy="12" r="10" fill="#C41E3A" />

      {/* Equatorial seam — classic S-curve, double line */}
      <path d="M 2 12 C 7 5, 17 19, 22 12"  stroke="white" strokeWidth="1.4" fill="none" strokeLinecap="round" />
      <path d="M 2 12 C 7 7.5, 17 16.5, 22 12" stroke="white" strokeWidth="1.4" fill="none" strokeLinecap="round" />

      {/* Stitch marks between the two seam lines */}
      <line x1="5.5"  y1="8.2"  x2="5.5"  y2="10.2" stroke="white" strokeWidth="0.9" strokeLinecap="round" />
      <line x1="8.5"  y1="7.0"  x2="8.5"  y2="9.5"  stroke="white" strokeWidth="0.9" strokeLinecap="round" />
      <line x1="12"   y1="8.0"  x2="12"   y2="11.0"  stroke="white" strokeWidth="0.9" strokeLinecap="round" />
      <line x1="15.5" y1="14.5" x2="15.5" y2="17.0"  stroke="white" strokeWidth="0.9" strokeLinecap="round" />
      <line x1="18.5" y1="13.5" x2="18.5" y2="16.0"  stroke="white" strokeWidth="0.9" strokeLinecap="round" />
    </svg>
  );
}
