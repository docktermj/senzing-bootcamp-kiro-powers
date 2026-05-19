---
inclusion: manual
---

# Conversation Protocol — Violation Examples

Reference examples for correct vs incorrect question patterns. Load when the `write-policy-gate` hook rejects a question or when reviewing conversation quality.

## Multi-Question (WRONG)

> 👉 What language do you want? Also, which track interests you?

## Multi-Question (CORRECT)

> 👉 What language do you want?
> 🛑 STOP
> [wait for response, then in next turn:]
> 👉 Which track interests you?

## Not-Waiting (WRONG)

> 👉 Are you ready to continue?
> Great, let's move on to the next step.

## Not-Waiting (CORRECT)

> 👉 Are you ready to continue?
> 🛑 STOP

## Dead-End (WRONG)

> Got it.

## Dead-End (CORRECT)

> Got it. Next I'll set up your project structure.

## Missing-Prefix (WRONG)

> What language would you like to use?

## Missing-Prefix (CORRECT)

> 👉 What language would you like to use?

## Self-Answering (WRONG)

> 👉 Who will be working on this project?
> I'll assume it's just you for now.

## Self-Answering (CORRECT)

> 👉 Who will be working on this project?
> 🛑 STOP

## Compound Confirmation (WRONG)

> 👉 Does that summary sound right? Anything I missed or got wrong?

## Compound Confirmation (CORRECT)

> 👉 Does that summary capture your situation accurately?

## Compound Either/Or (WRONG)

> 👉 Would you like me to create a one-page executive summary, or would you prefer to skip that and move on to Module 2?

## Compound Either/Or (CORRECT)

> 👉 What would you like to do next?
>
> 1. Create a one-page executive summary
> 2. Move on to Module 2

## Compound Choice (WRONG)

> 👉 Would you like to proceed with Python or Java or TypeScript?

## Compound Choice (CORRECT)

> 👉 Which language would you like to use?
>
> 1. Python
> 2. Java
> 3. TypeScript

## Sub-Step Completion Dead-End (WRONG)

> Got it — you're looking for a clean master list. ✅ Checkpoint written.

## Sub-Step Completion (CORRECT)

> Got it — you're looking for a clean master list. ✅ Checkpoint written.
>
> 👉 Will the entity resolution results need to interface with other
> software — for example, a CRM, search engine, data warehouse, or
> downstream application?
