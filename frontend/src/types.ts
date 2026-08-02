export type BranchStatus = 'unlocked' | 'in-progress' | 'pending';
export type BranchTone = 'cyan' | 'orange' | 'lime';
export type IconName = 'diamond' | 'sword' | 'feather' | 'leaf' | 'trophy' | 'tree' | 'list' | 'check' | 'info' | 'arrow-left' | 'chevron-right';

export interface Branch {
  id: string;
  name: string;
  rank: string;
  progress: number;
  tone: BranchTone;
  icon: IconName;
  status: BranchStatus;
  description?: string;
  hasChildren?: boolean;
  currentValue?: number | null;
  targetValue?: number | null;
  remainingValue?: number | null;
}

export interface Requirement {
  challengeId: number;
  challengeName: string;
  challengeDescription: string;
  currentTier: string;
  targetTier: string;
  currentValue: number | null;
  targetValue: number | null;
  remainingValue: number | null;
  remainingText: string;
  reverseDirection: boolean;
  progressDirection: 'increase' | 'decrease';
  iconUrl: string | null;
  achievedTime: string | null;
}

export interface TitleProgress {
  titleId: string;
  titleName: string;
  status: 'unlocked' | 'in_progress' | 'not_started' | 'unknown';
  unlocked: boolean;
  progressPercent: number | null;
  progressIsEstimate: boolean;
  requirements: Requirement[];
}

export interface ProgressResponse {
  player: { gameName: string; tagLine: string; riotId: string; puuid: string; platform: string };
  summary: {
    totalTitles: number;
    unlockedTitles: number;
    lockedTitles: number;
    inProgressTitles: number;
    notStartedTitles: number;
    unknownTitles: number;
    completionPercentage: number;
    closestTitleIds: string[];
  };
  titles: TitleProgress[];
  metadata: { locale: string; catalogSource: string; catalogFetchedAt: string; playerDataFetchedAt: string };
}

export interface TreeNode {
  challengeId: number;
  challengeName: string;
  challengeDescription: string;
  parentChallengeId: number | null;
  isCapstone: boolean;
  isCategory: boolean;
  status: 'unlocked' | 'in_progress' | 'not_started' | 'unknown';
  unlocked: boolean;
  progressPercent: number | null;
  progressIsEstimate: boolean;
  currentTier: string;
  targetTier: string;
  currentValue: number | null;
  targetValue: number | null;
  remainingValue: number | null;
  remainingText: string;
  reverseDirection: boolean;
  progressDirection: 'increase' | 'decrease';
  iconUrl: string | null;
  children: TreeNode[];
}

export interface TreeResponse {
  titleId: string;
  titleName: string;
  status: TitleProgress['status'];
  progressPercent: number | null;
  roots: TreeNode[];
}
