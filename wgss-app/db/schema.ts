import { sqliteTable, text, integer, uniqueIndex, index } from 'drizzle-orm/sqlite-core';

export const submissions = sqliteTable('wgss_submissions', {
  id: text('id').primaryKey(), ownerId: text('owner_id').notNull(), kind: text('kind').notNull(),
  status: text('status').notNull().default('pending'), version: integer('version').notNull().default(1),
  title: text('title').notNull(), contentJson: text('content_json').notNull(),
  privacyReviewed: integer('privacy_reviewed').notNull().default(0), readabilityReviewed: integer('readability_reviewed').notNull().default(0),
  createdAt: text('created_at').notNull(), updatedAt: text('updated_at').notNull(),
}, t => [index('wgss_submission_owner').on(t.ownerId)]);
export const versions = sqliteTable('wgss_versions', {
  id: text('id').primaryKey(), submissionId: text('submission_id').notNull().references(() => submissions.id, { onDelete: 'cascade' }),
  version: integer('version').notNull(), title: text('title').notNull(), contentJson: text('content_json').notNull(),
  status: text('status').notNull(), reviewReason: text('review_reason'), actorId: text('actor_id').notNull(), createdAt: text('created_at').notNull(),
}, t => [uniqueIndex('wgss_version_unique').on(t.submissionId, t.version)]);
export const files = sqliteTable('wgss_files', {
  id: text('id').primaryKey(), submissionId: text('submission_id').notNull().references(() => submissions.id, { onDelete: 'cascade' }),
  objectKey: text('object_key').notNull(), sha256: text('sha256').notNull(), mime: text('mime').notNull(), size: integer('size').notNull(),
  role: text('role').notNull(), reviewStatus: text('review_status').notNull().default('pending'), reviewedSha256: text('reviewed_sha256'),
  createdAt: text('created_at').notNull(),
}, t => [index('wgss_file_submission').on(t.submissionId)]);
export const comparisons = sqliteTable('wgss_comparisons', {
  id: text('id').primaryKey(), ownerId: text('owner_id').notNull(), name: text('name').notNull(),
  referenceIdsJson: text('reference_ids_json').notNull(), contextJson: text('context_json').notNull(), createdAt: text('created_at').notNull(),
});
export const jobs = sqliteTable('wgss_jobs', {
  id: text('id').primaryKey(), kind: text('kind').notNull(), actorId: text('actor_id').notNull(), submissionId: text('submission_id'),
  status: text('status').notNull(), model: text('model'), inputHash: text('input_hash'), resultJson: text('result_json'), error: text('error'),
  usageJson: text('usage_json'), costJson: text('cost_json'), createdAt: text('created_at').notNull(), completedAt: text('completed_at'),
});
export const audit = sqliteTable('wgss_audit', {
  id: text('id').primaryKey(), actorId: text('actor_id').notNull(), action: text('action').notNull(), entityId: text('entity_id').notNull(),
  detailsJson: text('details_json').notNull(), createdAt: text('created_at').notNull(),
});
export const settings = sqliteTable('wgss_settings', {
  key: text('key').primaryKey(), valueJson: text('value_json').notNull(), updatedAt: text('updated_at').notNull(),
});

export const publications = sqliteTable('wgss_publications', {
  id: text('id').primaryKey(), targetType: text('target_type').notNull(), targetId: text('target_id').notNull(),
  revision: integer('revision').notNull(), sourceSubmissionId: text('source_submission_id').references(()=>submissions.id,{onDelete:'set null'}),
  sourceVersion: integer('source_version').notNull(), patchJson: text('patch_json').notNull(), state: text('state').notNull().default('applied'),
  actorId: text('actor_id').notNull(), createdAt: text('created_at').notNull(),
},t=>[uniqueIndex('wgss_publication_revision').on(t.targetType,t.targetId,t.revision),index('wgss_publication_source').on(t.sourceSubmissionId)]);
