import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ApiException } from '../api/client';
import {
  createRequest,
  executeTransition,
  fetchRequests,
  updateRequest,
} from '../api/requests';
import { fetchAiSummary } from '../api/summary';
import { RequestCreateInput, RequestItem, RequestUpdateInput, SummaryResult } from '../api/types';
import { useToast } from '../context/ToastContext';

const AI_SUMMARY_STORAGE_KEY = 'moodhunter_ai_summary_cache';

export function useRequests(statusFilter?: string) {
  return useQuery<RequestItem[]>({
    queryKey: ['requests', { status: statusFilter || 'all' }],
    queryFn: () => fetchRequests(statusFilter),
    staleTime: 5000,
  });
}

export function useCreateRequest() {
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  return useMutation({
    mutationFn: (input: RequestCreateInput) => createRequest(input),
    onSuccess: (newReq) => {
      queryClient.invalidateQueries({ queryKey: ['requests'] });
      success('Solicitud creada exitosamente', `ID: ${newReq.public_id.slice(0, 8)}`);
    },
    onError: (err: unknown) => {
      if (err instanceof ApiException) {
        error(err.apiError.error, err.apiError.message);
      } else {
        error('Error al crear la solicitud', 'Por favor intenta de nuevo.');
      }
    },
  });
}

export function useUpdateRequest() {
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  return useMutation({
    mutationFn: ({ publicId, input }: { publicId: string; input: RequestUpdateInput }) =>
      updateRequest(publicId, input),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['requests'] });
      success('Solicitud actualizada', `Se guardaron los cambios de ${updated.title}`);
    },
    onError: (err: unknown) => {
      if (err instanceof ApiException) {
        error(err.apiError.error, err.apiError.message);
      } else {
        error('Error al actualizar', 'No se pudieron guardar las modificaciones.');
      }
    },
  });
}

export function useTransition() {
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  return useMutation({
    mutationFn: ({ publicId, targetStatus }: { publicId: string; targetStatus: string }) =>
      executeTransition(publicId, targetStatus),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['requests'] });
      success('Estado actualizado', `La solicitud avanzó a '${updated.status}'.`);
    },
    onError: (err: unknown) => {
      queryClient.invalidateQueries({ queryKey: ['requests'] });
      if (err instanceof ApiException) {
        if (err.status === 409) {
          error('Transición no permitida (409 Conflict)', err.apiError.message);
        } else {
          error(err.apiError.error, err.apiError.message);
        }
      } else {
        error('Error de red', 'No se pudo comunicar con el servidor para la transición.');
      }
    },
  });
}

export function useAiSummary() {
  const queryClient = useQueryClient();
  const { error } = useToast();

  // Read initial from localStorage if present
  const getInitialSummary = (): SummaryResult | undefined => {
    try {
      const stored = localStorage.getItem(AI_SUMMARY_STORAGE_KEY);
      return stored ? JSON.parse(stored) : undefined;
    } catch {
      return undefined;
    }
  };

  const summaryQuery = useQuery<SummaryResult | undefined>({
    queryKey: ['ai-summary'],
    queryFn: () => getInitialSummary(),
    staleTime: Infinity, // User manually triggers or regenerates
    initialData: getInitialSummary,
  });

  const generateMutation = useMutation({
    mutationFn: (refresh: boolean) => fetchAiSummary(refresh),
    onSuccess: (data) => {
      queryClient.setQueryData(['ai-summary'], data);
      try {
        localStorage.setItem(AI_SUMMARY_STORAGE_KEY, JSON.stringify(data));
      } catch (e) {
        console.warn('Could not persist summary to localStorage', e);
      }
    },
    onError: (err: unknown) => {
      if (err instanceof ApiException) {
        error('Error generando resumen', err.apiError.message);
      } else {
        error('Error inesperado', 'No se pudo generar el resumen.');
      }
    },
  });

  return {
    summary: summaryQuery.data,
    isGenerating: generateMutation.isPending,
    generate: generateMutation.mutate,
  };
}
