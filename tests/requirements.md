# Requirements Document

## Introduction

ForgeAI is an AI agent orchestration system that simulates a real software company end-to-end. The system accepts a software project as input and autonomously drives it through research, architecture, development, and quality assurance using a hierarchy of specialized AI agents. The human user is responsible only for providing the initial project brief, UI/UX mockups, and final deployment. All other activities — planning, coding, testing, and review — are performed by agents under the coordination of a Lead Agent.

## Glossary

- **ForgeAI**: The overall AI agent orchestration system described in this document.
- **Lead_Agent**: The central coordinator agent responsible for pre-flight checks, task creation, agent monitoring, conflict resolution, and final project review.
- **Research_Agent**: The agent responsible for gathering external information and domain knowledge at project start.
- **Architect_Agent**: The agent responsible for producing the Master_Document in collaboration with the Research_Agent.
- **Frontend_Agent**: The agent responsible for building user interface components based on assigned tasks.
- **Backend_Agent**: The agent responsible for building APIs and business logic based on assigned tasks.
- **QA_Agent**: The agent responsible for reviewing code, running tests, and acting as the quality gate before a task is marked DONE.
- **Master_Document**: The authoritative project specification produced by the Architect_Agent and approved by the Lead_Agent. It is the single source of truth for all agents.
- **API_Contract**: A formal, agreed-upon interface definition between Frontend_Agent and Backend_Agent that must be established before coding begins.
- **Task**: A discrete unit of work assigned by the Lead_Agent to a development agent, tracked through the Task_State_Machine.
- **Task_State_Machine**: The defined lifecycle of a task: TODO → IN_PROGRESS → IN_REVIEW → TESTING → DONE.
- **Drift_Monitor**: A per-agent subsystem that periodically checks whether the agent's current work remains aligned with its assigned task.
- **Lesson**: A structured record written after a failure resolution, capturing what failed, why, how it was fixed, and a rule to avoid recurrence.
- **Agent_Memory**: The private working notes and accumulated Lessons belonging to a single agent.
- **Task_Memory**: Ephemeral context scoped to a single task, discarded when the task reaches DONE.
- **Project_Memory**: The shared, read-only context available to all agents, writable only by the Lead_Agent.
- **Confidence_Score**: A numeric value (0–100) attached to an agent's output indicating the agent's self-assessed certainty in that output.
- **Escalation_Ladder**: The five-level failure escalation protocol that governs how unresolved failures are handled.
- **Pre-flight_Checklist**: A structured set of questions the Lead_Agent asks before development begins to collect all required credentials, API keys, third-party service details, and environment constraints.
- **Loop_Counter**: A per-agent counter that tracks consecutive occurrences of the same error to prevent infinite retry loops.
- **Human_Interface**: The conversational interface through which the human user communicates exclusively with the Lead_Agent.
- **Change_Bucket**: A queue where incoming client change requests are held pending research and architecture review before entering development.
- **Development_Change_Bucket**: A queue of Lead_Agent-approved change tasks ready for assignment to development agents.
- **Change_Type**: A tag applied to every change task indicating its nature: NEW_FEATURE, REMOVE_FEATURE, MODIFY_FEATURE, or BUG_FIX.
- **Change_Priority**: A priority lane assigned to every change task: CRITICAL (conflicts with active work), NORMAL (queued after current task), or DEFERRED (picked up when agent is idle).
- **Task_Checkpoint**: A saved snapshot of an agent's in-progress work that allows the agent to pause and resume without losing progress.
- **REWORK**: A special task state applied to previously DONE tasks that must be revisited due to a client change.

---

## Requirements

### Requirement 1: Project Intake and Pre-flight Checklist

**User Story:** As a user, I want the system to identify all external dependencies before development starts, so that no agent is blocked mid-project due to missing credentials or configuration.

#### Acceptance Criteria

1. WHEN a new project is submitted to ForgeAI, THE Lead_Agent SHALL execute the Pre-flight_Checklist before any other agent begins work.
2. THE Lead_Agent SHALL identify all required API keys, credentials, third-party service endpoints, and environment constraints by analyzing the project brief.
3. WHEN the Pre-flight_Checklist identifies a missing required input, THE Lead_Agent SHALL request that specific input from the user before proceeding.
4. THE Lead_Agent SHALL not start the research and architecture phase until all items on the Pre-flight_Checklist are resolved.
5. WHEN all Pre-flight_Checklist items are resolved, THE Lead_Agent SHALL record the collected configuration in Project_Memory.

---

### Requirement 2: Research and Architecture Phase

