CREATE TABLE `wgss_audit` (
	`id` text PRIMARY KEY NOT NULL,
	`actor_id` text NOT NULL,
	`action` text NOT NULL,
	`entity_id` text NOT NULL,
	`details_json` text NOT NULL,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `wgss_comparisons` (
	`id` text PRIMARY KEY NOT NULL,
	`owner_id` text NOT NULL,
	`name` text NOT NULL,
	`reference_ids_json` text NOT NULL,
	`context_json` text NOT NULL,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `wgss_files` (
	`id` text PRIMARY KEY NOT NULL,
	`submission_id` text NOT NULL,
	`object_key` text NOT NULL,
	`sha256` text NOT NULL,
	`mime` text NOT NULL,
	`size` integer NOT NULL,
	`role` text NOT NULL,
	`review_status` text DEFAULT 'pending' NOT NULL,
	`reviewed_sha256` text,
	`created_at` text NOT NULL,
	FOREIGN KEY (`submission_id`) REFERENCES `wgss_submissions`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `wgss_file_submission` ON `wgss_files` (`submission_id`);--> statement-breakpoint
CREATE TABLE `wgss_jobs` (
	`id` text PRIMARY KEY NOT NULL,
	`kind` text NOT NULL,
	`actor_id` text NOT NULL,
	`submission_id` text,
	`status` text NOT NULL,
	`model` text,
	`input_hash` text,
	`result_json` text,
	`error` text,
	`usage_json` text,
	`cost_json` text,
	`created_at` text NOT NULL,
	`completed_at` text
);
--> statement-breakpoint
CREATE TABLE `wgss_settings` (
	`key` text PRIMARY KEY NOT NULL,
	`value_json` text NOT NULL,
	`updated_at` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `wgss_submissions` (
	`id` text PRIMARY KEY NOT NULL,
	`owner_id` text NOT NULL,
	`kind` text NOT NULL,
	`status` text DEFAULT 'pending' NOT NULL,
	`version` integer DEFAULT 1 NOT NULL,
	`title` text NOT NULL,
	`content_json` text NOT NULL,
	`privacy_reviewed` integer DEFAULT 0 NOT NULL,
	`readability_reviewed` integer DEFAULT 0 NOT NULL,
	`created_at` text NOT NULL,
	`updated_at` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `wgss_submission_owner` ON `wgss_submissions` (`owner_id`);--> statement-breakpoint
CREATE TABLE `wgss_versions` (
	`id` text PRIMARY KEY NOT NULL,
	`submission_id` text NOT NULL,
	`version` integer NOT NULL,
	`title` text NOT NULL,
	`content_json` text NOT NULL,
	`status` text NOT NULL,
	`actor_id` text NOT NULL,
	`created_at` text NOT NULL,
	FOREIGN KEY (`submission_id`) REFERENCES `wgss_submissions`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE UNIQUE INDEX `wgss_version_unique` ON `wgss_versions` (`submission_id`,`version`);