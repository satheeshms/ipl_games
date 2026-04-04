interface Env {
  ANALYTICS: AnalyticsEngineDataset;
}

interface TrackPayload {
  event: string;
  puzzle_id?: string;
  game_mode?: string;
  result?: string;
  color?: string;
  attempt_number?: number;
  groups_made?: number;
  total_attempts?: number;
}

const KNOWN_EVENTS = new Set([
  'page_visited',
  'game_started',
  'guess_submitted',
  'group_completed',
  'game_completed',
]);

export async function onRequestPost(
  context: EventContext<Env, string, unknown>
): Promise<Response> {
  try {
    const body = await context.request.json<TrackPayload>();

    if (!body.event || !KNOWN_EVENTS.has(body.event)) {
      return new Response(null, { status: 400 });
    }

    context.env.ANALYTICS.writeDataPoint({
      indexes: [body.puzzle_id ?? ''],
      blobs: [
        body.event,
        body.game_mode ?? '',
        body.result ?? '',
        body.color ?? '',
      ],
      doubles: [
        body.attempt_number ?? 0,
        body.groups_made ?? 0,
        body.total_attempts ?? 0,
      ],
    });

    return new Response(null, { status: 204 });
  } catch {
    // Never let analytics errors surface to the client
    return new Response(null, { status: 204 });
  }
}
