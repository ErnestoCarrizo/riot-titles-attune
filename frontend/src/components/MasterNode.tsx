import { Icon } from './Icon';

type Props = { title: string; progress: number; rank: string };

export function MasterNode({ title, progress, rank }: Props) {
  return (
    <article className="master-node" aria-label={`${title}, ${rank}, ${progress} por ciento`}>
      <span className="master-node__icon"><Icon name="trophy" size={32} /></span>
      <h2>{title}</h2>
      <span className="rank-pill">{rank}</span>
      <strong>{progress}%</strong>
    </article>
  );
}
