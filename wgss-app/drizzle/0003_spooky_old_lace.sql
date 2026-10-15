CREATE TABLE `wgss_intake_quota` (
	`id` text PRIMARY KEY NOT NULL,
	`used` integer NOT NULL,
	`limit` integer NOT NULL,
	`updated_at` text NOT NULL
);
