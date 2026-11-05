import { apiClient } from './client';
import { SummaryResult } from './types';

export async function fetchAiSummary(refresh: boolean = false): Promise<SummaryResult> {
  const query = refresh ? '?refresh=true' : '';
  return apiClient<SummaryResult>(`/requests/ai-summary${query}`, {
    method: 'POST',
  });
}
