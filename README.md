# RUM Framework

RUM (Rule Manager) Framework is a lightweight and modular framework designed to define, manage, and execute **policies**, **rules**, and **actions** in a clear and reusable way. It has been developed to support flexible decision-making and automated processing pipelines, with a strong focus on configurability, reuse, and separation of concerns.

The framework is described in detail in the following technical report:

> *Fares M. et al.*, **INGV RUM — A Lightweight Rule Manager Framework**, Rapporti Tecnici INGV, 508, 2025. DOI: 10.13127/rpt/508

---

## Motivation

In many data-processing and service-oriented systems, operational logic is often hard-coded, duplicated across components, or tightly coupled to specific workflows. This makes systems difficult to adapt, maintain, and extend.

RUM addresses this problem by:

* separating *decision logic* from *execution logic*,
* enabling reuse of processing units across different scenarios,
* allowing behavior changes through configuration rather than code changes.

---

## Core Concepts

RUM is built around three core concepts:

* **Policies** – high-level containers that define *when* and *why* certain logic should be applied.
* **Rules** – conditional logic units that evaluate inputs and decide *what* should happen.
* **Actions** – executable units that define *how* something is done.

These concepts are intentionally decoupled but explicitly connected through the RUM execution model.

---

## Policies

A **policy** represents a coherent set of rules designed to address a specific operational or business objective.

Policies:

* group logically related rules,
* define the execution scope,
* provide a semantic layer above individual rules.

A policy does not directly execute actions; instead, it orchestrates the evaluation of its rules through the RUM sequencer.

---

## Rules

A **rule** encapsulates conditional logic. It evaluates inputs, context, or system state and determines whether one or more actions should be triggered.

Rules:

* are evaluated sequentially by the RUM sequencer,
* reference one or more actions,
* can override action configurations at runtime.

Rules are the key mechanism that connects abstract policies to concrete execution behavior.

---

## Actions

An **action** represents a reusable execution unit. It performs a specific task, such as:

* triggering a service,
* transforming data,
* sending a notification,
* executing a command or workflow step.

Actions are designed to be:

* generic,
* stateless or minimally stateful,
* reusable across multiple rules and policies.

### Action Configuration and Override Mechanism

A central design principle of RUM is that **action configurations can be overridden by rules**.

This means that:

* actions define *default* configuration parameters,
* rules may redefine or extend these parameters when invoking an action,
* the same action can be reused in different rules or policies with different behaviors.

This override mechanism enables high reuse while avoiding duplication of action definitions.

---

## Execution Model and Sequencer

At runtime, RUM processes logic through a dedicated **sequencer**, which enforces a clear and deterministic execution flow:

1. A policy is selected for execution.
2. The sequencer iterates over the rules associated with the policy.
3. Each rule is evaluated against the current input and context.
4. When a rule matches, the referenced actions are prepared.
5. Action configurations are resolved, applying rule-level overrides.
6. Actions are executed in the defined order.

This model ensures:

* predictable behavior,
* transparent decision-making,
* fine-grained control over execution.

---

## Reusability and Design Principles

RUM is designed around the following principles:

* **Separation of concerns**: policies decide *intent*, rules decide *conditions*, actions handle *execution*.
* **Configuration-driven behavior**: changes in logic do not require code changes.
* **Reusability**: actions are shared and specialized through rule-level configuration.
* **Extensibility**: new rules and actions can be added without impacting existing ones.

---

## Project Status

🚧 Research and engineering framework. APIs and configuration models may evolve.

---

## Related Resources

* Technical report: *INGV RUM — A Lightweight Rule Manager Framework* (Rapporti Tecnici INGV 508)
* Organization: [https://github.com/INGV](https://github.com/INGV)
