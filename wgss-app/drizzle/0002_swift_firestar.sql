CREATE TABLE `wgss_publications` (
	`id` text PRIMARY KEY NOT NULL,
	`target_type` text NOT NULL,
	`target_id` text NOT NULL,
	`revision` integer NOT NULL,
	`source_submission_id` text,
	`source_version` integer NOT NULL,
	`patch_json` text NOT NULL,
	`state` text DEFAULT 'applied' NOT NULL,
	`actor_id` text NOT NULL,
	`created_at` text NOT NULL,
	FOREIGN KEY (`source_submission_id`) REFERENCES `wgss_submissions`(`id`) ON UPDATE no action ON DELETE set null
);
--> statement-breakpoint
CREATE UNIQUE INDEX `wgss_publication_revision` ON `wgss_publications` (`target_type`,`target_id`,`revision`);--> statement-breakpoint
CREATE INDEX `wgss_publication_source` ON `wgss_publications` (`source_submission_id`);