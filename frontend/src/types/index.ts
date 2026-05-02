export interface TaskScore {
  code_understanding: number;
  log_analysis: number;
  metric_interpretation: number;
  causal_reasoning: number;
  pattern_recognition: number;
  context_synthesis: number;
  root_cause_identification: number;
  solution_recommendation: number;
}

export interface ModelMetadata {
  parameters: string;
  context_window: number;
  release_date: string;
}

export interface Model {
  id: string;
  name: string;
  provider: string;
  version: string;
  task_scores: TaskScore;
  rca_score: number;
  metadata: ModelMetadata;
  source?: string;
  last_updated?: string;
}

export interface UserModelInput {
  name: string;
  provider: string;
  version: string;
  task_scores: TaskScore;
  metadata: ModelMetadata;
}

export interface UserModelResponse {
  success: boolean;
  message: string;
  model?: Model;
}

export interface HuggingFaceFetchResponse {
  success: boolean;
  message: string;
  suitable_for_rca?: boolean;
  rejection_reason?: string;
  confidence?: 'high' | 'medium' | 'low' | 'very_low';
  warning?: string;
  model_info?: {
    name?: string;
    provider?: string;
    parameters?: string;
    context_window?: number;
  };
  benchmarks?: Record<string, number>;
  task_scores?: Partial<TaskScore>;
  rca_score?: number;
  assessment?: string;
}

export interface TaskInfo {
  id: keyof TaskScore;
  name: string;
  description: string;
  weight: number;
}

export interface TaskLeaderboard extends TaskInfo {
  top_model: string;
  top_score: number;
  all_scores: Array<{
    model: string;
    model_name: string;
    score: number;
  }>;
}

export interface LeaderboardEntry {
  rank: number;
  model: Model;
  rca_score: number;
}

export type SortOption = 'rca_score_desc' | 'rca_score_asc' | 'name_asc' | 'name_desc';
export type TaskFilter = keyof TaskScore | 'all';
export type ProviderFilter = string | 'all';

// Category types for multiple leaderboards
export interface Category {
  id: string;
  name: string;
  description: string;
  icon: string;
}

export interface CategoryLeaderboardEntry {
  rank: number;
  model: {
    id: string;
    name: string;
    provider: string;
    version: string;
    metadata: ModelMetadata;
  };
  score: number;
  rca_score: number;
  key_benchmarks: Record<string, number>;
}

export interface CategoryLeaderboardResponse {
  category: string;
  category_name: string;
  category_description: string;
  leaderboard: CategoryLeaderboardEntry[];
  count: number;
}

export interface CategoriesResponse {
  categories: Record<string, Category>;
}

// Made with Bob
