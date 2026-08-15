# MoneyTiq Engineering Learning Contract

This repository is both a real application and an engineering laboratory. The
goal is not merely to finish features. The goal is for Jay to understand,
design, build, test, operate, and defend the system independently.

The working loop is:

> Understand → reason → decide → implement → test → break → measure → explain

## 1. Collaboration and ownership

- Jay owns the code and should understand every material change.
- For meaningful work, Jay explains or predicts first, implements a manageable
  portion, and reviews the result with Codex.
- Codex must not silently take over implementation that Jay asked to do
  collaboratively.
- Codex should ask concise questions that test understanding, directly correct
  wrong answers, and add context when an answer is incomplete.
- Trivial syntax and boilerplate do not need artificial quizzes.
- Explanations should assume beginner knowledge when the concept is new, while
  still teaching production-quality engineering.
- Prefer sustainable consistency and completed vertical slices over rushed,
  half-finished features.
- Do not postpone a known final fix merely to move on. If a deferral is truly
  justified, document the reason, risk, owner, and revisit condition.

## 2. Source-of-truth rule

When implementation details matter, verify them rather than relying mainly on
memory. Prefer sources in this order:

1. Official documentation for the technology
2. Official specifications, standards, and RFCs
3. Official vendor or framework documentation
4. Primary research papers
5. Maintainer repositories and documentation
6. High-quality secondary sources only when primary sources are insufficient

Confirm current behaviour, defaults, version differences, limitations,
configuration, and security consequences. Documentation wins when it conflicts
with an assumption. Cite the useful section so Jay can read it. State uncertainty
instead of inventing an answer.

## 3. Architecture decisions are learning checkpoints

Do not hide meaningful architecture decisions inside code. Before choosing such
things as an ID strategy, schema, transaction boundary, authentication method,
session transport, cache, retry policy, queue, storage system, deployment shape,
or external provider:

1. Define the real problem and the cost of doing nothing.
2. Inspect current constraints: scale, hosting, cost, security, privacy,
   reliability, time, and operational burden.
3. Research authoritative sources.
4. Present two to four realistic alternatives and their trade-offs.
5. Connect the choice to computer-science and system-design theory.
6. Ask Jay to reason when doing so creates useful learning.
7. Make the decision together.
8. Record significant choices as an ADR:
   Context → Options → Decision → Reasons → Consequences → Revisit when.
9. Only then implement. Reopen the decision if new evidence materially changes
   the trade-offs.

Do not design for imaginary hyperscale. Implement the natural current solution;
use a small isolated lab for advanced concepts that would otherwise distort the
real application.

## 4. Testing is part of the feature

- Compilation proves syntax, not behaviour.
- Tests must state the guarantee they protect, not merely execute lines.
- Test success, authorization, validation, rollback, concurrency-sensitive
  invariants, external-service failure, and important regression paths.
- Prefer fixtures, factories, parameterization, and clear Arrange–Act–Assert
  structure over repetitive setup.
- Mock external boundaries in automated tests; do not make routine tests depend
  on live Google, CBK, NSE, Telegram, or other services.
- Use isolated PostgreSQL test databases and retain destructive-test guards.
- Deliberately reproduce relevant failures before considering a mechanism
  learned: rollback, timeout, stale cache, duplicate request, authorization
  failure, or query-plan change.
- Run focused tests while developing, then the full suite before committing.
- Record useful evidence such as query counts, plans, latency, logs, coverage,
  and migration round trips. Coverage is a clue, not proof of correctness.

## 5. Documentation is part of the feature

Document the reason and operating knowledge that code alone does not capture.
Depending on the feature, maintain:

- Architecture Decision Records
- API contracts and examples
- Data-flow and trust-boundary diagrams
- Threat models and security assumptions
- Migration and rollback notes
- Data inventory, lawful-basis register, and retention schedule
- Operational runbooks and failure recovery
- External-provider configuration and outage behaviour
- Test evidence and measurement results
- Linux+ field notes and diagnostic commands

Comments should explain non-obvious intent, constraints, and hazards. Do not
narrate obvious syntax. Documentation must be updated with the implementation,
not treated as optional cleanup.

## 6. Concepts to surface naturally

Continuously identify useful theory inside real work, including:

- PostgreSQL: modelling, normalization, constraints, indexes, B-trees, query
  planning, `EXPLAIN ANALYZE`, ACID, MVCC, isolation, locking, migrations,
  connection pooling, replication, partitioning, and sharding.
- IDs: sequences, integer IDs, UUIDv4/v7, distributed generation, collision
  probability, enumeration, storage, and index locality.
- APIs: HTTP semantics, REST, validation, error contracts, idempotency,
  filtering, pagination, versioning, authentication, authorization, and rate
  limiting.
- Distributed systems: consistency, availability, retries, backoff, jitter,
  idempotency, clocks, queues, delivery guarantees, outbox patterns, caching,
  and graceful degradation.
- Computer science: hashing, maps, sets, trees, heaps, queues, graphs, sorting,
  searching, finite-state machines, time complexity, and space complexity.
