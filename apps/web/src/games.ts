export interface GameConfig {
  slug: string;
  category: string;
  label: string;
  description: string;
  icon: string;
  path: string;
  status: 'active' | 'coming-soon';
  puzzleDir: string;
  storagePrefix: string;
}

export const GAMES: GameConfig[] = [
  {
    slug: 'ipl',
    category: 'Sports',
    label: 'IPL Edition',
    description: 'Group 16 IPL cricket items into 4 hidden categories.',
    icon: '🏏',
    path: '/sports/ipl',
    status: 'active',
    puzzleDir: 'puzzles/ipl',
    storagePrefix: 'ipl-cluster4', // preserves existing localStorage keys
  },
  {
    slug: 'kerala-elections',
    category: 'Politics',
    label: 'Kerala Elections Edition',
    description: 'Group 16 Kerala politics items into 4 hidden categories.',
    icon: '🗳️',
    path: '/politics/kerala-elections',
    status: 'coming-soon',
    puzzleDir: 'puzzles/kerala-elections',
    storagePrefix: 'kerala-elections',
  },
];

export function getGamesByCategory(): Record<string, GameConfig[]> {
  return GAMES.reduce((acc, game) => {
    (acc[game.category] ??= []).push(game);
    return acc;
  }, {} as Record<string, GameConfig[]>);
}

export function getGameBySlug(slug: string): GameConfig | undefined {
  return GAMES.find(g => g.slug === slug);
}
