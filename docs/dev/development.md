# Development conventions

Project collaboration and source publishing happen through the Radicle repository. Work is tracked with GitHub issues while that forge remains the team tracker; each issue should link its branch, relevant checks, and accepted change.

An independently closable change normally has its own Git branch. Use linked Git worktrees when independent changes proceed concurrently. Keep the primary checkout on its integration branch.

The shared development handbook is Devesis at `rad:z3Mb5cZhBVo8dDmcigD8QumiycCtX`. It defines general engineering practice. This document records only op2u-specific conventions; Git, Radicle, GitHub CLI, and other tool documentation remain authoritative for their mechanics.

Before changing discovery behavior, identify whether the change is:

- a product requirement change, which belongs in the MVP specification;
- a durable architectural or policy choice, which may require an ADR;
- an experimental hypothesis, which requires a recorded method and evaluation; or
- an implementation change that realizes an existing decision.

Do not use prompts as the only source of product requirements. Prompts implement the specification and may add a clearly labelled experimental mutation.
