import { apiClient } from './client';
import {
  AllowedTransitionsResponse,
  RequestCreateInput,
  RequestItem,
  RequestUpdateInput,
} from './types';

export async function fetchRequests(status?: string): Promise<RequestItem[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : '';
  return apiClient<RequestItem[]>(`/requests${query}`);
}

export async function fetchRequestById(publicId: string): Promise<RequestItem> {
  return apiClient<RequestItem>(`/requests/${publicId}`);
}

export async function createRequest(input: RequestCreateInput): Promise<RequestItem> {
  return apiClient<RequestItem>('/requests', {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export async function updateRequest(
  publicId: string,
  input: RequestUpdateInput
): Promise<RequestItem> {
  return apiClient<RequestItem>(`/requests/${publicId}`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  });
}

export async function fetchAllowedTransitions(
  publicId: string
): Promise<AllowedTransitionsResponse> {
  return apiClient<AllowedTransitionsResponse>(`/requests/${publicId}/allowed-transitions`);
}

export async function executeTransition(
  publicId: string,
  targetStatus: string
): Promise<RequestItem> {
  return apiClient<RequestItem>(`/requests/${publicId}/transitions`, {
    method: 'POST',
    body: JSON.stringify({ target_status: targetStatus }),
  });
}
