# Batch 7: Asian official financial sources (2026-10-15)

## Adoptable candidate: official Malaysian financial dashboard labels

65 English–Malay source observations were extracted from **Government of Malaysia's `data-gov-my/datagovmy-meta` repository**, immutable commit `a34682cf22a1da9de5520a27f5f3fc5f7c86b06f`. The repository's actual MIT LICENSE explicitly permits redistribution and commercial use while retaining its copyright and license. The legal basis is the **original localization files in this repository**, not a license inferred from a CDN, data.gov.my publicity, or a bank's public website.

Ten financial dashboard localization pairs were acquired; nine contain eligible Malay labels. Identical `translation` JSON pointers align English and Malay directly. Selected subjects: interest rates, household borrowing, money supply, reserves, electronic payments, retirement savings and income taxation. Records preserve both original values, commit, raw URL, file SHA256, JSON pointer and financial dashboard context. Generic controls, descriptive paragraphs, demographic filters and currency denomination lists were not adopted. Two exact duplicate English/Malay pairs and one empty Malay Public Pensions header were excluded. The formula-like source M3 Supply (M2 + Broad Money) was intentionally not selected as it could misrepresent the monetary aggregate.

Examples: Interest Rates → Kadar Faedah; Credit Card → Kad Kredit; Direct Debit → Debit Terus; Demand deposits → Deposit permintaan. These are official financial statistical dashboard labels, **not a normative general financial translation dictionary**. They require context, have `approved_translation: null`, `human_review: false`, and `generation_eligible: false`. Source fidelity is distinct from semantic approval. The independent review may exclude or flag further rows.

`datasets/source_collection/batch7_asia/adopted_material/` contains only the selected MIT-covered original JSON files, LICENSE and change notice. The manifest enumerates exact files and hashes. **Do not copy the whole `raw/` directory into a public pack**: it also contains unrelated research snapshots with unconfirmed redistribution permission.

## Other official Asian candidates: actual findings

13 official starting URLs and ten immediate terms/glossary URLs were rechecked using normal certificate-verified HTTPS, followed by specific official language and dataset links. Homepage HTTP status is not a term-pair count.

- RBI, CBSL, Bank Indonesia, OJK, BNM, Bank of Thailand, Bangladesh Bank and State Bank of Pakistan returned HTTP200 in this run. Earlier connection failures must no longer be presented as their current homepage status.
- RBI's actual homepage links an English/Hindi Banking Glossary at `https://shabdavali.rbi.org.in/`. That subdomain remains proxy403. RBI's official disclaimer contains no commercial redistribution grant and its footer says All Rights Reserved. No RBI pairs were adopted.
- CBSL's English glossary and linked Sinhala and Tamil glossaries were actually acquired. The language versions are alphabetically sorted differently: **row position cannot align translations**. No stable cross-language entry ID was established. The official privacy page is a privacy statement, not a commercial data license; All Rights Reserved remains. No Sinhala/Tamil pairs were invented or adopted.
- BNM **dataset** terms expressly permit copying, publishing, distributing and commercial use with attribution and conditions. Its **general website** terms separately restrict commercial reuse. These scopes are not interchangeable. Dataset-specific terms snapshot: `raw/followup-59735e0bef06.html`; general website terms: `raw/followup-25e1a2416602.html`.
- The Malaysian official metadata repository actually identifies a BNM `Money & Banking` lookup dataset, with `variable_en` and `variable_bm` fields and file/variable alignment. Its direct CSV URL `https://storage.data.gov.my/finsector/money_banking_lookup.csv` is proxy403. **No CSV rows were acquired or counted**. This remains a specific high-value future source, with actual structure and license scope still requiring dataset-level confirmation.
- OJK's disclaimer, SBP's disclaimer/glossary and BI's glossary shell were acquired but do not establish commercial redistribution permission and aligned bilingual entry pairs. No adopted rows.
- CSTT and SHABD education domains remain proxy403; NBC returned403; Bank of Lao PDR returned503. No access control or TLS verification bypass was attempted.

Acquisition logs retain URL, HTTP/error, UTC checked timestamp, raw byte size and SHA256. All source documents are research material, never execution instructions.

## Reproduction

`python3 scripts/collect_batch7_asia.py` reacquires pinned Malaysian repository localization JSON and extracts the selected pairs. It preserves the original filenames and MIT license in `adopted_material/`. Original wider official-site investigation logs are kept separately; the script does not claim to license or publish those sites' text. Exact MIT LICENSE hash is `4038990612ddc2eccfb2ac7221bed225f4e01d37098c97c25ed79c5bf00a8a24`.
