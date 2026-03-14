import { ItemTile } from './ItemTile';

interface ItemGridProps {
  items: string[];
  selected: string[];
  onSelect: (item: string) => void;
  onDeselect: (item: string) => void;
  disabled: boolean;
  shakingItems?: string[];
  bouncingItems?: string[];
}

export function ItemGrid({ items, selected, onSelect, onDeselect, disabled, shakingItems = [], bouncingItems = [] }: ItemGridProps) {
  return (
    <div className="grid grid-cols-4 gap-2 w-full">
      {items.map(item => (
        <ItemTile
          key={item}
          item={item}
          isSelected={selected.includes(item)}
          onSelect={() => onSelect(item)}
          onDeselect={() => onDeselect(item)}
          disabled={disabled}
          shaking={shakingItems.includes(item)}
          bouncing={bouncingItems.includes(item)}
        />
      ))}
    </div>
  );
}
