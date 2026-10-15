export interface Statement { bind(...args: unknown[]): Statement; first<T = Record<string, unknown>>(): Promise<T | null>; all<T = Record<string, unknown>>(): Promise<{results: T[]}>; run(): Promise<unknown> }
export interface Database { prepare(sql: string): Statement; batch(statements: Statement[]): Promise<unknown[]> }
export interface Bucket { put(key: string, body: ArrayBuffer, options?: unknown): Promise<unknown>; get(key: string): Promise<{arrayBuffer(): Promise<ArrayBuffer>; body: ReadableStream} | null>; delete(key: string | string[]): Promise<void> }
export interface Runtime { DB: Database; BUCKET: Bucket; ADMIN_USER_IDS?: string; WGSS_OWNER_USER_ID?: string; WGSS_PRIVATE_SERVICE_ACCESS?: string; WGSS_ADMIN_EMAILS?: string; WGSS_SCHEDULE_ID?: string; WGSS_AI_DAILY_JOB_LIMIT?: string; BEDROCK_API_KEY?: string; BEDROCK_SONNET_INPUT_USD_PER_MILLION?: string; BEDROCK_SONNET_OUTPUT_USD_PER_MILLION?: string; BEDROCK_OPUS_INPUT_USD_PER_MILLION?: string; BEDROCK_OPUS_OUTPUT_USD_PER_MILLION?: string }
export interface Actor { userId: string | null; role: 'admin' | 'contributor' | 'anonymous'; service: boolean }
export class ApiError extends Error { constructor(public status: number, public code: string, message: string) { super(message); } }
export function getActor(userId: string | null, env: Runtime, email: string | null = null): Actor {
  const admins = new Set([...(env.ADMIN_USER_IDS || '').split(','), env.WGSS_OWNER_USER_ID || ''].map(s => s.trim()).filter(Boolean));
  // Dispatch must enforce owner-private access. This explicit deployment opt-in is for identityless service requests only.
  const trustedEmails = new Set((env.WGSS_ADMIN_EMAILS || '').split(',').map(s => s.trim().toLowerCase()).filter(Boolean));
  const service = !userId && env.WGSS_PRIVATE_SERVICE_ACCESS === 'true';
  return {userId, role: (userId && (admins.has(userId) || (email && trustedEmails.has(email.toLowerCase())))) || service ? 'admin' : userId ? 'contributor' : 'anonymous', service};
}
export function requireActor(actor: Actor, admin = false) { if (actor.role === 'anonymous') throw new ApiError(401, 'authentication_required', 'Sign in to continue.'); if (admin && actor.role !== 'admin') throw new ApiError(403, 'admin_required', 'Administrator access is required.'); }
export const actorId = (a: Actor) => a.userId || 'owner-private-service';
export const now = () => new Date().toISOString();
export const id = () => crypto.randomUUID();
export const stmt = (env: Runtime, sql: string, ...args: unknown[]) => env.DB.prepare(sql).bind(...args);
export async function rows<T = any>(env: Runtime, sql: string, ...args: unknown[]) { return (await stmt(env, sql, ...args).all<T>()).results; }
export function parse(value: unknown, fallback: any = {}) { try { return JSON.parse(String(value)); } catch { return fallback; } }
export function bounded(value: unknown, name: string, limit = 500, required = false): string { if (value == null && !required) return ''; if (typeof value !== 'string' || value.length > limit || (required && !value.trim())) throw new ApiError(400, 'invalid_input', `Invalid ${name}.`); return value.trim(); }
export function content(input: Record<string, unknown>) { const result: Record<string, string> = {}; for (const key of ['text','language','country','provider','sourceUrl','task','purpose','stage','referenceId','capturedAt','appVersion']) result[key] = bounded(input[key], key, key === 'text' ? 20000 : key === 'sourceUrl' ? 2000 : 300); if (result.sourceUrl) { try { if (new URL(result.sourceUrl).protocol !== 'https:') throw 0; } catch { throw new ApiError(400,'invalid_url','Source URL must use HTTPS.'); } } return result; }
export function auditStmt(env: Runtime, actor: Actor, action: string, entityId: string, details: unknown = {}) { return stmt(env, 'INSERT INTO wgss_audit (id,actor_id,action,entity_id,details_json,created_at) VALUES (?,?,?,?,?,?)', id(), actorId(actor), action, entityId, JSON.stringify(details), now()); }
export async function hash(bytes: ArrayBuffer | Uint8Array | string) { const data = typeof bytes === 'string' ? new TextEncoder().encode(bytes) : bytes; return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', data as BufferSource))).map(x => x.toString(16).padStart(2,'0')).join(''); }
export async function submission(env: Runtime, actor: Actor, submissionId: string, admin = false) { requireActor(actor,admin); const s = await stmt(env,'SELECT * FROM wgss_submissions WHERE id=?',submissionId).first<any>(); if (!s) throw new ApiError(404,'not_found','Submission not found.'); if (actor.role !== 'admin' && s.owner_id !== actor.userId) throw new ApiError(403,'forbidden','This submission belongs to another contributor.'); return s; }
export async function serializeSubmission(env: Runtime, s: any) { const fs = await rows(env,'SELECT id,sha256,mime,size,role,review_status,created_at FROM wgss_files WHERE submission_id=? ORDER BY created_at,rowid',s.id); return {id:s.id,ownerId:s.owner_id,kind:s.kind,status:s.status,version:s.version,title:s.title,current:parse(s.content_json),privacyReviewed:!!s.privacy_reviewed,readabilityReviewed:!!s.readability_reviewed,createdAt:s.created_at,updatedAt:s.updated_at,files:fs.map(f=>({id:f.id,sha256:f.sha256,mime:f.mime,size:f.size,role:f.role,reviewStatus:f.review_status,createdAt:f.created_at}))}; }
export function validModel(input: unknown) { const model = input || 'claude-sonnet-5'; if (!['claude-sonnet-5','claude-opus-5'].includes(String(model))) throw new ApiError(400,'invalid_model','Unsupported model.'); return String(model); }
export const defaultSettings = {scheduleEnabled:false,intervalHours:24,sourceUrls:[] as string[],marketQuery:'',model:'claude-sonnet-5'};
export async function getSettings(env: Runtime) { const row = await stmt(env,'SELECT value_json FROM wgss_settings WHERE key=?','workspace').first<any>(); return {...defaultSettings,...parse(row?.value_json)}; }

export function schedulerStatus(env: Runtime) { return env.WGSS_SCHEDULE_ID ? 'scheduled' : 'manual_only'; }
