import { motion } from 'framer-motion';

interface ItemTileProps {
  item: string;
  isSelected: boolean;
  onSelect: () => void;
  onDeselect: () => void;
  disabled: boolean;
  shaking?: boolean;
  bouncing?: boolean;
}

export function ItemTile({ item, isSelected, onSelect, onDeselect, disabled, shaking = false, bouncing = false }: ItemTileProps) {
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
      aria-label={`${item}${isSelected ? ', selected' : ''}`}
      animate={bouncing ? { scale: [1, 1.1, 0.95, 1.05, 1] } : { scale: 1 }}
      transition={bouncing ? { duration: 0.4 } : { duration: 0.15 }}
      className={[
        'rounded-lg py-4 px-2 text-white text-sm font-semibold text-center',
        'uppercase tracking-wider',
        'transition-colors duration-150 select-none min-h-[48px]',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-game-accent/50',
        isSelected
          ? 'bg-game-tile-selected border-2 border-game-accent'
          : 'bg-game-tile border border-white/10 hover:bg-game-tile-hover hover:border-game-accent/40',
        disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer',
        shaking ? 'shake' : '',
      ].join(' ')}
    >
      {item}
    </motion.button>
  );
}
