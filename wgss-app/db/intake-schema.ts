import {sqliteTable,text,integer} from 'drizzle-orm/sqlite-core';

// Increment and admission happen in the same D1 transaction as creation.
// NOT NULL turns exhausted quota into a rollback of the entire batch.
export const intakeQuota=sqliteTable('wgss_intake_quota',{
 id:text('id').primaryKey(),used:integer('used').notNull(),limit:integer('limit').notNull(),updatedAt:text('updated_at').notNull(),
});