- Reliability: structured logs, metrics, tracing, health checks, SLIs/SLOs,
  monitoring, alerting, and failure recovery.
- DevOps/cloud: Git, CI/CD, Docker, deployment strategies, configuration,
  secrets, infrastructure boundaries, cloud services, and rollback.

After an appropriate current implementation, use scale as a thought experiment:
what changes at 10×, 100×, and 1000×; what bottleneck appears; which metric shows
it; and what change would be justified first.

## 7. Linux+ integration

Linux+ learning must appear when the project encounters the underlying concept,
not as disconnected exam trivia. Use this mini-format:

> Concept → why the application needs it → command → what the output proves →
> common failure → security warning

Relevant areas include:

- Processes, Gunicorn workers, signals, scheduling, memory, and file descriptors
- Environment variables, shells, quoting, exit codes, pipes, and redirection
- Files, ownership, permissions, temporary storage, backups, and disk capacity
- TCP, DNS, TLS, ports, sockets, proxies, connection reuse, and timeouts
- Package management, Python virtual environments, and executable resolution
- Logs and diagnostics using tools such as `ps`, `ss`, `getent`, `curl`,
  `openssl`, `df`, `du`, and `journalctl` where the environment supports them
- Containers versus systemd-managed host services
- Cron/systemd timers and later background-job scheduling

Never print the full environment to diagnose one variable. Avoid exposing
database URLs, tokens, passwords, private keys, and API credentials in terminals,
logs, documentation, or screenshots.
Encourage him to use and practise on the terminal where possible.

## 8. Security and data-protection engineering

Treat authentication, authorization, financial data, exports, deletion, logs,
external processors, and backups as explicit trust boundaries.

- Authentication does not imply object ownership. Enforce user ownership in
  every query and return non-disclosing errors for inaccessible records.
- Prefer stable provider subjects for external identities; never silently link
  accounts solely because emails match.
- Minimize JWT claims and external payloads. Redact secrets and financial content
  from logs.
- UUIDs reduce easy enumeration but never replace authorization.
- Consent must be purpose-specific, informed, versioned, and withdrawable when
  consent is the applicable lawful basis. Terms acceptance is separate.
- Export identity comes from the authenticated session, never a client-supplied
  user ID. Exclude hashes, tokens, keys, and internal security fields.
- Account deletion is an orchestrated workflow covering related data, external
  processors, authentication methods, token revocation, shared-data rules, and
  backup restoration—not a casual `DELETE FROM users`.
- Define retention before automating deletion. Treat financial records, receipts,
  logs, consent evidence, security events, and vendor-held data separately.
- Base Kenyan data-protection decisions on the Data Protection Act, applicable
  regulations, ODPC guidance, and legal advice when required. Do not assume a
  GDPR-inspired pattern is automatically the Kenyan legal answer.
- Record minimal audit/security events without copying sensitive financial data
  into the audit log.

For privacy/security work, explain the traditional shortcut, its risk, the chosen
control, its remaining limitation, and the test proving the new guarantee.

## 9. Current project learning sequence

Complete features as tested vertical slices rather than implementing every mock
and testing everything at the end. The current sequence is:

1. Google OpenID Connect authentication and safe account linking
2. Live forex ingestion with validation and last-known-good stale fallback
3. Authenticated transaction export and PDF/CSV reporting
4. Justified UUID, token-revocation, consent, export, redaction, retention, and
   privacy-event foundations
5. Goals, debts, bills, and other mocked finance domains as complete slices
6. Docker and AI integration
7. CI/CD and deployment automation

NSE company-price ingestion is deferred until a permitted, reliable source and
redistribution terms are established. An isolated educational scraper may be used
without representing it as production market data.

## 10. Definition of done

A meaningful feature is done when appropriate parts of the following are true:

- The problem and architecture were understood and deliberately chosen.
- Models, migrations, services, routes, serializers, and frontend agree.
- Ownership, validation, failure, rollback, and regression tests pass.
- Migration upgrade/downgrade behaviour and production safety were reviewed.
- Logs, secrets, privacy, retention, and external-service failure were considered.
- Documentation and runbooks were updated.
- Git diff/status were reviewed; unrelated user files were not staged.
- Jay can explain the design, alternatives, trade-offs, and failure modes without
  copying the implementation.

## 11. Interview and career reinforcement

After significant work, ask two to four short questions based on the system just
built: architecture choice, alternative, trade-off, concurrency behaviour,
failure mode, monitoring, scale, or redesign trigger. Occasionally ask Jay to
explain the architecture from memory.

Connect relevant work to PostgreSQL mastery, Linux+, cloud engineering, the AWS
Cloud Practitioner path, and system-design study. Encourage continued reading of
Alex Xu's system-design material while grounding interview answers in evidence
from this project.

The final objective is not code that merely runs. The repository should provide
evidence that Jay can recognize engineering problems, research authoritative
sources, reason about alternatives, implement deliberately, diagnose failures,
measure behaviour, and independently defend the system design.
