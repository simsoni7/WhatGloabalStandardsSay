CREATE TABLE `wgss_providers` (
	`id` text PRIMARY KEY NOT NULL,
	`name` text NOT NULL,
	`normalized_name` text NOT NULL,
	`kind` text NOT NULL,
	`source_url` text DEFAULT '' NOT NULL,
	`aliases_json` text DEFAULT '[]' NOT NULL,
	`created_at` text NOT NULL,
	`created_by` text NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `wgss_providers_normalized_name_unique` ON `wgss_providers` (`normalized_name`);