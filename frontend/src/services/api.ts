import axios from 'axios';
import type {
  Model,
  TaskLeaderboard,
  LeaderboardEntry,
  UserModelInput,
  UserModelResponse,
  HuggingFaceFetchResponse,
  CategoriesResponse,
  CategoryLeaderboardResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL ?? '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ModelsResponse {
  models: Model[];
  count: number;
}

export interface TasksResponse {
  tasks: TaskLeaderboard[];
}

export interface LeaderboardResponse {
  leaderboard: LeaderboardEntry[];
}

export interface ProvidersResponse {
  providers: string[];
}

export interface DeleteModelResponse {
  success: boolean;
  message: string;
}

export interface RefreshStatus {
  last_refresh: string | null;
  next_refresh: string | null;
  models_updated: number;
  status: string;
  errors: string[];
}

export const apiService = {
  // Get all models
  async getModels(params?: {
    provider?: string;
    min_rca_score?: number;
    max_rca_score?: number;
  }): Promise<ModelsResponse> {
    const response = await api.get<ModelsResponse>('/models', { params });
    return response.data;
  },

  // Get single model by ID
  async getModel(modelId: string): Promise<Model> {
    const response = await api.get<Model>(`/models/${modelId}`);
    return response.data;
  },

  // Get all tasks with leaderboards
  async getTasks(): Promise<TasksResponse> {
    const response = await api.get<TasksResponse>('/tasks');
    return response.data;
  },

  // Get task leaderboard by ID
  async getTaskLeaderboard(taskId: string): Promise<TaskLeaderboard> {
    const response = await api.get<TaskLeaderboard>(`/tasks/${taskId}`);
    return response.data;
  },

  // Get overall RCA leaderboard
  async getLeaderboard(ascending: boolean = false): Promise<LeaderboardResponse> {
    const response = await api.get<LeaderboardResponse>('/leaderboard', {
      params: { ascending },
    });
    return response.data;
  },

  // Get all providers
  async getProviders(): Promise<ProvidersResponse> {
    const response = await api.get<ProvidersResponse>('/providers');
    return response.data;
  },

  // Health check
  async healthCheck(): Promise<{ status: string; service: string; version: string }> {
    const response = await api.get('/health');
    return response.data;
  },

  // Add user model
  async addUserModel(modelInput: UserModelInput): Promise<UserModelResponse> {
    const response = await api.post<UserModelResponse>('/models', modelInput);
    return response.data;
  },

  // Delete user model
  async deleteUserModel(modelId: string): Promise<DeleteModelResponse> {
    const response = await api.delete<DeleteModelResponse>(`/models/${modelId}`);
    return response.data;
  },

  // Fetch model from HuggingFace (preview)
  async fetchFromHuggingFace(huggingfaceUrl: string): Promise<HuggingFaceFetchResponse> {
    const response = await api.post<HuggingFaceFetchResponse>('/models/fetch-from-huggingface', {
      huggingface_url: huggingfaceUrl,
    });
    return response.data;
  },

  // Add model from HuggingFace
  async addFromHuggingFace(huggingfaceUrl: string): Promise<UserModelResponse> {
    const response = await api.post<UserModelResponse>('/models/add-from-huggingface', {
      huggingface_url: huggingfaceUrl,
    });
    return response.data;
  },

  // Get all categories
  async getCategories(): Promise<CategoriesResponse> {
    const response = await api.get<CategoriesResponse>('/categories');
    return response.data;
  },

  // Get category leaderboard
  async getCategoryLeaderboard(category: string, ascending: boolean = false): Promise<CategoryLeaderboardResponse> {
    const response = await api.get<CategoryLeaderboardResponse>(`/leaderboard/${category}`, {
      params: { ascending },
    });
    return response.data;
  },

  // Get refresh status
  async getRefreshStatus(): Promise<RefreshStatus> {
    const response = await api.get<RefreshStatus>('/refresh/status');
    return response.data;
  },

  // Force refresh
  async forceRefresh(): Promise<{ success: boolean; message: string; status: RefreshStatus }> {
    const response = await api.post('/refresh/force');
    return response.data;
  },
};

// Made with Bob
