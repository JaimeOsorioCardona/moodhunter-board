import React from 'react';
import { RequestItem } from '../../api/types';
import { getStatusMeta, StatusSlug } from '../../domain/statuses';
import { RequestCard } from './RequestCard';

interface StatusColumnProps {
  status: StatusSlug;
  requests: RequestItem[];
  onEditRequest: (request: RequestItem) => void;
}

export const StatusColumn: React.FC<StatusColumnProps> = ({
  status,
  requests,
  onEditRequest,
}) => {
  const meta = getStatusMeta(status);

  return (
    <div
      className={`flex flex-col min-w-[280px] max-w-[340px] w-full flex-1 bg-slate-100/70 rounded-2xl border ${meta.color.border} overflow-hidden shadow-2xs border-t-4 ${meta.color.headerAccent}`}
    >
      {/* Column Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-white/60 backdrop-blur-xs border-b border-slate-200/60">
        <div className="flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full ${meta.color.dot}`} />
          <h3 className="text-sm font-bold text-slate-800">{meta.label}</h3>
        </div>
        <span
          className={`text-xs font-semibold px-2 py-0.5 rounded-full ${meta.color.badgeBg} ${meta.color.badgeText}`}
        >
          {requests.length}
        </span>
      </div>

      {/* Cards Scrollable Body */}
      <div className="p-3 flex-1 overflow-y-auto space-y-3 min-h-[420px] max-h-[calc(100vh-280px)]">
        {requests.length > 0 ? (
          requests.map((request) => (
            <RequestCard
              key={request.public_id}
              request={request}
              onEdit={onEditRequest}
            />
          ))
        ) : (
          <div className="flex flex-col items-center justify-center h-48 border border-dashed border-slate-200 rounded-xl p-4 text-center">
            <p className="text-xs text-slate-400 font-medium">Sin solicitudes</p>
            <p className="text-[11px] text-slate-400 mt-0.5">{meta.description}</p>
          </div>
        )}
      </div>
    </div>
  );
};
