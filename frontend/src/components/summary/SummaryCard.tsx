import React, { useState } from 'react';
import {
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Clock,
  Database,
  ListChecks,
  RefreshCw,
  ShieldAlert,
  Sparkles,
} from 'lucide-react';
import { useAiSummary } from '../../hooks/useRequests';

export const SummaryCard: React.FC = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { summary, isGenerating, generate } = useAiSummary();

  const handleGenerate = (refresh = false) => {
    generate(refresh);
  };

  const formatTimestamp = (iso: string) => {
    try {
      return new Date(iso).toLocaleTimeString('es-ES', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return iso;
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden mb-6 transition-all">
      {/* Header bar */}
      <div className="flex items-center justify-between px-5 py-3.5 bg-gradient-to-r from-slate-50 via-white to-slate-50/50 border-b border-slate-100">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-xl bg-emerald-50 text-emerald-600 border border-emerald-100">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-slate-900">Resumen Ejecutivo Inteligente</h2>
              {summary && (
                <span
                  className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full border ${
                    summary.source === 'llm'
                      ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                      : 'bg-amber-50 text-amber-800 border-amber-200'
                  }`}
                >
                  {summary.source === 'llm' ? (
                    <>
                      <Sparkles className="w-3 h-3 text-emerald-600" />
                      Gemini AI
                    </>
                  ) : (
                    <>
                      <Database className="w-3 h-3 text-amber-600" />
                      Resumen automático (IA no disponible)
                    </>
                  )}
                </span>
              )}
              {summary?.cached && (
                <span className="text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded border border-slate-200 font-mono">
                  En caché
                </span>
              )}
            </div>
            {summary && (
              <p className="text-[11px] text-slate-400 mt-0.5 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Actualizado a las {formatTimestamp(summary.generated_at)}
              </p>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleGenerate(Boolean(summary))}
            disabled={isGenerating}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl shadow-2xs hover:shadow-xs disabled:opacity-50 transition-all active:scale-95"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-slate-500 ${isGenerating ? 'animate-spin' : ''}`} />
            <span>{isGenerating ? 'Generando...' : summary ? 'Regenerar' : 'Generar resumen'}</span>
          </button>

          {summary && (
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
              aria-label={isCollapsed ? 'Expandir resumen' : 'Colapsar resumen'}
            >
              {isCollapsed ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
            </button>
          )}
        </div>
      </div>

      {/* Loading Skeleton */}
      {isGenerating && (
        <div className="p-5 space-y-4 animate-pulse">
          <div className="h-4 bg-slate-200 rounded-md w-3/4" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            <div className="h-20 bg-slate-100 rounded-xl" />
            <div className="h-20 bg-slate-100 rounded-xl" />
            <div className="h-20 bg-slate-100 rounded-xl" />
          </div>
        </div>
      )}

      {/* Empty State before first generation */}
      {!summary && !isGenerating && (
        <div className="p-6 text-center">
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Haz clic en <strong>Generar resumen</strong> para obtener una síntesis ejecutiva del
            estado de las solicitudes, alertas de estancamiento y próximas acciones recomendadas.
          </p>
        </div>
      )}

      {/* Expanded Content */}
      {summary && !isGenerating && !isCollapsed && (
        <div className="p-5 space-y-4">
          {/* Headline */}
          <div className="p-3.5 bg-slate-50/80 rounded-xl border border-slate-100">
            <p className="text-sm font-semibold text-slate-900 leading-snug">
              {summary.headline}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Highlights */}
            <div className="bg-slate-50/50 rounded-xl p-3.5 border border-slate-100 space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-bold text-slate-700 uppercase tracking-wider">
                <ListChecks className="w-3.5 h-3.5 text-emerald-600" />
                <span>Puntos Clave</span>
              </div>
              <ul className="space-y-1.5">
                {summary.highlights.map((h, i) => (
                  <li key={i} className="text-xs text-slate-600 flex items-start gap-1.5">
                    <span className="text-emerald-500 font-bold mt-0.5">•</span>
                    <span>{h}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Risks */}
            <div className="bg-rose-50/40 rounded-xl p-3.5 border border-rose-100 space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-bold text-rose-800 uppercase tracking-wider">
                <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
                <span>Riesgos y Bloqueos</span>
              </div>
              <ul className="space-y-1.5">
                {summary.risks.map((r, i) => (
                  <li key={i} className="text-xs text-rose-900 flex items-start gap-1.5">
                    <AlertTriangle className="w-3 h-3 text-rose-500 flex-shrink-0 mt-0.5" />
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Next actions */}
            <div className="bg-blue-50/40 rounded-xl p-3.5 border border-blue-100 space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-bold text-blue-800 uppercase tracking-wider">
                <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                <span>Próximas Acciones</span>
              </div>
              <ul className="space-y-1.5">
                {summary.next_actions.map((a, i) => (
                  <li key={i} className="text-xs text-blue-900 flex items-start gap-1.5">
                    <span className="text-blue-500 font-bold mt-0.5">→</span>
                    <span>{a}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
