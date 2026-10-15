# Batch 8 — Malaysia financial-statistics metadata

## Source and rights

144 newly observed English–Malay pairs from the Malaysian government's official `data-gov-my/datagovmy-meta` repository at immutable commit `a34682cf22a1da9de5520a27f5f3fc5f7c86b06f`. The repository LICENSE explicitly grants MIT commercial reuse; the verbatim license is retained in `datasets/source_collection/batch8_malaysia/raw/LICENSE`. This license conclusion applies to the repository metadata files, **not** to linked BNM source datasets or arbitrary Malaysian bank web pages.

All 23 original JSON metadata files are retained, with pinned public URLs, SHA-256 hashes, JSON source keys, original values, issuer/data-source context and collection script. The English and Malay strings come from matching `title_en/title_ms`, the same `translations_en/translations_ms` dictionary key, or `title_en/title_ms` in the same `fields` array object. No translated text was generated to form these pairs.

## Financial coverage

Interest and deposit-rate series, monetary aggregates, government borrowing and securities, direct/indirect taxation, operating expenditure, BOP accounts, foreign direct investment, income, EPF dividends, exchange-rate labels, card payment instruments and ATM withdrawals. These are statistical or operational source labels, not a normative terminology standard. In particular, BOP `Current Account` is not silently merged with a consumer bank current account.

Examples: `Treasury Bills` → `Bil-bil Perbendaharaan`; `Debt service` → `Khidmat hutang`; `Credit Card (online)` → `Kad Kredit (dalam talian)`; `Weighted Avg Savings Deposit Rate` → `Kadar Deposit Tabungan Purata Berwajaran`.

## Exclusions and caution

229 observations were excluded from this acquisition's pre-deduplication pass: exact existing/intra-batch English–Malay pairs, generic chart actions/categories, unchanged English strings, denomination-number variants and source defects. The existing 65 dashboard observations are not recounted. Notable original errors are preserved in the raw files and exclusion log rather than repaired: M3 deposit label gains `Kadar` (rate), `Total Expenditure` is paired with Malay total revenue, banknote labels use `Nota`, `Acutal` and `Perbelajaan` are misspellings, and an income-component field incorrectly says expenditure type.

`Median Income` occurs with `Pendapatan Penengah` and `Pendapatan Median`. These remain separate source observations; retaining both is not a declaration of interchangeable preferred terminology.

`money_banking_lookup.csv` at the documented official storage URL was attempted with ordinary TLS and returned proxy HTTP 403. It was not acquired, relayed through an alternate host, or counted. Its unavailable contents have no inferred commercial license.

All candidate records have `approved_translation: null`, `human_review: false`, and `generation_eligible: false`. A separate agent verifies the fixed source bytes and exact bilingual key alignment before adoption. This does not constitute financial-expert approval.

## Reproduction

Run `python3 scripts/collect_batch8_malaysia.py`. It retrieves only fixed-commit public raw GitHub metadata under normal TLS. Existing core/batch-7 English–Malay pairs are read locally for exact pair deduplication. Evidence extraction sorts source keys for deterministic pair selection. `manifest.json` binds raw file hashes and evidence SHA-256.
