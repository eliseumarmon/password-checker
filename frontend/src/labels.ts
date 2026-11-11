import type { CredentialType, DuplicateGroup, RecordEdit, Review, Screen, UndoStep } from './types';

type ScreenIcon = { kind: 'glyph'; text: string } | { kind: 'trash' };

export const SCREENS: { id: Screen; icon: ScreenIcon; label: string; title: string; showCount: boolean }[] = [
  { id: 'credentials', icon: { kind: 'glyph', text: '▤' }, label: 'Credenciales', title: 'Credenciales', showCount: false },
  { id: 'audit', icon: { kind: 'glyph', text: '⬡' }, label: 'Auditoría', title: 'Auditoría local', showCount: false },
  { id: 'trash', icon: { kind: 'trash' }, label: 'Papelera', title: 'Papelera', showCount: true },
  { id: 'settings', icon: { kind: 'glyph', text: '⚙' }, label: 'Ajustes', title: 'Ajustes', showCount: false },
];

/** Every review state, in the order the review moves through them. */
export const REVIEWS: readonly Review[] = ['pending', 'reviewed', 'incorrect'];

export function labelReview(review: Review): string {
  return ({ pending: 'Pendiente', reviewed: 'Revisada', incorrect: 'No funciona' })[review];
}

export function labelGroup(kind: DuplicateGroup['kind']): string {
  return ({ exact: 'Copia exacta', conflict: 'Versiones diferentes', 'multiple-accounts': 'Varias cuentas' })[kind];
}

export function labelType(type: CredentialType): string {
  return type === 'android' ? 'Android' : 'Web';
}

export function labelOrigin(origin: string): string {
  return origin === 'unknown' ? 'Desconocido' : origin;
}

const FIELD_LABELS: Record<keyof RecordEdit, string> = {
  name: 'Nombre', url: 'URL', username: 'Usuario', password: 'Contraseña', totp: 'Código 2FA',
  note: 'Notas', review: 'Estado de revisión', included: 'Papelera',
};

function joinList(items: string[]): string {
  return items.length < 2 ? items.join('') : `${items.slice(0, -1).join(', ')} y ${items[items.length - 1]}`;
}

/** What an undo step did, by record and field names only, never values (undo-ux S2). */
export function describeStep(step: UndoStep): string {
  const name = step.name === null ? null : `«${step.name}»`;
  switch (step.action) {
    case 'edit': return `${name ?? 'Credencial'} guardada. Cambió: ${joinList(step.fields.map(field => FIELD_LABELS[field]))}.`;
    case 'trash': return step.count === 1
      ? `${name ?? 'Credencial'} en la papelera.`
      : `${step.count} registros${name ? ` de ${name}` : ''} en la papelera.`;
    case 'restore': return `${name ?? 'Credencial'} restaurada.`;
    case 'merge': return `Copias exactas fusionadas: ${step.count} ${step.count === 1 ? 'registro' : 'registros'} a la papelera.`;
  }
}
