import { motion } from 'framer-motion';
import type { PuzzleCategory, Guess } from '../types';

const COLOR_MAP: Record<string, string> = {
  yellow: '#F5A623',
  green:  '#4CAF50',
  blue:   '#42A5F5',
  purple: '#AB47BC',
};

interface CategoryBannerProps {
  category: PuzzleCategory;
  guessHistory: Guess[];
  displayNames?: Record<string, string>;
}

export function CategoryBanner({ category, guessHistory, displayNames }: CategoryBannerProps) {
  const guess = guessHistory.find(g => g.correct && g.categoryColor === category.color);
  const items = guess?.items ?? [];
  const labels = items.map(item => displayNames?.[item] ?? item);

  return (
    <motion.div
      initial={{ opacity: 0, y: -20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      className="w-full rounded-lg px-4 py-3 flex flex-col items-center justify-center gap-1"
      style={{ backgroundColor: COLOR_MAP[category.color] }}
    >
      <p className="text-sm font-bold text-gray-900 uppercase tracking-wider">{category.title}</p>
      <p className="text-sm text-gray-800">{labels.join(', ')}</p>
    </motion.div>
  );
}
