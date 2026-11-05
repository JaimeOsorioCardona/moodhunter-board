import React, { useState } from 'react';
import { Filter, Layers, Plus, RefreshCw } from 'lucide-react';
import { RequestItem } from './api/types';
import { Board } from './components/board/Board';
import { CreateRequestModal } from './components/requests/CreateRequestModal';
import { EditRequestModal } from './components/requests/EditRequestModal';
import { SummaryCard } from './components/summary/SummaryCard';
import { STATUS_LIST, getStatusMeta } from './domain/statuses';
import { useRequests } from './hooks/useRequests';

export const App: React.FC = () => {
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingRequest, setEditingRequest] = useState<RequestItem | null>(null);

  const { data: requests = [], isLoading, isError, refetch, isRefetching } = useRequests(statusFilter || undefined);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top Navigation */}
      <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-slate-200/80 px-4 sm:px-8 py-3.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-slate-900 text-white flex items-center justify-center font-black tracking-wider text-sm shadow-sm">
              MH
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-extrabold text-slate-900 tracking-tight">
                  MOOD HUNTER
                </h1>
                <span className="text-[10px] font-semibold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full border border-emerald-200">
                  FSM Board v1.0
                </span>
              </div>
              <p className="text-xs text-slate-500 hidden sm:block">
                Tablero de solicitudes con flujo estricto de estados
              </p>
            </div>
          </div>

          {/* Right Header Controls */}
          <div className="flex items-center gap-2.5">
            {/* Filter by status */}
            <div className="relative hidden sm:flex items-center">
              <Filter className="w-3.5 h-3.5 text-slate-400 absolute left-3 pointer-events-none" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="pl-8 pr-8 py-1.5 text-xs font-medium bg-slate-100 border border-slate-200 rounded-xl text-slate-700 hover:bg-slate-200/70 focus:bg-white focus:outline-none focus:ring-2 focus:ring-slate-400 appearance-none cursor-pointer"
              >
                <option value="">Todos los estados</option>
                {STATUS_LIST.map((slug) => (
                  <option key={slug} value={slug}>
                    {getStatusMeta(slug).label}
                  </option>
                ))}
              </select>
            </div>

            {/* Refresh */}
            <button
              onClick={() => refetch()}
              disabled={isRefetching}
              className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-xl transition-all"
              title="Refrescar solicitudes"
              aria-label="Refrescar solicitudes"
            >
              <RefreshCw className={`w-4 h-4 ${isRefetching ? 'animate-spin' : ''}`} />
            </button>

            {/* Create Button */}
            <button
              onClick={() => setIsCreateOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 active:scale-95 rounded-xl shadow-sm transition-all"
            >
              <Plus className="w-4 h-4" />
              <span>Nueva Solicitud</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-8">
        {/* Executive AI Summary Component */}
        <SummaryCard />

        {/* Board Header Metrics */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
            <Layers className="w-4 h-4 text-slate-400" />
            <span>
              Mostrando {requests.length} solicitud{requests.length === 1 ? '' : 'es'}
              {statusFilter ? ` en '${getStatusMeta(statusFilter).label}'` : ''}
            </span>
          </div>
        </div>

        {/* Kanban Board */}
        <Board
          requests={requests}
          isLoading={isLoading}
          isError={isError}
          onRetry={() => refetch()}
          onEditRequest={(req) => setEditingRequest(req)}
        />
      </main>

      {/* Modals */}
      <CreateRequestModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
      />

      <EditRequestModal
        request={editingRequest}
        isOpen={Boolean(editingRequest)}
        onClose={() => setEditingRequest(null)}
      />
    </div>
  );
};
