CREATE TABLE `wgss_provider_names` (
	`normalized_name` text PRIMARY KEY NOT NULL,
	`provider_id` text NOT NULL,
	FOREIGN KEY (`provider_id`) REFERENCES `wgss_providers`(`id`) ON UPDATE no action ON DELETE no action
);

--> statement-breakpoint
INSERT INTO wgss_providers (id,name,normalized_name,kind,source_url,aliases_json,created_at,created_by)
VALUES ('registered-349ea085e7c763adbad98208','MetaMask','metamask','wallet','https://metamask.io/','["메타마스크"]',strftime('%Y-%m-%dT%H:%M:%fZ','now'),'project-owner-request');
--> statement-breakpoint
INSERT INTO wgss_provider_names (normalized_name,provider_id) VALUES ('metamask','registered-349ea085e7c763adbad98208'),('메타마스크','registered-349ea085e7c763adbad98208');