**User Story:** As a user, I want the system to produce a thorough project specification before any code is written, so that all agents work from a consistent and complete plan.

#### Acceptance Criteria

1. WHEN the Pre-flight_Checklist is complete, THE Lead_Agent SHALL initiate a collaborative session between the Research_Agent and the Architect_Agent.
2. THE Research_Agent SHALL gather domain knowledge, technology options, and relevant external information required by the project brief.
3. WHEN the Research_Agent completes its information gathering, THE Architect_Agent SHALL produce a Master_Document that covers system architecture, component boundaries, data models, and API surface areas.
4. THE Master_Document SHALL be reviewed and approved by the Lead_Agent before it is written to Project_Memory.
5. WHEN the Lead_Agent approves the Master_Document, THE Lead_Agent SHALL write it to Project_Memory as a read-only artifact.
6. IF the Architect_Agent produces a Master_Document that contradicts information in Project_Memory, THEN THE Lead_Agent SHALL reject the document and request a revision.

---

### Requirement 3: API Contract Negotiation

**User Story:** As a user, I want the Frontend and Backend agents to agree on API interfaces before writing any code, so that integration failures are caught at design time rather than during development.

#### Acceptance Criteria

1. WHEN the Lead_Agent creates tasks that require both frontend and backend work, THE Lead_Agent SHALL initiate an API contract negotiation session between the Frontend_Agent and the Backend_Agent before either agent begins coding.
2. THE Frontend_Agent and the Backend_Agent SHALL each propose their required interface definitions and resolve any conflicts to produce a single API_Contract.
3. WHEN the Frontend_Agent and the Backend_Agent reach agreement, THE Lead_Agent SHALL write the API_Contract to Project_Memory.
4. THE Frontend_Agent SHALL not begin coding any feature that depends on a backend endpoint until the corresponding API_Contract is recorded in Project_Memory.
5. THE Backend_Agent SHALL not begin coding any endpoint until the corresponding API_Contract is recorded in Project_Memory.
6. IF the Frontend_Agent or the Backend_Agent identifies a required change to an existing API_Contract, THEN THE Lead_Agent SHALL coordinate a renegotiation session before any implementation changes are made.

---

### Requirement 4: Task Creation and Assignment

**User Story:** As a user, I want the Lead Agent to decompose the project into well-defined tasks and assign them to the right agents, so that work is organized and traceable.

#### Acceptance Criteria

1. WHEN the Master_Document is approved and all API_Contracts for the initial scope are recorded, THE Lead_Agent SHALL decompose the project into Tasks and record each Task in the Task_State_Machine with state TODO.
2. THE Lead_Agent SHALL assign each Task to exactly one agent (Frontend_Agent, Backend_Agent, or QA_Agent) based on the task's domain.
3. THE Lead_Agent SHALL ensure each Task contains a reference to the relevant section of the Master_Document and any applicable API_Contract.
4. WHEN the Lead_Agent assigns a Task to an agent, THE Lead_Agent SHALL transition the Task state from TODO to IN_PROGRESS.
5. THE Lead_Agent SHALL monitor all active Tasks and detect Tasks that have not progressed within a configurable time threshold.
6. WHEN a Task has not progressed within the configured time threshold, THE Lead_Agent SHALL initiate the Escalation_Ladder for that Task.

---

### Requirement 5: Parallel Development

**User Story:** As a user, I want the Frontend and Backend agents to work simultaneously where possible, so that the project is completed efficiently.

#### Acceptance Criteria

1. WHILE the API_Contract for a feature is recorded in Project_Memory, THE Frontend_Agent and the Backend_Agent SHALL be permitted to work on their respective Tasks for that feature concurrently.
2. THE Frontend_Agent SHALL read the API_Contract from Project_Memory to guide its implementation and SHALL NOT modify the API_Contract directly.
3. THE Backend_Agent SHALL read the API_Contract from Project_Memory to guide its implementation and SHALL NOT modify the API_Contract directly.
4. WHEN a Frontend_Agent Task and a Backend_Agent Task share a dependency, THE Lead_Agent SHALL sequence those Tasks so the dependency is resolved before the dependent Task begins.

---

### Requirement 6: Task Review and Quality Gate

**User Story:** As a user, I want every completed task to pass QA review before it is marked done, so that only verified work is accepted into the project.

#### Acceptance Criteria

