# RUM Framework

RUM (Rule Manager) Framework is a lightweight and modular engine to define, manage, and execute **policies**, **rules**, and **actions** in a configurable and reusable way, clearly separating decision logic from execution logic.

This implementation represents the core engine of the framework and is designed to support policy-driven workflows in automation, data processing, and service-oriented contexts.

The framework is described in detail in the technical report:

> *Fares M., Carluccio I., Danecek P., et al.*
> **INGV RUM — A Lightweight Rule Manager Framework**, Rapporti Tecnici INGV, 508 (2025).
> DOI: 10.13127/rpt/508

---

## Motivation

In many complex systems, operational logic is often:

* hard-coded into application code,
* duplicated across multiple components,
* tightly coupled to specific workflows.

This approach makes systems hard to evolve and limits reusability.

RUM addresses this problem by introducing a configuration-driven model that:

* separates **decision logic** from **execution logic**,
* allows behavior changes without code modifications,
* promotes component reuse.

---

## Core Concepts

RUM is based on three core concepts:

* **Policy** – defines context and overall intent.
* **Rule** – expresses conditional logic.
* **Action** – represents reusable execution units.

These elements are orchestrated by the **sequencer**, which ensures a deterministic execution flow.

---

## Policy

A **policy** is a logical container of related rules designed to represent a specific operational or functional goal.

Policies:

* group logically related rules,
* define the execution scope,
* do not execute actions directly.

Their role is to provide a higher semantic layer that guides the sequencer in executing the rules.

---

## Rule

A **rule** encapsulates a logical condition that is evaluated against input, context, or system state.

Rules:

* are evaluated sequentially by the sequencer,
* determine whether and which actions should be executed,
* can **override action configuration**.

The rule is the key connection point between the intent expressed by a policy and the concrete execution of actions.

---

## Action

An **action** is a reusable execution unit that performs a specific task, such as:

* invoking a service,
* transforming data,
* sending notifications,
* executing commands or workflow steps.

Actions are designed to be:

* generic,
* context-independent,
* configurable through parameters.

### Configuration Override

A key principle of RUM is that **action configuration can be overridden at the rule level**.

In practice:

* the action defines default parameters,
* the rule can redefine or extend these parameters,
* the same action can be reused in multiple rules and policies with different behaviors.

This mechanism prevents duplication and enables high reuse.

---

## Execution Model and Sequencer

The **sequencer** is responsible for executing policies.

Execution flow:

1. Select the policy to run
2. Iterate over the rules defined in the policy
3. Evaluate each rule against the current input
4. If the rule matches:

   * resolve the associated actions
   * apply configuration overrides
5. Execute the actions in a deterministic order

This model ensures:

* predictability,
* transparency of decision logic,
* fine-grained control over execution.

---

## Repository Structure

The repository structure reflects the core concepts of the framework:

```
├── actions/         # reusable action definitions
├── config/          # global framework configurations
├── modules/         # extendable modules and core components
├── policies/        # policy definitions
├── rules/           # rule definitions
├── utils/           # helper functions
└── README.md
```

---

## Conceptual Example

### Action (default configuration)

```yaml
name: notify_action
parameters:
  retries: 3
  timeout: 30
```

### Rule (override configuration)

```yaml
name: high_priority_rule
condition: input.priority == "high"
actions:
  - name: notify_action
    override:
      timeout: 5
```

### Policy

```yaml
name: notification_policy
rules:
  - high_priority_rule
```

During execution, the sequencer applies the rule's override to the action configuration before executing it.

---

## Project Context

RUM Framework is **only the core engine**. It requires a concrete **project** to provide rules, policies, actions. 
Without a project context, the engine does not produce any output.

For example, the **Curation project** ([RUM Project](https://github.com/INGV/rum-project) ) provides:

* the set of policies and rules to apply
* configuration of actions


This separation allows RUM to remain flexible, reusable, and independent from specific use cases.

---

## Design Principles

RUM is built on the following principles:

* **Separation of concerns**: policies, rules, and actions have distinct responsibilities.
* **Configuration-driven behavior**: system behavior is defined via configuration.
* **Reusability**: actions are reusable and customizable.
* **Extensibility**: new rules and actions can be added without modifying the core engine.

---

---

## References

* *INGV RUM — A Lightweight Rule Manager Framework*, Rapporti Tecnici INGV 508 (2025), DOI: [10.13127/rpt/508](https:doi.org/10.13127/rpt/508)
* [RUM Project](https://github.com/INGV/rum-project) - Project Curation implementation
