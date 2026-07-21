# DEVELOPMENT_WORKFLOW.md

# Development Workflow

This document defines how this project is developed.

---

# Core Principle

Always keep the project in a runnable state.

Never implement multiple modules at once.

Every change must be small, testable, and reversible.

---

# Standard Development Cycle

1.

Discuss

↓

2.

Agree on architecture

↓

3.

Implement

↓

4.

Compile

↓

5.

Run

↓

6.

Verify

↓

7.

Commit

↓

Repeat

---

# Rules

## Rule 1

Never change architecture without discussion.

---

## Rule 2

Never generate a large amount of code at once.

Implement one file at a time.

---

## Rule 3

Implement only one feature at a time.

Example:

GOOD

Progress

↓

Test

↓

Table

↓

Test

↓

Report

↓

Test

BAD

Progress

Table

Report

Worker

Excel

...

↓

Test

---

## Rule 4

Always review existing source code before proposing changes.

Never assume code exists.

---

## Rule 5

When reviewing code:

Always explain

- Where to modify
- New code
- Why

Never rewrite an entire file.

---

## Rule 6

Business Logic and UI are completely separated.

UI never processes PDF.

Worker never accesses UI.

---

## Rule 7

process()

must remain an orchestrator.

Business logic belongs to

_process_pdf().

---

## Rule 8

Always keep Mock Mode working.

Mock Mode is used before every new module.

---

## Rule 9

Never optimize early.

Correctness first.

Performance second.

---

## Rule 10

When a design decision becomes stable,

update PROJECT_CONTEXT.md.

Do not rely on chat history.