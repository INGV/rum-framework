# RUM Administration Tool

`rum-admin` is the operational administration utility for the RUM Framework.

It is responsible for preparing the execution environment, managing RUM worker instances, and orchestrating administrative workflows such as offline data insertion and updates.

Unlike the RUM Framework itself, which processes individual files, `rum-admin` operates at the **cluster level**, coordinating multiple workers and supporting operational tasks.

---

# Responsibilities

The tool performs three main functions:

- configure the execution Context;
- manage RUM worker containers;
- execute administrative operations.

The framework remains responsible for processing data, while `rum-admin` orchestrates how and when those processes are executed.

---

# Command Line

```bash
python3 rum-admin.py [OPTIONS]
```

---

## Options

| Option | Description | Default        |
|---------|-------------|----------------|
| `--cmd` | Docker or Docker Compose command to execute on all workers | none           |
| `--workers` | Number of worker instances | `2`            |
| `--prefix` | Prefix used to build worker container names | `rum-curation` |
| `--context` | Execution Context name (without `context-` prefix and `.yaml` suffix) | `default`      |
| `--operation` | Administrative operation to execute | none           |

---

# Worker Naming

Workers are identified using a configurable prefix followed by a progressive number.

Example:

```
rum-curation-1
rum-curation-2
rum-curation-3
...
```

Changing the prefix allows the same administration tool to manage different RUM clusters.

---

# Context Files

Execution Contexts are stored in the project's `contexts/` directory.

The `--context` parameter expects only the logical context name.

Example:

```bash
--context issue-2456
```

loads

```
contexts/context-issue-2456.yaml
```

During workflow operations, the selected execution Context is copied to:

```
contexts/context.yaml
```
which becomes the active Context used by the RUM workers.

Cluster management commands (`--cmd`) do not modify the active Context.

---

# Cluster Commands

The `--cmd` option executes the same Docker command on every configured worker.

Supported commands are:

```
docker start
docker restart
docker stop
docker rm
compose up
compose down
```

Example:

```bash
python3 rum-admin.py \
    --cmd "docker restart" \
    --workers 25
```

All worker containers are restarted sequentially.

---

# Administrative Operations

Administrative operations represent higher-level workflows built on top of the framework.

Unlike `--cmd`, which simply manages worker containers, an operation may coordinate multiple tools and perform complete processing workflows.

Current operations include:

| Operation | Description |
|-----------|-------------|
| `insert` | Insert new offline data into the archive. |
| `update` | Update existing archived data and create new versions when required. |

Operations requiring data processing must be executed together with an explicit Context.

Example:

```bash
python3 rum-admin.py \
    --operation update \
    --context issue-2456
```

A workflow operation automatically:

1. load the specified Context;
2. activate it for all workers;
3. restart the worker containers;
4. launch the SDS Distributor using the parameters defined in the Context.

---

# Relationship with SDS Distributor

`rum-admin` does not process SDS archives directly.

Instead, it orchestrates the execution of the SDS Distributor.

The execution Context provides the information describing what should be processed (for example, the SDS archive location), 
while the Distributor configuration defines how the workload is distributed across workers.
This separation keeps both tools independent and focused on a single responsibility.

---

# Workflow

A typical workflow operation executes the following steps:

1. Load the selected execution Context.
2. Load the Distributor configuration associated with the operation.
3. Activate the Context for all workers.
4. Restart the worker containers.
5. Launch the SDS Distributor.

This orchestration allows administrative workflows to be executed without modifying the RUM Framework itself.

---

# Design Philosophy

`rum-admin` follows the same design principles as the RUM Framework and the Bicycle Approach.

It is intentionally designed as an orchestration tool rather than a processing engine.

Business logic remains inside RUM Policies, Rules, Actions, Contexts, and project configuration, while `rum-admin `simply coordinates operational activities.

---

# Future Extensions

The tool is intentionally designed to accommodate additional administrative operations.

Future operations may include:

- recovery
- migration
- verification
- maintenance
- reporting

without requiring modifications to the RUM Framework processing engine.