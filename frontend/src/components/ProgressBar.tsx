type Props = {
  value: number;
  tone?: 'gold' | 'cyan' | 'orange' | 'lime';
  label?: string;
};

export function ProgressBar({ value, tone = 'gold', label }: Props) {
  const safeValue = Math.min(100, Math.max(0, value));
  return (
    <div
      className={`progress-bar progress-bar--${tone}`}
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={safeValue}
      aria-label={label}
    >
      <span style={{ width: `${safeValue}%` }} />
    </div>
  );
}
