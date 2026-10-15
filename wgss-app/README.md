# WGSS — public reference browser

Public UI: https://simsoni7.github.io/WhatGloabalStandardsSay/wgss/

This directory contains the integrated application source and the approved data used to build its public reader. The original dictionary at the repository root is retained.

## Build the public reader

Use Node 22.16 or later. No dependency installation is needed for the public export.

```sh
node wgss-app/scripts/build-github-pages.mjs /tmp/wgss-public
```

Publish the resulting files under `wgss/` on the existing `gh-pages` branch. The publishing workflow preserves the original dictionary and other root files. The source and output manifests record the exact snapshot and asset hashes. `integration-data` remains the source observation layer; URL projection and public release authorization are recorded separately in the generated catalog.

The project owner authorized public publication on 2026-10-16. Only the 101 previously reviewed, masked Toss images are included. Their capture dates, original URLs, app versions and actual navigation remain unknown where unknown. An image grouping does not prove a financial flow. Conditional dictionary rights and original evidence are retained; operator corrections do not imply expert translation approval.

## Server boundary

Public pages read static published snapshots. They contain no Bedrock key, privileged Sites bearer, private review queue, original unmasked captures or database credentials. Suggestions and management link to the existing owner-private operating server. Public readers cannot submit directly to that server until its identity and contribution access are deliberately opened. There is no cross-origin privileged API proxy and no embedded service token.

Public data changes when a new snapshot is exported and published. An approval on the operating server immediately updates that server's browser; it does not yet trigger this repository's snapshot export. Do not describe the public release as live synchronization.

`public-snapshot.json` contains only approved typed changes and approved record versions. Any referenced contributed media must be an exact SHA-verified, reviewed masked file. To refresh, export a new reviewed snapshot through an authorized operator session, update the data/source files on the integration branch, then publish. The bootstrap transfer is one-time; future builds use repository files and do not require the development VM to be running.

The full-stack application (`app/`, `server/`, Drizzle migrations) remains compatible with its existing Sites runtime. To operate it elsewhere, provision persistent DB/file storage, HTTPS and verified authentication before enabling access. Do not trust inbound `oai-authenticated-user-*` headers outside the managed gateway, and do not use `WGSS_PRIVATE_SERVICE_ACCESS=true` on an internet-accessible development server.
