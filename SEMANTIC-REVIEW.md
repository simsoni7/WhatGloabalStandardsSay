# Source-definition review

The 390 integration issue groups now have a triage classification and a review packet containing exact source observations, definitions, source group/context, jurisdiction and generation eligibility. This is preparation for semantic validation, not a claim that all 390 groups are linguistically reviewed.

11 source-definition decisions cover 18 records. They are AI-assisted and checksum-bound to the observed terms and definitions. Changed evidence invalidates the decision and requires re-review. Original source concepts are retained; relationships remain candidates with merge_authorized=false. approved_translation remains null.

| Case | Decision |
|---|---|
| Mongolbank304 Interest Rate / Хүү | Definition mismatch suspected; quarantined from generation |
| 733 Interest / Хүү | Definition supports interest sense as a candidate, not approval |
| 737/3377 interest-rate forms | Percentage-rate definitions support same-sense variant candidate |
| 3104 Warrant premium | Definition describes combining firms in supply-chain roles; quarantined |
| 2591 Warrant premium | Definition supports market-versus-theoretical value sense as a candidate |
| 2555/3087 Treasury stock | Definitions concern repurchased company shares; target wording needs specialist review |
| 18/1101 Customer | Payment-service versus insurance context split candidate |
| 1044/3153 Capital | Financial resources versus physical production capital split candidate |
| 270/1480 Collateral | Pledged-asset variant candidate; legal/product scope retained |
| 75/3208 Debt for nature swap | Identical source-definition variant candidate |
| Canadian Agreement Type | Contracts versus grants field context retained |

API evidence still shows quarantined source observations for audit. generation_eligible=false prevents these rows from being passed to the model. When every matching source is quarantined, model_status=blocked_source_review and the model is not called. Other model proposals remain unapproved and subject to context review.

Automated triage classes include cross-domain meaning review, identical-definition variant candidates, unresolved target variants and shared-target sense review. These are candidate classifications; synonyms, polysemy, different product contexts and genuine source errors require different follow-up. No automatic corrections, expert approvals or broad semantic-equivalence claims are produced.

Commercial permission is separate. The commercial export includes only previously commercially permitted sources, with these same semantic review fields. Mongolia/Nepal legacy sources remain excluded from commercial export. FinQA remains an independent numerical-reasoning asset, not translation gold.
