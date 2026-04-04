interface TrackProps {
  puzzle_id?: string;
  game_mode?: string;
  result?: string;
  color?: string;
  attempt_number?: number;
  groups_made?: number;
  total_attempts?: number;
}

export function track(event: string, props: TrackProps = {}): void {
  if (typeof navigator === 'undefined' || !navigator.sendBeacon) return;
  navigator.sendBeacon('/api/track', JSON.stringify({ event, ...props }));
}
