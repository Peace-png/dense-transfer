# Example: Architecture Decision

**Topic:** "Should I use Postgres or SQLite for a single-user desktop app that stores ~100k records?"

| Section | Tokens (cl100k_base) | Status |
|---|---|---|
| Bloated baseline | varies by model | illustrative excerpt below — not a measured response |
| Dense version (below) | **480** | measured |

---

## Bloated version (illustrative excerpt of the kind of prose this protocol replaces)

> When choosing between Postgres and SQLite for your application, there are a number of factors you should carefully consider. Both databases have their own strengths and weaknesses, and the right choice depends on your specific use case. Postgres is a powerful, enterprise-grade relational database management system that has been in development for over 30 years. It offers a rich feature set including support for complex queries, ACID transactions, foreign keys, triggers, views, stored procedures, and much more...

A typical version in this register continues with feature lists for both databases and never reaches a recommendation, leaving the user to do the comparison work themselves.

---

## Dense version (full)

### CODE (the decision)

```
Use SQLite.
```

### WHY

- **Single-user desktop app**: SQLite is in-process. Zero network, zero auth, zero server lifecycle. Postgres needs a daemon, a port, a config file, and a backup story your user has to think about. For one user that's pure cost.
- **100k records is nothing for SQLite**: well-designed SQLite handles tens of millions of rows. 100k is two orders of magnitude under the comfortable ceiling.
- **Single-file storage**: the entire database is one file. Backup = copy the file. Sync = sync the file. Send to support = email the file. Postgres makes all three of these procedures.
- **Bundled with Python, every browser, every mobile OS**: zero install for your user. Postgres = "ask the user to install Postgres" or "ship Postgres in your installer." Both are bad.
- **Write concurrency is a non-issue at single-user**: SQLite's one-writer-at-a-time limit is the most-cited reason to avoid it. It does not apply to single-user apps. A cited limit that doesn't apply is not a valid reason.

### FAILURE MODES (and when to revisit)

- **Multiple concurrent writers**: if the app ever grows to multi-user with simultaneous writes (sync server, shared workspace), SQLite's writer lock becomes a bottleneck. Migrate to Postgres at that point, not before. Migration cost is real but bounded — schemas are mostly portable.
- **Network access from another machine**: SQLite over a network filesystem is broken. If you ever need that, you need a server database. Don't use NFS+SQLite as a workaround.
- **Heavy concurrent analytics workloads**: parallel reads with joins on millions of rows — Postgres's query planner is better. Not your situation.
- **Full-text search at scale**: SQLite has FTS5 and it's good up to ~1M docs. Past that you want a real search engine (Tantivy, Meilisearch), not Postgres.

### KEY

Postgres is a server. SQLite is a file. You have one user and 100k records. You don't need a server. The day you need a server, you'll know — and the migration is bounded work, not a one-way door.

---

## What got cut from the bloated style and why

- **The full Postgres feature list**: irrelevant when the answer is "you don't need a server."
- **The "both have their strengths" both-sides framing**: hedging that makes the reader do the decision work. The user asked which one to use — answer the question.
- **Generic "it depends on your use case"**: the use case was given in the question. Apply it. Don't restate it.
- **Tutorial on ACID, transactions, and SQL**: the user is choosing between two SQL databases.

What was kept: the recommendation, the *why* (each bullet ties a feature of SQLite to a property of the user's situation), and the explicit conditions under which to revisit. That last part is the difference between a decision and an opinion.
