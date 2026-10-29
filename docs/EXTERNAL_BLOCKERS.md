# External blockers — exact questions for the employer

These items cannot be resolved by engineering alone. Each lists the affected
requirement IDs, why engineering cannot resolve it, the exact information or
action needed, the verification that becomes possible once it is provided, and
any budget, credential or privacy constraint. Nothing on this page is inferred;
every item states a question that must be answered by a person outside this
repository. A concise, copy-paste question set, the provider/credential
authorization checklist and an **unsent** ready-to-send email draft are
consolidated in [EMPLOYER_CLARIFICATIONS.md](EMPLOYER_CLARIFICATIONS.md).

| # | Blocker | Requirement IDs | Why engineering cannot resolve it | Exact information or action needed | Verification once provided | Constraints |
| --- | --- | --- | --- | --- | --- | --- |
| B1 | Approved X data source (Actor or historical dataset) | R2, R4, R5, R9, R10, A3, O6, O13 | No Actor or dataset has been selected, reviewed or approved; choosing one and paying without sign-off is prohibited by the project rules | Select and approve one X source: provider identity, terms/licence review, Actor identity or dataset URL, input/output schema, text availability, created-at and retrieved-at timestamp semantics, engagement and follower fields, recent-180-day coverage | Profile one accepted payload with `scripts/profile_local_x_dataset.py` or one bounded ingest; re-run R2, R4, R5, R7 and R9 acceptance on real rows | Any paid Actor run first needs its spend cap (B3) and a credential route (B2) |
| B2 | Secure credential-transfer route | A2, O10 | Secrets must never appear in chat, Git or reports; the project has no authority to define the employer's private channel | Name the private channel (e.g. password manager share, encrypted email attachment) and who receives each credential | `.env` entries can then be created locally and tested against the real provider | Tokens are never committed; `TAVILY_API_KEY`/`APIFY_TOKEN` stay in the local environment only |
| B3 | Explicit spend cap for any paid collection | R2, NFR4, O13 | Paid Actor launches cost money; the code refuses to run one without an approved cap | State a hard budget ceiling and per-run item cap in USD for the selected Actor | Bounded ingest can run once, then records actual spend against the cap | No paid operation is automatically retried (NFR4, implemented) |
| B4 | The `n+0` target convention | R8, R9, O3, O4 | The brief is ambiguous; the working assumption (forecast the not-yet-completed close of day `n`, issued at 00:00 UTC) is documented but not employer-confirmed; silently redefining it would invalidate recorded metrics | Confirm or correct: is `n+0` the close of the current day forecast at its start, or the next available close after issue? | If changed, targets, folds and recorded metrics are regenerated in a new run and PHASES/traceability updated; the previous run remains in Git history as the audit trail | No deferral: the comparison verdict depends on it |
| B5 | Exact calendar submission deadline | A1, A7, O11 | The brief states both "one week" and "5–7 days" with no calendar date; no date can be inferred from files | State the due date (and timezone) and the delivery channel | The submission packet is assembled and sent with a recorded date | Email recipient on record: gilad@crowdwisdomtrading.com |
| B6 | Is live Tavily news mandatory for submission? | A4, O7, O12 | The adapter, gated `fetch-news` CLI, JSONL hand-off and offline `run --news-file` wiring are implemented and mocked-verified. A live call still requires an approved API key and employer authorisation, and the brief's news role (context vs feature) is unsettled | Answer (a) whether live Tavily ingestion is required for submission, and (b) whether news may ever be a model feature | If live news is required: authorize one bounded `fetch-news --confirm-live-call` search with the approved key (B2), record the observed provider response shape, keep news context-only unless the feature policy is formally changed, then run `--news-file` offline | No key is requested in chat; no call without authorisation |
| B7 | Submission format and packet expectations | A7 | The brief asks for an evaluation report "PDF or Markdown" and an email; whether a PDF is additionally required is unconfirmed | Confirm the accepted format(s) and any required attachments beyond repository link, credentials/Actor IDs and the evaluation report | The packet is produced in the confirmed format from existing evidence | Nothing is emailed without explicit authorization |
| B8 | ~~PR #14 head promotion permission~~ **RESOLVED 2026-10-28** | A7, delivery only | The earlier belief that this session could push only to the Arena branch was an unverified assumption; GitHub itself always reported the feature branch unprotected with zero rulesets | Nothing further needed: the non-forced fast-forward was executed from this session (`5af5bc7..d801661`) | The code change `d8016610aa7ebf82263413c48b1164e4a64d13df` is contained in the feature branch; live PR head at the 2026-10-29 query was `fa69d53f70535dec03dd7f48c1c0d212b565e336` with successful CI runs `40787633232` and `40787639350`. Current local changes are uncommitted and not covered | Still never force-push, rewrite history, merge PR #14, or push to the base branch |

## What is NOT on this list

The following were internal engineering items and are now complete or
implementation-verified in-repo, so they do not need employer input:

- NFR1 automatic code-revision provenance: implemented and tested.
- R15 persisted-input CLI integration: tested end-to-end on fixtures.
- R10 sentiment-change series: implemented and unit-verified; only its real-data
  render remains, which is governed by B1.
- R11 one-page outlook contract: machine-checked (`check_outlook_page`).
- CI pull-request triggers: fixed to cover the actual PR base branches.
- Tavily adapter and gated `fetch-news` CLI (D-005, O12, D-028): implemented,
  mocked-verified, context-only, streaming-size-bounded, and wired to the offline
  `run --news-file` step.
- Offline demo network isolation (D-028): a regression now blocks socket and HTTP
  client calls during a real offline `run` execution.

None of the above may be reclassified as "complete" in the real-data sense
until B1/B2/B3 unblock the accepted X corpus; the traceability matrix keeps
those statuses honest.
