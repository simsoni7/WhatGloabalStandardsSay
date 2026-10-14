# Integration schema v2

Raw source datasets, including frozen cfpd v1, remain unchanged. The derived SQLite index and exported JSONL/CSV use schema v2. This is a breaking field change: source evidence is no longer labeled an approved translation.

| Field | Meaning |
|---|---|
| evidence_id | Original stable source evidence identifier |
| source_concept_id | Source-specific concept, not a global verified equivalence |
| source_english / source_target | Exact source observations; search normalization does not rewrite them |
| alignment_status / alignment_basis | Source pairing observation and pairing method; not semantic approval |
| equivalence_status | unreviewed, needs_review, or not_applicable when target is missing |
| approved_translation | Always null in this release; no expert approval has been recorded |
| approval | null; any future approval must identify reviewer, evidence, context, jurisdiction and decision |
| integration_issue_ids | Links to review_queue.jsonl |
| record_type | Term, financial expression, form label, procurement classification etc. |

API requests retain english_term/target_language. Response evidence uses source_english/source_target. source_candidates and source_quoted_text are explicitly unapproved source observations. translated_text and approved_translation remain null. Exact source comparison is not a contextual correctness verdict. Model proposals remain generated_expression; a model response cannot grant semantic approval.

Migration: replace evidence.english with source_english and evidence.translation with source_target only for source quoting. Do not migrate translation consumers by silently treating source_target as an approved translation. CSV empty approval cells mean no approval. SQLite entries.source_english and entries.source_target are observed source text; FTS normalization supports search only.

Preprocessing groups same-source/same-language normalized English with multiple target forms, and normalized target forms linked to multiple English labels. These are review candidates, not confirmed errors: synonyms and polysemy are possible. Cross-source English spelling matches become candidate_links.jsonl with merge_authorized=false. No concepts are silently merged.

Mongolbank 304 retains Interest Rate / Хүү. It has a high-priority suspected source-definition mismatch, from AI triage only. 733 retains Interest / Хүү. 737 and 3377 retain Interest rate / Хүүгийн хувь and Хүүгийн хувь хэмжээ. All four remain unapproved; selecting 304 by source concept cannot suppress its suspected mismatch warning. No source term was replaced with a proposed correction.

Commercial-use eligibility and semantic equivalence are separate. The commercial export retains its approved source licenses, but all approved_translation fields are still null. FinQA remains separate from reference retrieval.

The integration report covers all indexed observations including excluded candidates and the one missing translation. Export counts cover usable nonempty source pairs only. Raw archives may retain original source-specific field names; use the integrated v2 export for retrieval.

## Source-definition review update

`semantic_review` records AI triage decisions; `generation_eligible` controls whether a source observation can enter model evidence. It is not translation approval. Decisions and all 390 review packets are preserved in derived datasets. See `docs/semantic-review.md`.
