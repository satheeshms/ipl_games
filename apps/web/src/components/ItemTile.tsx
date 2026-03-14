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
      animate={bouncing ? { scale: [1, 1.1, 0.95, 1.05, 1] } : { scale: 1 }}
      transition={bouncing ? { duration: 0.4 } : { duration: 0.15 }}
      className={[
        'rounded-lg py-4 px-2 text-white text-sm font-semibold text-center',
        'transition-colors duration-150 select-none min-h-[48px]',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-white/50',
        isSelected
          ? 'bg-[#4a4a6a]'
          : 'bg-[#2d2d44] hover:bg-[#3a3a58]',
        disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer',
        shaking ? 'shake' : '',
      ].join(' ')}
    >
      {item}
    </motion.button>
  );
}
