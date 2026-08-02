import { Icon } from './Icon';

type ViewMode = 'tree' | 'list';

type Props = {
  value: ViewMode;
  onChange: (value: ViewMode) => void;
};

export function SegmentedControl({ value, onChange }: Props) {
  return (
    <div className="segmented" aria-label="Vista del progreso">
      <button
        type="button"
        className={value === 'tree' ? 'is-active' : ''}
        aria-pressed={value === 'tree'}
        onClick={() => onChange('tree')}
      >
        <Icon name="tree" size={19} />
        Árbol
      </button>
      <button
        type="button"
        className={value === 'list' ? 'is-active' : ''}
        aria-pressed={value === 'list'}
        onClick={() => onChange('list')}
      >
        <Icon name="list" size={19} />
        Lista
      </button>
    </div>
  );
}
