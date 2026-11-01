import type { CredentialType, DuplicateGroup, Review, Screen } from './types';

export const SCREENS: { id: Screen; icon: string; label: string; title: string; isTrash: boolean }[] = [
  { id: 'credentials', isTrash: false, icon: '▤', label: 'Credenciales', title: 'Credenciales' },
  { id: 'audit', isTrash: false, icon: '⬡', label: 'Auditoría', title: 'Auditoría local' },
  { id: 'trash', isTrash: true, icon: '', label: 'Papelera', title: 'Papelera' },
  { id: 'settings', isTrash: false, icon: '⚙', label: 'Ajustes', title: 'Ajustes' },
];

export function labelReview(review: Review): string {
  return ({ pending: 'Pendiente', reviewed: 'Revisada', verified: 'Verificada', incorrect: 'No funciona' })[review];
}

export function labelGroup(kind: DuplicateGroup['kind']): string {
  return ({ exact: 'Copia exacta', conflict: 'Contraseñas diferentes', 'multiple-accounts': 'Varias cuentas' })[kind];
}

export function labelType(type: CredentialType): string {
  return type === 'android' ? 'Android' : 'Web';
}
