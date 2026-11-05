import { ApiError } from './types';

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

export class ApiException extends Error {
  apiError: ApiError;
  status: number;

  constructor(status: number, apiError: ApiError) {
    super(apiError.message || `Error HTTP ${status}`);
    this.name = 'ApiException';
    this.status = status;
    this.apiError = apiError;
  }
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    ...(options.headers || {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorData: ApiError;
    try {
      errorData = await response.json();
    } catch {
      errorData = {
        error: 'unknown_error',
        message: `Error del servidor (${response.status}: ${response.statusText})`,
      };
    }
    throw new ApiException(response.status, errorData);
  }

  return response.json() as Promise<T>;
}
