import type { CredentialType, DuplicateGroup, Review, Screen } from './types';

type ScreenIcon = { kind: 'glyph'; text: string } | { kind: 'trash' };

export const SCREENS: { id: Screen; icon: ScreenIcon; label: string; title: string; showCount: boolean }[] = [
  { id: 'credentials', icon: { kind: 'glyph', text: '▤' }, label: 'Credenciales', title: 'Credenciales', showCount: false },
  { id: 'audit', icon: { kind: 'glyph', text: '⬡' }, label: 'Auditoría', title: 'Auditoría local', showCount: false },
  { id: 'trash', icon: { kind: 'trash' }, label: 'Papelera', title: 'Papelera', showCount: true },
  { id: 'settings', icon: { kind: 'glyph', text: '⚙' }, label: 'Ajustes', title: 'Ajustes', showCount: false },
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
