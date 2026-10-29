export type Review = 'pending' | 'reviewed' | 'verified' | 'incorrect';
export type Screen = 'credentials' | 'audit' | 'settings';
export type FilterType = 'all' | 'web' | 'android';

export interface CredentialSummary {
  id: string; name: string; url: string; username: string; type: 'web' | 'android';
  source: string; line: number; included: boolean; review: Review;
  http: boolean; invalid_uri: boolean; embedded_auth: boolean; host: string;
}
export interface CredentialDetail extends CredentialSummary {
  password: string; note: string;
  original: { name: string; url: string; username: string; source: string; line: number };
}
export interface GroupMember extends CredentialSummary {
  match_url: boolean; match_username: boolean; match_password: boolean;
}
export interface DuplicateGroup {
  id: string; kind: 'exact' | 'conflict' | 'multiple-accounts';
  name: string; url: string; username: string; type: 'web' | 'android';
  members: GroupMember[]; count: number; pending: boolean;
}
export interface WorkspaceState {
  files: { name: string; source: string; count: number }[];
  records: CredentialSummary[]; groups: DuplicateGroup[];
  audit: { reused: string[][]; weak: string[]; incomplete: string[]; breaches: 'not_checked' };
  stats: { total: number; included: number; excluded: number; reviewed: number; verified: number };
  can_undo: boolean; session_saved: false;
}
export type RecordEdit = Partial<Pick<CredentialDetail, 'name' | 'url' | 'username' | 'password' | 'note' | 'included' | 'review'>>;
