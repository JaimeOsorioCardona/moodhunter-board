export type StatusSlug = 'created' | 'in_review' | 'in_progress' | 'paused' | 'done';

export interface StatusMeta {
  code: StatusSlug;
  label: string;
  description: string;
  color: {
    bgLight: string;
    text: string;
    border: string;
    badgeBg: string;
    badgeText: string;
    dot: string;
    headerAccent: string;
  };
}

export const STATUS_LIST: StatusSlug[] = [
  'created',
  'in_review',
  'in_progress',
  'paused',
  'done',
];

export const STATUS_META: Record<StatusSlug, StatusMeta> = {
  created: {
    code: 'created',
    label: 'Creada',
    description: 'Solicitud recién registrada en el sistema',
    color: {
      bgLight: 'bg-slate-50',
      text: 'text-slate-700',
      border: 'border-slate-200',
      badgeBg: 'bg-slate-100',
      badgeText: 'text-slate-800',
      dot: 'bg-slate-400',
      headerAccent: 'border-t-slate-400',
    },
  },
  in_review: {
    code: 'in_review',
    label: 'En revisión',
    description: 'En evaluación técnica y de negocio',
    color: {
      bgLight: 'bg-amber-50/50',
      text: 'text-amber-800',
      border: 'border-amber-200',
      badgeBg: 'bg-amber-100',
      badgeText: 'text-amber-900',
      dot: 'bg-amber-500',
      headerAccent: 'border-t-amber-500',
    },
  },
  in_progress: {
    code: 'in_progress',
    label: 'En progreso',
    description: 'Trabajo activo de desarrollo o ejecución',
    color: {
      bgLight: 'bg-blue-50/50',
      text: 'text-blue-800',
      border: 'border-blue-200',
      badgeBg: 'bg-blue-100',
      badgeText: 'text-blue-900',
      dot: 'bg-blue-500',
      headerAccent: 'border-t-blue-500',
    },
  },
  paused: {
    code: 'paused',
    label: 'Pausada',
    description: 'Detenida temporalmente por bloqueo o espera',
    color: {
      bgLight: 'bg-purple-50/50',
      text: 'text-purple-800',
      border: 'border-purple-200',
      badgeBg: 'bg-purple-100',
      badgeText: 'text-purple-900',
      dot: 'bg-purple-500',
      headerAccent: 'border-t-purple-500',
    },
  },
  done: {
    code: 'done',
    label: 'Finalizada',
    description: 'Completada y aprobada satisfactoriamente',
    color: {
      bgLight: 'bg-emerald-50/50',
      text: 'text-emerald-800',
      border: 'border-emerald-200',
      badgeBg: 'bg-emerald-100',
      badgeText: 'text-emerald-900',
      dot: 'bg-emerald-500',
      headerAccent: 'border-t-emerald-500',
    },
  },
};

export function getStatusMeta(slug: string): StatusMeta {
  if (slug in STATUS_META) {
    return STATUS_META[slug as StatusSlug];
  }
  return {
    code: 'created',
    label: slug,
    description: '',
    color: {
      bgLight: 'bg-gray-50',
      text: 'text-gray-700',
      border: 'border-gray-200',
      badgeBg: 'bg-gray-100',
      badgeText: 'text-gray-800',
      dot: 'bg-gray-400',
      headerAccent: 'border-t-gray-400',
    },
  };
}
