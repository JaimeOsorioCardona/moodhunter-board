import React, { useState } from 'react';
import { ArrowRight, Clock, Edit2, Play, Pause, Check } from 'lucide-react';
import { RequestItem } from '../../api/types';
import { getStatusMeta, StatusSlug } from '../../domain/statuses';
import { useTransition } from '../../hooks/useRequests';

interface RequestCardProps {
  request: RequestItem;
  onEdit: (request: RequestItem) => void;
}

export const RequestCard: React.FC<RequestCardProps> = ({ request, onEdit }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const transitionMutation = useTransition();

  const handleTransition = (target: string) => {
    transitionMutation.mutate({
      publicId: request.public_id,
      targetStatus: target,
    });
  };

  const getTransitionIcon = (target: string) => {
    switch (target) {
      case 'in_progress':
        return <Play className="w-3 h-3 text-blue-600" />;
      case 'paused':
        return <Pause className="w-3 h-3 text-purple-600" />;
      case 'done':
        return <Check className="w-3 h-3 text-emerald-600" />;
      default:
        return <ArrowRight className="w-3 h-3 text-slate-500" />;
    }
  };

  const formatDate = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString('es-ES', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="group bg-white rounded-xl border border-slate-200/90 hover:border-slate-300 shadow-sm hover:shadow transition-all p-4 space-y-3">
      {/* Top Bar: Reference ID & Edit Action */}
      <div className="flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-1.5 font-mono">
          <span className="bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded text-[11px] font-medium">
            #{request.public_id.slice(0, 8)}
          </span>
          <span className="text-[11px] text-slate-400">v{request.version}</span>
        </div>

        <button
          onClick={() => onEdit(request)}
          className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-slate-700 p-1 hover:bg-slate-100 rounded-lg transition-all"
          title="Editar título y descripción"
          aria-label="Editar solicitud"
        >
          <Edit2 className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Title */}
      <h4 className="text-sm font-semibold text-slate-900 leading-snug break-words">
        {request.title}
      </h4>

      {/* Description */}
      {request.description && (
        <div className="text-xs text-slate-600">
          <p className={isExpanded ? 'whitespace-pre-line' : 'line-clamp-2'}>
            {request.description}
          </p>
          {request.description.length > 80 && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-[11px] text-emerald-600 hover:text-emerald-700 font-medium mt-0.5"
            >
              {isExpanded ? 'Ver menos' : 'Ver más'}
            </button>
          )}
        </div>
      )}

      {/* Timestamp */}
      <div className="flex items-center gap-1 text-[11px] text-slate-400 pt-1">
        <Clock className="w-3 h-3 text-slate-400" />
        <span>Actualizado: {formatDate(request.updated_at)}</span>
      </div>

      {/* Allowed Transitions Actions */}
      <div className="pt-2 border-t border-slate-100">
        {request.allowed_transitions.length > 0 ? (
          <div className="space-y-1.5">
            <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-400 block">
              Transiciones disponibles:
            </span>
            <div className="flex flex-wrap gap-1.5">
              {request.allowed_transitions.map((target) => {
                const targetMeta = getStatusMeta(target as StatusSlug);
                const isTargeting =
                  transitionMutation.isPending &&
                  transitionMutation.variables?.targetStatus === target;

                return (
                  <button
                    key={target}
                    onClick={() => handleTransition(target)}
                    disabled={transitionMutation.isPending}
                    className="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-lg border border-slate-200 bg-slate-50 hover:bg-white hover:border-slate-300 text-slate-700 shadow-2xs hover:shadow-xs transition-all active:scale-95 disabled:opacity-50"
                  >
                    {getTransitionIcon(target)}
                    <span>{targetMeta.label}</span>
                    {isTargeting && (
                      <span className="w-2 h-2 rounded-full border-2 border-slate-400 border-t-transparent animate-spin ml-0.5" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ) : (
          <p className="text-[11px] text-slate-400 italic">
            Estado finalizado (terminal). Sin transiciones permitidas.
          </p>
        )}
      </div>
    </div>
  );
};
