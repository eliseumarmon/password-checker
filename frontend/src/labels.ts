import type { DuplicateGroup, Review, Screen } from './types';

export const SCREENS: { id: Screen; icon: string; label: string; title: string }[] = [
  { id: 'credentials', icon: '▤', label: 'Credenciales', title: 'Credenciales' },
  { id: 'audit', icon: '⬡', label: 'Auditoría', title: 'Auditoría local' },
  { id: 'trash', icon: '', label: 'Papelera', title: 'Papelera' },
  { id: 'settings', icon: '⚙', label: 'Ajustes', title: 'Ajustes' },
];

export function labelReview(review: Review): string {
  return ({ pending: 'Pendiente', reviewed: 'Revisada', verified: 'Verificada', incorrect: 'No funciona' })[review];
}

export function labelGroup(kind: DuplicateGroup['kind']): string {
  return ({ exact: 'Copia exacta', conflict: 'Contraseñas diferentes', 'multiple-accounts': 'Varias cuentas' })[kind];
}

export function labelType(type: 'web' | 'android'): string {
  return type === 'android' ? 'Android' : 'Web';
}
