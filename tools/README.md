# RUM Operational Utilities

The `tools` directory contains **operational utilities** that support the deployment, administration, and maintenance of the RUM Framework.

These tools are **not part of the framework core**. Instead, they assist administrators in managing RUM installations and orchestrating operational workflows around the framework.

Typical responsibilities include:

- configuring execution environments;
- managing RUM worker instances;
- distributing input data for processing;
- supporting administrative and maintenance tasks.

Each tool is self-contained and provides its own documentation.

## Available Tools

---

### rum-admin

Administrative utility used to orchestrate RUM cluster operations.

Typical tasks include:

- configuring the execution Context;
- managing worker containers;
- executing administrative workflows (e.g. insert, update).

 See the documentation in: [rum-admin-read-me](readme/rum-admin-read-me.md)

---

### sds_distributor

Utility for scanning SDS archives and distributing data files across RUM workers for parallel processing.

See the documentation in: [distributor-read-me](sds_distributor/distributor-read-me.md)

---

---

### policy-explain

Is a command-line utility that analyzes a RUM Policy and reconstructs its effective execution workflow.

See the documentation in: [policy-explain-read-me](readme/policy-explain-read-me.md)

---