1. WHEN a development agent (Frontend_Agent or Backend_Agent) completes its work on a Task, THE agent SHALL transition the Task state to IN_REVIEW.
2. WHEN a Task enters IN_REVIEW, THE QA_Agent SHALL be assigned to review the Task.
3. WHEN the QA_Agent begins reviewing a Task, THE QA_Agent SHALL transition the Task state to TESTING.
4. THE QA_Agent SHALL execute all applicable tests for the Task and evaluate the output against the acceptance criteria in the Master_Document.
5. WHEN all tests pass and the QA_Agent approves the Task, THE QA_Agent SHALL transition the Task state to DONE.
6. IF any test fails or the QA_Agent identifies a defect, THEN THE QA_Agent SHALL transition the Task state back to IN_PROGRESS and attach a structured defect report to the Task.
7. THE development agent that originally owned the Task SHALL address the defect report before transitioning the Task back to IN_REVIEW.
8. THE agent that produced the work for a Task SHALL NOT approve or transition that Task to DONE (no self-approval).

---

### Requirement 7: Task State Machine Integrity

**User Story:** As a user, I want the task lifecycle to be strictly enforced, so that no work is skipped or bypassed.

#### Acceptance Criteria

1. THE Task_State_Machine SHALL enforce the transition sequence: TODO → IN_PROGRESS → IN_REVIEW → TESTING → DONE.
2. THE Task_State_Machine SHALL permit the transition TESTING → IN_PROGRESS only when the QA_Agent attaches a defect report.
3. IF an agent attempts a state transition that is not permitted by the Task_State_Machine, THEN THE Task_State_Machine SHALL reject the transition and log the violation.
4. THE Task_State_Machine SHALL record the agent identity, timestamp, and previous state for every state transition.
5. WHEN a Task reaches the DONE state, THE Task_State_Machine SHALL move the Task's output to Project_Memory as a read-only artifact.

---

### Requirement 8: Failure Escalation Ladder

**User Story:** As a user, I want the system to handle agent failures systematically and escalate to a human only when truly necessary, so that the project keeps moving without infinite loops.

#### Acceptance Criteria

1. WHEN an agent encounters a failure on a Task, THE agent SHALL retry the Task using a different approach, up to a maximum of 2 retries (Escalation Level 1).
2. WHEN an agent has exhausted its 2 self-retries without resolving the failure, THE Lead_Agent SHALL assign a peer agent of the same domain to assist (Escalation Level 2).
3. WHEN the peer agent assistance at Level 2 does not resolve the failure, THE Architect_Agent SHALL re-examine the Task specification to determine whether the Task definition is incorrect (Escalation Level 3).
4. WHEN the Architect_Agent review at Level 3 does not resolve the failure, THE Lead_Agent SHALL rewrite and simplify the Task and reassign it to a fresh agent (Escalation Level 4).
5. WHEN the rewritten Task at Level 4 does not resolve the failure, THE Lead_Agent SHALL mark the Task as "needs human input", notify the user with a structured description of the failure, and pause all Tasks that depend on the blocked Task (Escalation Level 5).
6. THE Lead_Agent SHALL NOT retry a Task at Level 5 without receiving explicit input from the user.
7. WHEN the user provides input at Level 5, THE Lead_Agent SHALL resume the paused Tasks using the user-provided guidance.

---

### Requirement 9: Loop and Drift Prevention

**User Story:** As a user, I want agents to stay on track and never loop indefinitely, so that the system makes consistent forward progress.

#### Acceptance Criteria

1. THE Drift_Monitor SHALL check every agent's current work against its assigned Task specification at a configurable interval (measured in agent steps).
2. WHEN the Drift_Monitor detects that an agent's current work has diverged from its assigned Task, THE agent SHALL self-correct its work to realign with the Task specification.
3. IF the agent cannot self-correct within one step, THEN THE agent SHALL escalate to the Lead_Agent with a description of the divergence.
4. THE Loop_Counter SHALL increment each time an agent encounters the same error on the same Task.
5. WHEN the Loop_Counter for a Task reaches 3, THE agent SHALL immediately escalate to the next level of the Escalation_Ladder without further self-retry.
6. THE Loop_Counter SHALL reset to 0 when a Task transitions to a new state in the Task_State_Machine.

---

### Requirement 10: Self-Learning via Lessons

**User Story:** As a user, I want agents to learn from past failures so that they make fewer mistakes over time.

#### Acceptance Criteria

1. WHEN a failure on a Task is resolved at any level of the Escalation_Ladder, THE resolving agent SHALL write a Lesson to its Agent_Memory.
2. THE Lesson SHALL contain: a description of what failed, the root cause, the resolution applied, and a rule to avoid the same failure in future Tasks.
3. WHEN an agent is assigned a new Task, THE agent SHALL read all Lessons in its Agent_Memory before beginning work.
4. THE Agent_Memory SHALL persist Lessons across Tasks and across project sessions.
5. THE Lesson format SHALL be structured (not free-form prose) so that it can be parsed and retrieved consistently.
6. WHERE an agent has accumulated more than a configurable maximum number of Lessons, THE agent SHALL summarize older Lessons into consolidated rules to keep Agent_Memory within the configured size limit.

