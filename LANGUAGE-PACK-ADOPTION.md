# Financial language-pack adoption

## Separate assets

A reference language pack contains source-attested English–target-language terms or financial expressions. It is not a translation-quality benchmark. A benchmark needs distinct held-out prompts, task definitions, evaluation criteria, and reviewed reference answers. Source-overlapping glossary material must not be reported as independent held-out evaluation.

## Admission gates

1. An identifiable official financial institution, regulator, or public financial-education publisher.
2. Explicit bilingual pair evidence: a bilingual row/label or stable shared source identifier. Similar pages or list positions alone are insufficient.
3. Original file or response, SHA256, source URL, and row/page locator retained.
4. Source financial context and jurisdiction retained; general administrative labels excluded unless financial context is necessary and explicit.
5. Applicable redistribution terms checked and recorded. Inaccessible or unclear permission sources stay pending; accessibility alone is not permission.
6. Exact source text retained; duplicates identified without merging institution-specific concepts.
7. No invented translations or expert-review claims. Machine extraction/review is labeled candidate with `human_review: false`.

## Research feedback cycle

The researcher submits candidate metadata and source files. The data manager records accepted, rejected, or further-research decisions and concrete reasons. A pending source is not exported through the default reference index. Accepted packs have an adoption manifest and checksummed evidence JSONL; the research feedback log also retains sources that were not adopted.

## Benchmark readiness

A source-attested term pair can support terminology lookup and a diagnostic glossary-consistency check. It cannot establish translation accuracy in unseen financial situations. Semantic evaluation remains pending until separate examples and appropriately reviewed references exist; consultation or expert review is not implied by an official publisher.

## Provisional candidate review

CFPB remittance-rights fact sheets are being checked for Arabic, Haitian Creole, and Tagalog. The proposed asset is a financial-guidance expression reference pack, not a comprehensive dictionary. Admission is pending original PDF evidence, explicitly corresponding headings or sentences, and a documented reuse basis. No pending candidate is listed in the registry.

## Other financial benchmark tasks

Published multilingual financial classification or question-answering benchmarks may be admitted as separate benchmark packs if original data, labels, splits, language coverage, license, and checksums are verified. Their task names must remain explicit: a financial classification benchmark does not evaluate translation or terminology verification. Such records never enter the reference glossary index and never increase the number of English–target-language glossary pairs. Existing train/dev/test splits and overlap warnings must be preserved.

## Current reviewed decisions

- **FinQA accepted as a separate financial numerical-reasoning benchmark:** 1,147 original English public-test records, no new glossary languages or pairs. Repository MIT notice, original data and provenance retained. Fourteen empty textual answers remain flagged; execution answers and programs exist for all records. Inputs exclude gold annotations and source retrieved model-input fields. No evaluation has been run.
- **CFPB Arabic/Haitian Creole/Tagalog remittance expressions pending:** official source and public-domain reuse policy identified, but translated PDF originals remain inaccessible. No reference pairs adopted.
- **MultiFin pending:** official author repository identifies CC BY-NC 4.0, while original data download is blocked. No data adopted; any later acquisition must be separated as noncommercial research-only.
- **FLUE pending:** constituent source datasets and their individual redistribution terms remain unverified; umbrella repository license does not suffice.

The data manager returned the unresolved multilingual candidates for further research. Existing frozen cfpd v1 and previously accepted glossary records were not changed by these decisions.
