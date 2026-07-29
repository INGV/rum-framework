# Policy Explain

`Policy Explain` is a command-line utility that analyzes a RUM Policy and reconstructs its effective execution workflow.

Instead of manually opening multiple Policy, Rule, and Action configuration files, the tool follows the entire execution chain and produces a human-readable description of the workflow, including the effective configuration applied to every Action.

The utility is intended as both a documentation aid and a debugging tool for developers and system administrators.

---

## What it does

Starting from a Policy, the tool automatically:

- loads the Policy definition;
- follows the referenced Rules in execution order;
- resolves the Actions executed by each Rule;
- loads the default configuration of every Action;
- applies Rule-specific configuration overrides;
- displays the effective configuration that will actually be used during execution.

The tool never modifies the project.

It is a read-only inspection utility.

---

## Repository Layout

`Policy Explain` expects the standard RUM project structure:

```text
project/
├── policies/
├── rules/
├── config/
└── actions/
```

The utility automatically locates the corresponding Rule and Action configuration files.

---

## Usage

```bash
python3 policy-explain.py <policy-name>
```

Example:

```bash
python3 policy-explain.py checkin-only
```

or equivalently

```bash
python3 policy-explain.py policy-checkin-only.yaml
```

---

## Example Output

```text
------------------------------------------------------------------------
Policy : checkin-only
------------------------------------------------------------------------

Rules

    Rule : filechecks

        Action : PRE-FLY_CHECKS
            module : preflychecks

            - ARCHIVE_TRUST = /var/lib/archive/trust/
            - CHK_ARCHIVE = False
            * CHK_AUTH = True [OVERRIDE]
            * MONGO.DB_HOST = mongodb:27017 [OVERRIDE]

        Action : SANITY_CHECKS
            module : sanitychecks

            ...
```

Parameters marked with **`[OVERRIDE]`** indicate values supplied by the Rule that replace the default configuration defined by the Action.

---

## Why this tool exists

As projects evolve, understanding the effective behavior of a Policy often requires opening multiple files:

```
Policy
    ↓
Rule
    ↓
Action
    ↓
Configuration
```

`Policy Explain` reconstructs this chain automatically, allowing developers to understand the execution workflow without manually navigating the repository.

This is particularly useful for:

- onboarding new developers;
- debugging policy execution;
- validating Rule configuration overrides;
- documenting project behavior;
- reviewing existing workflows.

---

## Philosophy

`Policy Explain` follows the same design philosophy as the RUM Framework.

It does not extend the framework or modify its behavior.

Instead, it improves the readability of projects by exposing the effective execution model in a simple and human-readable form.

Keeping inspection tools outside the framework itself is consistent with the **Bicycle Approach**: improve understanding without increasing framework complexity.

---

## Future Extensions

Possible future enhancements include:

- Markdown documentation generation
- Mermaid workflow diagrams
- JSON export
- Policy validation (lint)
- Detection of unused configuration parameters
- Detection of orphan Rules or Actions
- Project documentation generation