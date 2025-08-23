// frontend/src/api.ts
// API fetch helpers for backend endpoints

import { SchedulesResponse, PortItem, CarrierItem, SearchParams, ApiError } from './types';

export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

class ApiClient {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        const errorText = await response.text();
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        
        try {
          const errorData = JSON.parse(errorText);
          if (errorData.detail) {
            errorMessage = errorData.detail;
          }
        } catch {
          // Use default error message if parsing fails
        }
        
        throw new Error(errorMessage);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Network error occurred');
    }
  }

  async listSchedules(params: SearchParams = {}): Promise<SchedulesResponse> {
    const searchParams = new URLSearchParams();
    
    // Add all defined parameters to query string
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, String(value));
      }
    });

    const endpoint = `/api/schedules${searchParams.toString() ? `?${searchParams}` : ''}`;
    return this.request<SchedulesResponse>(endpoint);
  }

  async searchPorts(query: string, limit: number = 15): Promise<PortItem[]> {
    if (!query || query.length < 2) {
      return [];
    }

    const searchParams = new URLSearchParams({
      q: query,
      limit: String(limit),
    });

    const endpoint = `/api/ports/search?${searchParams}`;
    const response = await this.request<PortItem[]>(endpoint);
    return response || [];
  }

  async searchCarriers(query: string, limit: number = 15): Promise<CarrierItem[]> {
    if (!query || query.length < 2) {
      return [];
    }

    const searchParams = new URLSearchParams({
      q: query,
      limit: String(limit),
    });

    const endpoint = `/api/carriers/search?${searchParams}`;
    const response = await this.request<CarrierItem[]>(endpoint);
    return response || [];
  }

  async healthCheck(): Promise<{ ok: boolean }> {
    return this.request<{ ok: boolean }>('/health');
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export individual functions that call methods on the apiClient instance
export const listSchedules = (params?: SearchParams) => apiClient.listSchedules(params);
export const searchPorts = (query: string, limit?: number) => apiClient.searchPorts(query, limit);
export const searchCarriers = (query: string, limit?: number) => apiClient.searchCarriers(query, limit);
export const healthCheck = () => apiClient.healthCheck();