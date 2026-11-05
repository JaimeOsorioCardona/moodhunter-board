import React, { useState } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { RequestItem } from '../../api/types';
import { STATUS_LIST, StatusSlug, getStatusMeta } from '../../domain/statuses';
import { StatusColumn } from './StatusColumn';

interface BoardProps {
  requests: RequestItem[];
  isLoading: boolean;
  isError: boolean;
  onRetry: () => void;
  onEditRequest: (request: RequestItem) => void;
}

export const Board: React.FC<BoardProps> = ({
  requests,
  isLoading,
  isError,
  onRetry,
  onEditRequest,
}) => {
  const [activeMobileTab, setActiveMobileTab] = useState<StatusSlug>('created');

  // Group requests by status
  const groupedRequests = STATUS_LIST.reduce<Record<StatusSlug, RequestItem[]>>(
    (acc, status) => {
      acc[status] = requests.filter((r) => r.status === status);
      return acc;
    },
    {
      created: [],
      in_review: [],
      in_progress: [],
      paused: [],
      done: [],
    }
  );

  if (isLoading) {
    return (
      <div className="flex gap-4 overflow-x-auto pb-4">
        {STATUS_LIST.map((status) => (
          <div
            key={status}
            className="min-w-[280px] max-w-[340px] w-full flex-1 bg-slate-100 rounded-2xl h-[480px] animate-pulse p-4 space-y-4"
          >
            <div className="h-6 bg-slate-200 rounded-md w-1/2" />
            <div className="h-32 bg-slate-200 rounded-xl" />
            <div className="h-28 bg-slate-200 rounded-xl" />
          </div>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-rose-50 border border-rose-200 rounded-2xl p-8 text-center max-w-md mx-auto my-12">
        <AlertTriangle className="w-10 h-10 text-rose-500 mx-auto mb-3" />
        <h3 className="text-base font-bold text-rose-900">Error al cargar el tablero</h3>
        <p className="text-xs text-rose-700 mt-1 mb-4">
          No se pudo conectar con el servidor para obtener las solicitudes.
        </p>
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 rounded-xl shadow-sm transition-all"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Reintentar conexión
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Mobile Tab Selector (Visible only on small screens < md) */}
      <div className="md:hidden mb-4 overflow-x-auto pb-2 flex gap-1.5 no-scrollbar">
        {STATUS_LIST.map((status) => {
          const meta = getStatusMeta(status);
          const count = groupedRequests[status].length;
          const isActive = activeMobileTab === status;

          return (
            <button
              key={status}
              onClick={() => setActiveMobileTab(status)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all border ${
                isActive
                  ? 'bg-slate-900 text-white border-slate-900 shadow-sm'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              <span>{meta.label}</span>
              <span
                className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                  isActive ? 'bg-slate-700 text-white' : 'bg-slate-100 text-slate-700'
                }`}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Desktop Multi-column Kanban View (md and up) */}
      <div className="hidden md:flex gap-4 overflow-x-auto pb-6 items-start">
        {STATUS_LIST.map((status) => (
          <StatusColumn
            key={status}
            status={status}
            requests={groupedRequests[status]}
            onEditRequest={onEditRequest}
          />
        ))}
      </div>

      {/* Mobile Single Column Active View */}
      <div className="md:hidden">
        <StatusColumn
          status={activeMobileTab}
          requests={groupedRequests[activeMobileTab]}
          onEditRequest={onEditRequest}
        />
      </div>
    </div>
  );
};