---

### Requirement 11: Memory Scoping and Immutability

**User Story:** As a user, I want agents to share information safely without overwriting each other's work, so that the project state remains consistent and auditable.

#### Acceptance Criteria

1. THE Project_Memory SHALL be readable by all agents at any time.
2. THE Lead_Agent SHALL be the only agent permitted to write to or modify Project_Memory.
3. WHEN a Task reaches the DONE state, THE Task's output SHALL be written to Project_Memory as an immutable artifact that no agent can modify.
4. THE Task_Memory SHALL be scoped to a single Task and SHALL be accessible only to the agent currently assigned to that Task and the Lead_Agent.
5. WHEN a Task reaches the DONE state, THE Task_Memory for that Task SHALL be discarded.
6. THE Agent_Memory SHALL be accessible only to the agent that owns it and the Lead_Agent.
7. IF an agent attempts to write to Project_Memory directly, THEN THE system SHALL reject the write and log the violation.

---

### Requirement 12: Confidence Scoring and Automatic Peer Review

**User Story:** As a user, I want low-confidence agent outputs to be automatically reviewed, so that uncertain work does not silently enter the project.

#### Acceptance Criteria

1. WHEN an agent produces an output for a Task, THE agent SHALL attach a Confidence_Score between 0 and 100 to that output.
2. THE Confidence_Score SHALL reflect the agent's self-assessed certainty that the output correctly fulfills the Task specification.
3. WHEN an agent's output has a Confidence_Score below a configurable threshold, THE Lead_Agent SHALL automatically assign a peer agent to review the output before the Task transitions to IN_REVIEW.
4. THE peer reviewer SHALL produce a structured review report and either approve the output or return it to the original agent with specific feedback.
5. WHEN the peer reviewer approves the output, THE Task SHALL proceed to IN_REVIEW as normal.
6. THE configurable Confidence_Score threshold SHALL default to 70.

---

### Requirement 13: Final Project Review

**User Story:** As a user, I want the Lead Agent to perform a final review before the project is declared complete, so that I receive a coherent and fully integrated deliverable.

#### Acceptance Criteria

1. WHEN all Tasks in the Task_State_Machine have reached the DONE state, THE Lead_Agent SHALL initiate a final project review.
2. THE Lead_Agent SHALL verify that all outputs in Project_Memory are consistent with the Master_Document.
3. THE Lead_Agent SHALL verify that all API_Contracts have been implemented by both the Frontend_Agent and the Backend_Agent.
4. WHEN the Lead_Agent identifies an inconsistency during the final review, THE Lead_Agent SHALL create a new Task to resolve the inconsistency and assign it to the appropriate agent.
5. WHEN the final review passes with no inconsistencies, THE Lead_Agent SHALL mark the project as COMPLETE and notify the user.
6. THE Lead_Agent SHALL produce a final summary report that lists all completed Tasks, all Lessons learned across all agents, and any items deferred for human action.

---

### Requirement 14: Master Document as Single Source of Truth

**User Story:** As a user, I want all agents to work from the same authoritative specification, so that there are no conflicting interpretations of the project requirements.

#### Acceptance Criteria

1. THE Lead_Agent SHALL ensure that every Task references the relevant section of the Master_Document.
2. WHEN an agent's proposed output contradicts the Master_Document, THE Lead_Agent SHALL reject the output and instruct the agent to revise it to comply with the Master_Document.
3. IF a change to the Master_Document is required during development, THEN THE Lead_Agent SHALL coordinate with the Architect_Agent to produce a revised Master_Document, approve it, and update Project_Memory before any agent acts on the change.
4. THE Master_Document SHALL be versioned, with each version recorded in Project_Memory alongside the timestamp and reason for the change.

---

### Requirement 15: Human-Lead Communication Interface

**User Story:** As a user, I want to communicate only with the Lead Agent in plain language, so that I never need to interact with individual agents directly or understand internal system details.

#### Acceptance Criteria

