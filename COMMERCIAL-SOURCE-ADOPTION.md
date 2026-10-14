# Commercial financial language-pack adoption — 2026-10-14

Five source collectors submitted original acquisition evidence to a separate data-management review. Only sources with documented commercial reuse permission and identifiable bilingual evidence entered the reference registry. This is an evidence-based machine review, not professional legal or linguistic approval.

| Source | Accepted pairs | Reuse basis | Financial scope |
|---|---:|---|---|
| CFPB translated remittance fact sheets | 85: Arabic 16, Haitian Creole 35, Tagalog 34 | CFPB-created information public-domain policy, original policy snapshot retained | US remittance consumer-rights headings and contextual expressions |
| Government of Canada CKAN extension | 117: French | Official source-code/associated documentation MIT notice retained | 94 currency names; 23 government reporting, contracts and expense labels |
| EU Publications Office OP-TED eForms CPV | 1,958: 89 concepts × 22 languages | CC BY 4.0, original license and attribution retained | Division 66 government-procurement financial and insurance service labels |
| Philippine financial authorities | 0 | Original texts/permission not acquired | Blocked; not admitted |
| Arabic central banks/regulators | 0 | Original texts/permission not acquired | Blocked; not admitted |

Total newly admitted reference records: **2,160**, covering 25 destination languages, 24 of which are new to the previously distributed seven-language collection. French is represented in both Canada and EU packs; Spanish already existed. No accepted record was produced by translating English-only source text. These packs are references, not independent translation-quality benchmarks.

## Feedback and exclusions

The data manager excluded one Tagalog cancellation passage whose official translation omits the English business-day qualification. One Canadian French label, `Nombre do soumissions`, was excluded as a suspected source typo without silently correcting it. All 89 Irish CPV labels were English fallbacks and excluded. Original excluded evidence remains available separately; none enters the default reference index.

Canada currency names preserve a source-code snapshot, including potentially historical currencies. They are not a current currency-validity registry. Official CPV labels describe procurement services and must retain that context; they are not a universal consumer banking dictionary. CFPB parallel expressions can paraphrase or explain, and their 2021 legal guidance is not guaranteed current. Arabic short expressions were checked against rendered originals because PDF RTL/font extraction was damaged; source extraction and image locators remain preserved.

## Commercial export boundary

`datasets/language_packs/commercial_policy.json` allows cfpd v1 and the three new accepted packs in the commercial terminology export. All five original cfpd PDFs expressly identify the glossary as created and used by CFPB; the original policy snapshot permits reuse of CFPB-created public-domain information. Frozen cfpd files were not modified. Third-party exceptions and CFPB trademarks remain excluded from blanket reuse claims.

Mongolbank and Nepal Bank remain in the pre-existing collection, but their commercial redistribution permission is unverified and they are excluded from the commercial-only export. Official availability is not evidence of permission. FinQA remains a separately admitted MIT numerical-reasoning benchmark; it does not enter the terminology export or increase the bilingual pair count.

MultiFin is rejected for commercial adoption due to CC BY-NC 4.0. Its published collection methodology may inform independent collection from original publishers only when each original source permits commercial reuse. Translating, paraphrasing or relabeling restricted records does not remove their restrictions.

## Retained evidence and admission checks

Each new accepted pack under `datasets/language_packs/` contains checksummed evidence JSONL, original source files, original license or policy, source identifiers, financial context, jurisdiction, and a manifest with commercial-use basis. Canada pairs use identical YAML fields or currency-object keys. EU pairs use the same Genericode row and CPV code. CFPB pairs use explicitly mapped sections in officially published language versions, with page/block/bounding-box locators. Source-specific concept namespaces prevent silent cross-institution merging.

All records remain `candidate`, `human_review: false`. Admission establishes documented permission and source-attested correspondence; it does not establish semantic perfection, current law, financial suitability, or expert translation approval. Published source text is treated as data, not executable instructions. Acquisition reports for inaccessible sources are retained under `datasets/source_collection/` without adopting their absent content.
