export type Review = 'pending' | 'reviewed' | 'verified' | 'incorrect';
export type Screen = 'credentials' | 'audit' | 'trash' | 'settings';
export type CredentialType = 'web' | 'android';
export type FilterType = 'all' | CredentialType;

export interface CredentialSummary {
  id: string; name: string; url: string; username: string; type: CredentialType;
  source: string; line: number; included: boolean; review: Review;
  http: boolean; invalid_uri: boolean; embedded_auth: boolean; host: string;
}
export interface CredentialDetail extends CredentialSummary {
  password: string; note: string; totp: string;
  original: { name: string; url: string; username: string; source: string; line: number };
}
export interface GroupMember extends CredentialSummary {
  match_url: boolean; match_username: boolean; match_password: boolean;
}
export interface DuplicateGroup {
  id: string; kind: 'exact' | 'conflict' | 'multiple-accounts';
  name: string; url: string; username: string; type: CredentialType;
  members: GroupMember[]; count: number; pending: boolean;
}
export interface WorkspaceState {
  files: { name: string; source: string; count: number }[];
  records: CredentialSummary[]; groups: DuplicateGroup[];
  audit: { reused: string[][]; weak: string[]; incomplete: string[]; breaches: 'not_checked' };
  stats: { total: number; included: number; excluded: number; reviewed: number; verified: number };
  can_undo: boolean;
}
export interface ImportWarningColumn { column: string; rows: number }
export interface ImportWarning { file: string; imported_count: number; columns: ImportWarningColumn[] }
/** Only a successful /api/import answers the ephemeral warnings channel; the workspace snapshot never carries it. */
export type ImportResponse = WorkspaceState & { warnings: ImportWarning[] };
export type SessionMode = 'save' | 'load';
export type SessionRequestEmits = { sessionRequested: [mode: SessionMode] };
export interface SessionInput { passphrase: string; confirmation: string; file: File | null }
export type RecordEdit = Partial<Pick<CredentialDetail, 'name' | 'url' | 'username' | 'password' | 'note' | 'totp' | 'included' | 'review'>>;