1. THE Lead_Agent SHALL be the sole point of contact between the human user and the ForgeAI system.
2. THE human user SHALL NOT communicate directly with any agent other than the Lead_Agent.
3. WHEN a new project is submitted, THE Lead_Agent SHALL conduct the Pre-flight_Checklist as a natural conversational exchange with the user, not as a technical form.
4. THE Lead_Agent SHALL proactively notify the user when a project milestone is reached, without the user needing to ask.
5. THE Lead_Agent SHALL notify the user when a Task is blocked at Escalation Level 5, presenting the problem in plain language with a clear description of options available.
6. THE Lead_Agent SHALL NOT surface internal agent failures, disputes, or technical errors to the user unless they require a human decision.
7. WHEN the user asks for a project status update, THE Lead_Agent SHALL respond with a plain-language summary of completed work, work in progress, and any pending decisions.
8. THE Lead_Agent SHALL present all requests for human input with clear options and sufficient context so the user can make an informed decision without technical knowledge.

---

### Requirement 16: Change Bucket and Change Planning

**User Story:** As a user, I want to submit client changes to the Lead Agent at any time, so that changes are properly planned and reviewed before they affect development.

#### Acceptance Criteria

1. WHEN the user submits a change request to the Lead_Agent during an active project, THE Lead_Agent SHALL place the request into the Change_Bucket with status PENDING.
2. THE Lead_Agent SHALL assign the Research_Agent and the Architect_Agent to produce a detailed plan for every change request in the Change_Bucket before it enters development.
3. WHEN the Research_Agent and Architect_Agent complete the change plan, THE Lead_Agent SHALL review the plan and either return it with suggested revisions or mark it GREEN.
4. THE Lead_Agent SHALL NOT mark a change plan GREEN until it is consistent with the existing Master_Document and Project_Memory.
5. WHEN a change plan is marked GREEN, THE Lead_Agent SHALL assign a Change_Type (NEW_FEATURE, REMOVE_FEATURE, MODIFY_FEATURE, or BUG_FIX) and a Change_Priority (CRITICAL, NORMAL, or DEFERRED) to the change.
6. WHEN a change plan is marked GREEN, THE Lead_Agent SHALL move the resulting tasks into the Development_Change_Bucket.
7. THE Lead_Agent SHALL perform a conflict analysis to determine whether the change affects any Task currently IN_PROGRESS before assigning a Change_Priority.
8. WHEN a change conflicts with a Task currently IN_PROGRESS, THE Lead_Agent SHALL assign Change_Priority CRITICAL.
9. WHEN a change does not conflict with any active Task, THE Lead_Agent SHALL assign Change_Priority NORMAL or DEFERRED based on urgency communicated by the user.
10. THE Lead_Agent SHALL inform the user of the change plan, its Change_Type, Change_Priority, and any impact on existing completed or in-progress work before tasks enter the Development_Change_Bucket.

---

### Requirement 17: Mid-Project Change Execution Without Interruption

**User Story:** As a user, I want client changes to be absorbed into the development flow without disrupting agents that are currently working, so that ongoing work is not broken by incoming changes.

#### Acceptance Criteria

1. AN agent SHALL complete its current Task before picking up any task from the Development_Change_Bucket, unless the change has Change_Priority CRITICAL.
2. WHEN a CRITICAL change conflicts with a Task currently IN_PROGRESS, THE Lead_Agent SHALL instruct the assigned agent to save a Task_Checkpoint of its current work and pause the Task.
3. WHEN an agent saves a Task_Checkpoint, THE agent SHALL record sufficient state so that work can be resumed from the checkpoint without loss of progress.
4. WHEN the CRITICAL change tasks are completed and QA-approved, THE Lead_Agent SHALL resume the paused Task from its Task_Checkpoint.
5. WHEN an agent completes its current Task and its regular task queue is empty, THE agent SHALL pick up the next task from the Development_Change_Bucket in priority order.
6. WHEN an agent completes its current Task and both its regular queue and the Development_Change_Bucket contain tasks, THE Lead_Agent SHALL determine the next task based on Change_Priority and project dependency order.
7. WHEN a change has Change_Type REMOVE_FEATURE and the feature has Tasks in DONE state, THE Lead_Agent SHALL transition the affected DONE Tasks to REWORK state and create removal tasks in the Development_Change_Bucket.
8. WHEN a Task is in REWORK state, THE Lead_Agent SHALL unlock the corresponding Project_Memory artifact to allow modification, and re-lock it as immutable when the REWORK Task reaches DONE.
9. THE QA_Agent SHALL verify that REWORK tasks have not introduced regressions in other DONE tasks before approving the REWORK task.
10. WHEN a change requires an update to the Master_Document, THE Lead_Agent SHALL coordinate the Master_Document revision before any development agent acts on the change tasks.
11. AN agent SHALL NOT be aware of whether a task originated from the original project scope or from the Development_Change_Bucket — tasks SHALL appear identical from the agent's perspective.
