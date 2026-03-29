import { motion } from 'framer-motion';

interface ItemTileProps {
  item: string;
  displayName?: string;
  isSelected: boolean;
  onSelect: () => void;
  onDeselect: () => void;
  disabled: boolean;
  shaking?: boolean;
  bouncing?: boolean;
}

function labelFontSize(label: string): string {
  if (label.length > 22) return 'text-[0.6rem]';
  if (label.length > 16) return 'text-[0.7rem]';
  if (label.length > 11) return 'text-xs';
  return 'text-sm';
}

export function ItemTile({ item, displayName, isSelected, onSelect, onDeselect, disabled, shaking = false, bouncing = false }: ItemTileProps) {
  const label = displayName ?? item;

  function handleClick() {
    if (disabled) return;
    if (isSelected) {
      onDeselect();
    } else {
      onSelect();
    }
  }

  return (
    <motion.button
      onClick={handleClick}
      disabled={disabled}
      aria-pressed={isSelected}
      aria-label={`${label}${isSelected ? ', selected' : ''}`}
      animate={bouncing ? { scale: [1, 1.1, 0.95, 1.05, 1] } : { scale: 1 }}
      transition={bouncing ? { duration: 0.4 } : { duration: 0.15 }}
      className={[
        `rounded-lg px-2 text-white ${labelFontSize(label)} font-semibold text-center`,
        'h-16 flex items-center justify-center leading-tight',
        'transition-colors duration-150 select-none',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-game-accent/50',
        isSelected
          ? 'bg-game-tile-selected border-2 border-game-accent'
          : 'bg-game-tile border border-white/10 hover:bg-game-tile-hover hover:border-game-accent/40',
        disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer',
        shaking ? 'shake' : '',
      ].join(' ')}
    >
      {label}
    </motion.button>
  );
}
