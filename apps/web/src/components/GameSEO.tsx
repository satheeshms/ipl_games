import { Helmet } from 'react-helmet-async';
import type { Puzzle } from '../types';

interface GameSEOProps {
  puzzle: Puzzle;
}

export function GameSEO({ puzzle }: GameSEOProps) {
  const canonicalUrl = import.meta.env.VITE_CANONICAL_URL ?? '';
  const title = `Puzzle #${puzzle.edition} – ${puzzle.date} | Cluster 4 - IPL Edition`;
  const description = `Today's IPL Cluster 4 puzzle (#${puzzle.edition}) — find 4 groups across ${puzzle.categories.length} categories. ${puzzle.date}.`;

  const gameJsonLd = JSON.stringify({
    '@context': 'https://schema.org',
    '@type': 'Game',
    name: 'Cluster 4 - IPL Edition',
    description: 'A daily IPL cricket word puzzle. Find 4 hidden groups of 4 items.',
    url: canonicalUrl,
    datePublished: puzzle.date,
    identifier: String(puzzle.edition),
    inLanguage: 'en',
    numberOfPlayers: {
      '@type': 'QuantitativeValue',
      minValue: 1,
      maxValue: 1,
    },
    gamePlayMode: 'SinglePlayer',
  });

  return (
    <Helmet>
      <title>{title}</title>
      <meta name="description" content={description} />
      <link rel="canonical" href={canonicalUrl} />
      <meta property="og:title" content={`Puzzle #${puzzle.edition} – ${puzzle.date}`} />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={canonicalUrl} />
      <script type="application/ld+json">{gameJsonLd}</script>
    </Helmet>
  );
}
