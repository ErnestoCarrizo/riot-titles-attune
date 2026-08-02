import type { ReactNode } from 'react';
import type { IconName } from '../types';

type Props = {
  name: IconName;
  size?: number;
  className?: string;
  title?: string;
};

export function Icon({ name, size = 20, className, title }: Props) {
  const common = {
    width: size,
    height: size,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.8,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    className,
    role: title ? ('img' as const) : undefined,
    'aria-hidden': title ? undefined : true,
  };

  const paths: Record<IconName, ReactNode> = {
    diamond: <><path d="M12 2 21 12 12 22 3 12 12 2Z"/><path d="m8.5 12 3.5 4 3.5-4-3.5-4-3.5 4Z"/></>,
    sword: <><path d="m14 3 7 7-11 11-4-4L17 6"/><path d="m14 3 7 7"/><path d="m6 14 4 4"/><path d="m3 21 4-4"/></>,
    feather: <><path d="M20 4c-7.5 0-13 3.5-15 10 3.5-2 7-3 11-3"/><path d="M20 4c0 7-4 12-11 14"/><path d="m4 20 6-6"/></>,
    leaf: <><path d="M20 4C11 4 5 8 4 20c8-1 14-6 16-16Z"/><path d="M4 20 14 10"/></>,
    trophy: <><path d="M8 4h8v4a4 4 0 0 1-8 0V4Z"/><path d="M6 6H3v1a4 4 0 0 0 4 4"/><path d="M18 6h3v1a4 4 0 0 1-4 4"/><path d="M12 12v5"/><path d="M8 21h8"/><path d="M9 17h6v4H9z"/></>,
    tree: <><path d="M12 3v18"/><path d="m5 8 7-5 7 5"/><path d="m5 14 7-5 7 5"/><path d="M7 21h10"/></>,
    list: <><path d="M9 6h11"/><path d="M9 12h11"/><path d="M9 18h11"/><path d="M4 6h.01"/><path d="M4 12h.01"/><path d="M4 18h.01"/></>,
    check: <path d="m5 12 4 4L19 6"/>,
    info: <><circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><path d="M12 8h.01"/></>,
    'arrow-left': <><path d="m15 18-6-6 6-6"/><path d="M9 12h10"/></>,
    'chevron-right': <path d="m9 18 6-6-6-6"/>,
  };

  return <svg {...common}>{title ? <title>{title}</title> : null}{paths[name]}</svg>;
}
