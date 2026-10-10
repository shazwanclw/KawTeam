# StakeMate AI — Complete Hackathon Blueprint

> **KawTeam workflow amendment, 11 October 2026:** The user's latest task workflow supersedes earlier shortlist and outgoing-message approval descriptions below. Every new conversation starts a task within a selected, inferred or newly named project; subsequent messages continue the selected task. Research retains the full evidence-backed candidate pool for non-binding liaison through connected providers. Final, complete replies are ranked for human approval, with a waitlist and one or multiple placement slots according to the request. Rejection advances the queue; filling the target closes other candidates locally. Only a separate supplier confirmation matching approved terms makes a placement Secured. Requirement edits need fresh terms. WorkBuddy remains deferred and real email is not connected; the tote demonstration is explicitly simulated. See [the current implementation checkpoint](docs/TASK_CONVERSATIONS_CHECKPOINT.md).

> **Track:** WorkBuddy Track 2 — Agentic Solutions  
> **Product tagline:** *From First Contact to Final Agreement.*  
> **Core idea:** An AI stakeholder liaison agent powered by Tencent WorkBuddy that discovers, evaluates, engages, negotiates, coordinates, and verifies outcomes with external stakeholders.

---

## Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Solution and Value Proposition](#3-solution-and-value-proposition)
4. [Primary Use Cases](#4-primary-use-cases)
5. [How Module A and Module B Integrate](#5-how-module-a-and-module-b-integrate)
6. [End-to-End Workflow Example](#6-end-to-end-workflow-example)
7. [Technical Architecture](#7-technical-architecture)
8. [Module A — Discovery, Sourcing, and Evaluation](#8-module-a--discovery-sourcing-and-evaluation)
9. [Module B — Communication and Negotiation](#9-module-b--communication-and-negotiation)
10. [Complete Feature Catalogue and Priorities](#10-complete-feature-catalogue-and-priorities)
11. [Trust, Safety, and Verification](#11-trust-safety-and-verification)
12. [Dashboard, Reporting, and Analytics](#12-dashboard-reporting-and-analytics)
13. [MVP Scope and Build Order](#13-mvp-scope-and-build-order)
14. [Hackathon Demo Scenario](#14-hackathon-demo-scenario)
15. [Judging Strategy](#15-judging-strategy)
16. [Beginner Guide: Integrating Tencent WorkBuddy](#16-beginner-guide-integrating-tencent-workbuddy)
17. [Starter MCP Server Code](#17-starter-mcp-server-code)
18. [Supplier Handoff Data Contract](#18-supplier-handoff-data-contract)
19. [Suggested Technology Stack and Code Components](#19-suggested-technology-stack-and-code-components)
20. [Product Decisions and Important Limitations](#20-product-decisions-and-important-limitations)
21. [Closing Pitch](#21-closing-pitch)
22. [Official References](#22-official-references)

---

## 1. Executive Summary

**StakeMate AI** is an autonomous stakeholder management and negotiation platform for student clubs and societies, small businesses, procurement teams, event organisers, and business development teams. It tackles the time-consuming work involved in locating suitable external stakeholders, evaluating them, communicating, following up, negotiating terms, coordinating meetings, and confirming commitments.

Rather than stopping at recommendations or drafting emails, StakeMate aims to take a user-defined goal through a controlled, tool-enabled workflow and deliver a measurable, verifiable result.

**Central principle:** Finding the right stakeholder is difficult; getting them to respond, agree, and deliver is even harder.

### Core value proposition

One prompt → one goal → end-to-end execution:

1. **Discover** the right people or suppliers.
2. **Engage** them through appropriate channels.
3. **Negotiate** price and terms within user-defined limits.
4. **Coordinate** meetings, messages, and next steps.
5. **Execute** approved actions.
6. **Verify** the outcome and report the result.

### Recommended hackathon direction

Build one shared stakeholder-management engine, demonstrated primarily through **supplier procurement and negotiation**. Add sponsorship acquisition as a second workflow only if time permits. Procurement is especially effective for a demo because judges can observe supplier comparisons, target-price decisions, negotiation responses, and final terms.

---

## 2. Problem Statement

### Pitch-ready problem statement

Students, organisations, and businesses face significant challenges when engaging external stakeholders, including suppliers, sponsors, vendors, and potential collaborators. The process is fragmented, time-consuming, and highly manual, requiring individuals to independently source contacts, evaluate options, initiate communication, negotiate terms, coordinate schedules, and manage follow-ups across multiple platforms.

These inefficiencies often result in missed opportunities, delayed decisions, poor negotiation outcomes, and unnecessary administrative workloads. The challenge is particularly significant for student-led organisations and small businesses that lack dedicated procurement, business development, or stakeholder-management teams.

**How might we leverage agentic AI to autonomously discover, engage, negotiate, and coordinate with external stakeholders, transforming fragmented communication into seamless, goal-driven, end-to-end collaboration?**

### Problem in one sentence

**Finding the right stakeholder is difficult. Getting them to agree, respond, and deliver is even harder.**

### Pain points discovered

- Hard to source suitable external stakeholders.
- Hard to find the right contact person or official contact channel.
- Hard to initiate and sustain communication.
- Hard to liaise across multiple platforms and conversations.
- Hard to follow up consistently.
- Hard to persuade a stakeholder or explain mutual value.
- Hard to find a middle ground that benefits both parties.
- Hard to negotiate a price or package that meets the user's target.
- Hard to coordinate a suitable meeting time.
- Hard to compare quality, price, reliability, reviews, and delivery conditions.
- Hard to manage commitments, action items, and deadlines after meetings.
- Hard to keep the full history and avoid repeating work.
- Student clubs and societies often lack dedicated procurement or partnership teams; small businesses may also lack dedicated staff for these tasks.

---

## 3. Solution and Value Proposition

### What StakeMate does

StakeMate AI is an AI-powered stakeholder engagement platform built on Tencent WorkBuddy. It manages the collaboration lifecycle: from discovering suitable stakeholders to contacting them, negotiating within defined constraints, coordinating next steps, and recording verified outcomes.

### Product positioning

> An autonomous AI stakeholder liaison agent powered by Tencent WorkBuddy that helps organisations discover, engage, negotiate, and collaborate with external partners—turning complex stakeholder management into goal-driven, end-to-end execution.

### Key distinction

A basic chatbot can write a sponsorship email or suggest a counteroffer. StakeMate is intended to go further: find candidates, use tools to compare them, send approved communications through connected services, process replies, replan after a rejection, and return an evidence-backed result.

### Core principles

- User goal and measurable outcome first.
- Research and communication should share a persistent mission state.
- Use structured data for handoffs between modules, not just free-form text.
- Autonomy operates inside user-defined boundaries.
- Every consequential result should be supported by evidence.
- Clearly distinguish live information, estimates, and simulated data.

---

## 4. Primary Use Cases

### Use Case A — Sponsorship Acquisition Agent

A student club needs RM5,000 of sponsorship for a technology event. StakeMate finds relevant companies, scores sponsor fit, prepares personalised proposals, sends approved outreach, tracks replies, negotiates benefits or contributions, and arranges meetings.

**Why it matters:** Relevant for student clubs, societies, conferences, and campus events.

### Use Case B — Autonomous Procurement Agent

An SME needs 300 custom-printed tote bags within a target budget. StakeMate researches suppliers, compares quotations and quality indicators, calculates total costs, negotiates within approved limits, and presents the best verified offer.

**Why it matters:** The result is measurable through price, total cost, delivery terms, quality, and savings against comparable initial quotations.

### Use Case C — Collaboration and Partnership Agent

A business wants a university partner for a workshop. StakeMate identifies potential collaborators, proposes mutual benefits, manages correspondence, schedules meetings, and tracks commitments.

**Recommendation:** Make Use Case B the main demo; use Use Case A as an optional additional workflow.

---

## 5. How Module A and Module B Integrate

### Main distinction

- **Module A — Discovery & Evaluation:** Finds, verifies, compares, filters, and ranks potential stakeholders.
- **Module B — Engagement & Negotiation:** Contacts the shortlist, requests information, follows up, negotiates terms, and coordinates next steps.

They should not be two disconnected tools or two independent agents that do not share information. They are specialised capabilities within a single WorkBuddy-orchestrated workflow.

### Module A → Module B handoff

Module A passes a structured, evidence-backed shortlist to Module B. The handoff should include:

- Stakeholder identity and official contact channel.
- Product/service or partnership fit.
- Quoted or advertised price, if available.
- Delivery cost, taxes, setup fees, and other known costs.
- Quality indicators, reviews, and source links.
- Lead time and deadline compatibility.
- Missing or uncertain information.
- User target price, hard budget, minimum quality, and deadline.
- Negotiation rules, communication approval policy, and purchase-approval requirements.

Module B should not need to research everything from scratch or ask the user to repeat the requirements.

### Return loop: Module B → Module A

The integration must be bidirectional:

1. Module A finds and ranks suppliers.
2. Module B contacts approved candidates and tracks their responses.
3. A supplier may reject a price, change delivery terms, or fail to respond.
4. Module B records the new information in the shared mission database.
5. The evaluation engine reranks candidates based on updated prices, terms, and availability.
6. If necessary, Module A searches for additional alternatives.
7. Module B continues with a suitable alternative.
8. StakeMate presents the best verified result and outstanding conditions.

**Key design requirement:** Shared state and controlled feedback loops—not just text passing between separate chatbots.

### Example sequence

1. User asks for 300 tote bags, delivered by 25 October, within RM1,500.
2. WorkBuddy extracts goals, constraints, and missing information.
3. Module A finds candidates through accessible web search, directories, marketplace APIs, and existing records.
4. The evaluation engine calculates total cost and ranks suppliers against price, quality, reliability, and lead-time criteria.
5. The shortlist is saved in the database and passed to Module B.
6. Module B drafts enquiries or counteroffers.
7. The user approves messages where required; communication tools send them.
8. Supplier replies are retrieved and classified.
9. The negotiation engine decides whether to counteroffer, clarify, wait, stop, or switch suppliers.
10. Module A updates rankings using new information.
11. StakeMate outputs final quotations, costs, evidence, delivery terms, savings calculations, risks, and required approvals.

---

## 6. End-to-End Workflow Example

### User request

> “I’m organising a technology event for 200 students. I need 300 custom tote bags within RM1,500, delivered before 25 October. Find the best suppliers, compare their quality, negotiate for a better price, and present the best available deal for my approval.”

### Workflow

1. **Goal analysis:** Extract budget, quantity, specifications, quality requirements, and delivery date. Ask only for essential missing details.
2. **Autonomous research:** Search accessible supplier sources and return candidates with evidence-backed prices, quality signals, delivery terms, and official contacts.
3. **Multi-criteria evaluation:** Compare total costs, delivery charges, quality, ratings, reliability evidence, and deadline compatibility.
4. **Negotiation handoff:** Pass the shortlist and negotiation limits into Module B.
5. **Approved outreach:** Draft and, after required approval, send enquiries or counteroffers through connected email/messaging services.
6. **Reply processing:** Classify replies as accepted, rejected, conditional, requesting information, or pending.
7. **Dynamic replanning:** If one supplier refuses the target, try an alternative or negotiate non-price terms such as simpler printing, bulk quantity, packaging, delivery, or a repeat-order opportunity.
8. **Verification:** Compare the latest offers against constraints, confirm what is actually agreed, flag unresolved conditions, and request user approval before a financial commitment.
9. **Final report:** Present the best available option, total landed cost, quality evidence, delivery terms, communication history, estimated savings against a comparable starting quote, and remaining risks.

### Negotiation example

- Initial quote: RM1,800.
- User's hard budget: RM1,500.
- Potential final offer: RM1,450.
- Difference: RM350, or about 19.4% of RM1,800.

These numbers are illustrative demo values, not real supplier quotes. Savings should only be described as realised when comparable terms and a final agreement are verified. If an offer excludes delivery or changes specifications, compare total equivalent cost before claiming savings.

---

## 7. Technical Architecture

### High-level architecture

```text
User
  ↓
StakeMate Dashboard
(goal, budget, deadline, requirements, approval settings)
  ↓
WorkBuddy Agent + StakeMate Skill
(understand goal → plan → invoke tools → inspect results → replan)
  ↕
StakeMate MCP Server
  ├── Module A tools
  │     ├── search_stakeholders
  │     ├── verify_supplier
  │     ├── compare_offers
  │     └── rank_candidates
  ├── Module B tools
  │     ├── draft_outreach
  │     ├── send_approved_message
  │     ├── prepare_counteroffer
  │     └── process_reply
  └── Common workflow tools
        ├── read_mission_state
        ├── update_mission_state
        ├── request_approval
        └── create_final_report
  ↕
Shared Backend + Database
(goals, contacts, sources, quotations, offers, messages, approvals, task states, audit log)
  ↕
External services
(web search, supplier APIs, email, calendar, documents)
```

### The parts in plain language

- **WorkBuddy = brain/orchestrator:** Understands goals, plans tasks, chooses tools, interprets outputs, and decides the next step.
- **MCP server = bridge/tool interface:** Exposes functions you implement so WorkBuddy can call them.
- **External APIs = hands:** Search websites, send/read messages, retrieve availability, or create calendar events, according to their permissions.
- **Database = persistent memory:** Stores missions, suppliers, quotations, negotiations, responses, approvals, and outcomes across steps or sessions.
- **Frontend = control centre:** Displays requirements, activity, comparisons, approval requests, status, and reports.
- **Approval/verification layer = safety gate:** Enforces budget, permission, and commitment rules.

### Important WorkBuddy integration idea

Use **MCP + Skill**: the MCP server exposes the actual tools; the Skill describes their purpose, ordering, constraints, and workflow. Avoid merely adding WorkBuddy branding to a conventional chatbot. WorkBuddy should genuinely call the tools and coordinate execution.

### One agent or multiple agents?

For the first hackathon version, use **one WorkBuddy-orchestrated agent** with specialised tools and a shared database. Add specialised agents later only if they provide a measurable improvement. Logical modules do not have to be separate AI models or separate servers.

---

## 8. Module A — Discovery, Sourcing, and Evaluation

### A1. Search and discovery

- Internet-wide search across accessible/indexed websites.
- Multi-source search across suitable public sources and supported directories.
- Product-specific vendor search.
- Geographic and delivery-area filtering.
- Budget filtering.
- Sponsor discovery by industry, target audience, and partnership fit.
- Collaborator discovery for universities, NGOs, startups, speakers, and industry partners.
- Public contact discovery from legitimate, official sources.
- Existing database search to reuse previously known stakeholders.
- Search expansion if the first search returns too few candidates.

### A2. Quality and suitability assessment

- Price comparison across advertised prices and quotations.
- Total-cost calculation including delivery, customisation/printing, setup fees, taxes where applicable, and other known fees.
- Quality assessment using specifications, certifications, samples, and evidence.
- Review analysis summarising recurring positive and negative themes.
- Review credibility flags for suspicious patterns or low review volume.
- Delivery assessment and deadline feasibility.
- Supplier reliability assessment using available fulfilment history, references, and other evidence.
- Capability matching for required quantity, customisation, or services.
- Risk and suitability checks for missing company details, unclear terms, and unusual payment requests.
- AI comparison report explaining trade-offs and linking to sources.

### A3. Ranking and selection

- Configurable compatibility score with adjustable weights.
- Cheapest qualifying option among candidates meeting all mandatory criteria.
- Best-value recommendation that may differ from the cheapest offer.
- Explainable ranking that states why candidates ranked as they did.
- User-managed shortlist.
- Backup suppliers for failed negotiations.
- Live reranking when new quotes, terms, or availability arrive.
- Price history for repeat suppliers (advanced).
- Target-price estimation from verified comparable offers (advanced).

### Example compatibility score

A transparent weighted score can combine normalised measures of price, quality, reliability, delivery, and fit. Let users adjust the weights. The ranking should show each subscore and supporting evidence rather than presenting an unexplained number.

Example supplier records (simulated only):

| Supplier | Price | Quality score | Delivery | Total score |
|---|---:|---:|---:|---:|
| Supplier A | RM1,650 | 82/100 | 7 days | 84/100 |
| Supplier B | RM1,420 | 75/100 | 12 days | 79/100 |
| Supplier C | RM1,750 | 94/100 | 5 days | 91/100 |

Supplier C has the best illustrative overall score, while Supplier B has the lowest price. The system should explain the trade-off. These values are simulated, not market research.

### Limitation to communicate honestly

A search engine cannot guarantee it has found the cheapest vendor anywhere on the internet. Recommendations should say they are based on accessible sources and terms that could be verified, and should note gaps in coverage or missing quotation details.

---

## 9. Module B — Communication and Negotiation

### B1. Outreach and communication

- Personalised emails based on the recipient's business and the user's goal.
- Enquiry generation to request quotes, specifications, delivery, and missing details.
- Sponsorship proposal generation and personalisation.
- Attach approved decks, quotation requests, and supporting documents.
- Multiple authorised communication channels where APIs/integrations are available.
- Reply monitoring using connected email/messaging accounts.
- Reply classification (accepted, declined, conditional, clarification required, pending).
- Intent and objection analysis (price concerns, delivery concerns, interest, questions).
- Context-aware responses using prior messages and offers.
- Follow-up scheduling after a defined time without a reply.
- Escalation for urgent, ambiguous, or sensitive messages.
- Full communication history.
- Multilingual messages in English, Bahasa Malaysia, and Chinese.

### B2. Negotiation intelligence

- User-set target price and hard budget.
- Counteroffer generation with rationale.
- Sending approved counteroffers through connected services.
- Offer tracking for every round and changed term.
- Negotiation-round limits.
- Conditional negotiation that changes strategy based on responses.
- Walk-away conditions when the budget is exceeded or mandatory requirements fail.
- Multi-variable bargaining across price, quantity, delivery, payment terms, packaging, and customisation.
- Win-win optimisation (e.g., bulk order or repeat business in exchange for a discount).
- Bulk and quantity price-break comparison.
- Best-and-final offer strategy where appropriate.
- Alternative-supplier switching after failure.
- Cross-supplier benchmarking using legitimate comparable quotations; do not share confidential competing offers improperly.
- Agreement comparison against the original target.
- Negotiation debrief explaining what worked, what failed, and why.

### B3. User-defined negotiation boundaries

Let the user set:

- **Target price:** ideal outcome.
- **Hard budget:** maximum permitted total spend.
- **Minimum quality:** minimum acceptable specifications or quality.
- **Deadline:** latest acceptable delivery date.
- **Negotiation limit:** maximum counteroffer rounds or stopping point.
- **Approval policy:** which messages or commitments require a human.

Example: ask for RM1,350; consider RM1,420 if all terms meet requirements; reject RM1,520 if the hard budget is RM1,500. The target is not permission for binding commitments. Never invent competing quotations or misrepresent another supplier to gain leverage.

---

## 10. Complete Feature Catalogue and Priorities

### Priority definitions

- **P0 — Core hackathon demo:** Essential for the first coherent end-to-end workflow.
- **P1 — Strong extension:** Valuable after the core flow works.
- **P2 — Advanced roadmap:** Longer-term or more complex feature.

### A. Agent orchestration and goal understanding

| Feature | What it does | Priority |
|---|---|---|
| Natural-language goal input | Accepts requests such as “find a sponsor for our event” | P0 |
| Goal decomposition | Breaks a goal into research, communication, and negotiation tasks | P0 |
| Requirement extraction | Extracts product, quantity, budget, location, and deadline | P0 |
| Clarification engine | Asks only for missing information needed to act | P0 |
| Dynamic task planning | Changes the plan when a supplier rejects an offer | P0 |
| Agent execution loop | Observes results, selects next actions, and repeats | P0 |
| Task dependency management | Ensures prerequisite actions happen in the right order | P0 |
| Workflow checkpoints | Saves and resumes interrupted missions | P1 |
| Parallel research | Searches different supplier categories simultaneously | P1 |
| Multi-agent collaboration | Specialises research, negotiation, and risk review | P2 |
| Failure recovery | Retries recoverable errors and chooses alternative tools | P1 |
| Confidence/uncertainty reporting | Flags incomplete evidence instead of guessing | P0 |
| User-defined autonomy | Lets users choose which steps can run independently | P1 |

### B. Module A features

| Feature | What it does | Priority |
|---|---|---|
| Internet-wide sourcing | Searches accessible indexed websites and sources | P0 |
| Multi-source search | Uses several accessible sources | P1 |
| Product-specific search | Finds vendors selling a specified product/service | P0 |
| Geographic filtering | Filters by country, state, city, or delivery area | P1 |
| Budget filtering | Identifies potentially affordable options | P0 |
| Sponsor discovery | Finds businesses with relevant audience/industry fit | P1 |
| Collaborator discovery | Finds universities, NGOs, startups, speakers, and partners | P1 |
| Public contact discovery | Retrieves official public contact channels | P0 |
| Existing database search | Reuses saved stakeholders and vendors | P0 |
| Search expansion | Finds alternatives if too few candidates emerge | P1 |
| Price comparison | Compares advertised prices and quotations | P0 |
| Total-cost calculation | Includes known delivery, setup, tax, printing and other costs | P0 |
| Quality assessment | Compares specifications, certifications, and evidence | P0 |
| Review analysis | Summarises available positive/negative review themes | P1 |
| Review credibility flags | Flags suspicious patterns or sparse evidence | P1 |
| Delivery assessment | Evaluates lead time and deadline compatibility | P0 |
| Reliability assessment | Uses available track records and references | P1 |
| Capability matching | Checks quantity, customisation and service fit | P0 |
| Risk/suitability checks | Flags missing details, unclear terms, unusual payment requests | P1 |
| Comparison report | Explains candidate trade-offs and cites sources | P0 |
| Configurable compatibility score | Weights price, quality, reliability, and delivery | P0 |
| Cheapest qualifying option | Finds the lowest-priced candidate meeting mandatory criteria | P0 |
| Best-value recommendation | Recommends the best trade-off rather than cheapest by default | P0 |
| Explainable ranking | Explains ranking and its evidence | P0 |
| Shortlist management | Approve/remove candidates | P0 |
| Alternative recommendations | Keeps backup suppliers | P0 |
| Live reranking | Recalculates ranking when new offers arrive | P0 |
| Price history | Tracks previous quotes | P2 |
| Target-price estimation | Estimates targets from verified comparable offers | P1 |

### C. Module B features

| Feature | What it does | Priority |
|---|---|---|
| Personalised email generation | Tailors emails to recipient and objective | P0 |
| Enquiry generation | Requests quotes and missing terms | P0 |
| Sponsorship proposals | Creates sponsor-specific proposals | P1 |
| Document attachments | Attaches approved decks and supporting documents | P1 |
| Multiple communication channels | Uses authorised email/messaging integrations | P1 |
| Reply monitoring | Retrieves replies from connected accounts | P1 |
| Reply classification | Categorises replies by outcome/intent | P0 |
| Intent/objection detection | Identifies concerns, objections, or interest | P1 |
| Context-aware responses | Uses prior messages/offers | P0 |
| Follow-up scheduling | Prepares follow-ups after a defined interval | P1 |
| Escalation rules | Flags ambiguous, urgent or sensitive messages | P0 |
| Communication history | Stores the interaction trail | P0 |
| Multilingual messaging | Supports English, Bahasa Malaysia, and Chinese | P1 |
| Target-price setting | Defines desired price and hard budget | P0 |
| Counteroffer generation | Suggests a price and reasoning | P0 |
| Counteroffer execution | Sends approved proposals via connected services | P0 |
| Offer tracking | Records offers, counteroffers, and changed terms | P0 |
| Negotiation-round management | Limits and records rounds | P0 |
| Conditional negotiation | Adjusts strategy based on reply | P0 |
| Walk-away conditions | Stops when limits/requirements fail | P0 |
| Multi-variable bargaining | Trades price against quantity, delivery, terms, packaging, etc. | P1 |
| Win-win optimiser | Proposes reciprocal value for concessions | P1 |
| Bulk discounts | Compares quantity/price tiers | P1 |
| Best-and-final offer | Requests final quote when sensible | P1 |
| Alternative switching | Returns to Module A when negotiation fails | P0 |
| Cross-supplier benchmarking | Uses legitimate comparable quotes where appropriate | P1 |
| Agreement comparison | Compares latest deal with original target | P0 |
| Negotiation debrief | Explains outcomes and lessons | P1 |

### D. Meeting, collaboration and relationships

| Feature | What it does | Priority |
|---|---|---|
| Meeting-slot discovery | Finds possible times | P1 |
| Calendar integration | Reads authorised availability and creates approved invites | P1 |
| Agenda generation | Creates agendas from goals and prior messages | P1 |
| Meeting notes | Summarises notes or authorised transcripts | P1 |
| Action-item extraction | Finds owners, deadlines and next steps | P1 |
| Meeting follow-up emails | Drafts minutes and follow-ups | P1 |
| Commitment tracker | Tracks promises, deliverables and overdue actions | P1 |
| Stakeholder CRM | Stores contact and interaction history | P0 |
| Relationship history | Records previous partnerships and outcomes | P1 |
| Team collaboration | Lets multiple club/business members work on one mission | P1 |
| Role-based access | Controls viewing, editing, and approvals | P1 |
| Duplicate contact detection | Prevents repeated approaches to same company | P1 |
| Relationship health monitoring | Flags unresponsive threads and unresolved commitments | P2 |
| Reusable templates | Reuses successful workflows and communications | P1 |

### E. Sponsorship and partnership features

| Feature | What it does | Priority |
|---|---|---|
| Event brief builder | Captures audience size, date, venue and goals | P1 |
| Sponsor matching | Ranks companies by industry, audience and fit | P1 |
| Sponsorship tier generator | Creates Gold/Silver/Bronze packages | P1 |
| Benefit matching | Matches sponsor needs to exposure, booths, talks, recruitment, etc. | P1 |
| Proposal personalisation | Tailors each deck/email | P1 |
| Sponsorship pipeline | Tracks prospects, outreach, replies, meetings and decisions | P1 |
| Sponsorship negotiation | Handles cash, in-kind support and deliverables | P1 |
| Sponsorship value tracking | Separates confirmed cash from estimated in-kind value | P1 |
| Sponsor deliverable tracker | Tracks logos and promised benefits | P2 |
| Post-event reporting | Generates reports and thank-you messages | P2 |
| Future-partner recommendations | Finds returning sponsors based on past outcomes | P2 |
| In-kind sponsorship optimisation | Compares non-cash support against actual event needs | P1 |

### F. Trust, safety, and verification features

| Feature | What it does | Priority |
|---|---|---|
| Source attribution | Stores evidence URLs and timestamps | P0 |
| Verified vs estimated labels | Separates confirmed quotes from estimates | P0 |
| Approval before sending | Lets users review consequential outgoing messages | P0 |
| Purchase approval | Requires explicit authorisation for financial commitments | P0 |
| Budget enforcement | Prevents actions beyond permitted limits | P0 |
| Contact/outreach controls | Respects opt-outs and avoids inappropriate bulk outreach | P0 |
| Credential protection | Stores API keys and account tokens securely | P0 |
| Least-privilege access | Requests only necessary permissions | P0 |
| Audit logs | Records tools, actions, results, approvals, and timestamps | P0 |
| Prompt-injection defences | Treats webpage/email instructions as untrusted data | P1 |
| Error/contradiction handling | Detects missing or conflicting prices and terms | P0 |
| Personal-data protection | Minimises stored personal/contact information | P0 |
| Human escalation | Requests assistance for risky or ambiguous terms | P0 |
| Supplier fraud warnings | Flags suspicious payment requests/inconsistent identities | P1 |

### G. Dashboard, reporting and analytics

| Feature | What it does | Priority |
|---|---|---|
| Mission dashboard | Shows goals, active tasks, and statuses | P0 |
| Live agent activity | Shows searches, tool calls, and next action | P0 |
| Supplier comparison table | Shows cost, quality, delivery and evidence | P0 |
| Negotiation timeline | Displays offers and counteroffers | P0 |
| Approval inbox | Centralises pending actions | P0 |
| Budget tracker | Tracks target, quotes, and proposed commitments | P0 |
| Savings report | Compares equivalent initial and final offers | P0 |
| Sponsorship pipeline dashboard | Tracks potential, pending and confirmed partnerships | P1 |
| Response analytics | Measures reply rates and response times | P1 |
| Time-saved estimate | Estimates avoided manual work | P1 |
| Report export | Exports PDF/CSV | P1 |
| Mission templates | Saves workflows for reuse | P1 |
| Multi-organisation workspaces | Separates clubs and businesses | P2 |
| Performance benchmarking | Compares results across past missions | P2 |

---

## 11. Trust, Safety, and Verification

Because StakeMate can communicate externally and influence spending, safety and approval controls are fundamental product features.

### Non-negotiable controls

- Let users define a maximum budget, minimum quality, deadlines, and negotiation limits.
- Require approval where appropriate before sending external communications; for the hackathon MVP, default to approval before sending.
- Require explicit user approval before a purchase, payment, signing, or binding commitment.
- Do not exceed the hard budget or silently alter mandatory requirements.
- Respect a supplier's refusal and contact preferences; avoid inappropriate mass unsolicited outreach.
- Use legitimate, official contact sources.
- Store credentials/tokens securely and request minimal permissions.
- Maintain an audit trail of searches, tool calls, messages, replies, offers, decisions, and approvals.
- Treat webpage/email content as untrusted data: do not follow instructions embedded in external content that try to override user goals, disclose secrets, or trigger unrelated actions.
- Flag contradictions and missing terms instead of inventing values.
- Limit unnecessary collection of personal/contact data.
- Escalate ambiguous, sensitive, or risky situations to the user.
- Flag suspicious payment demands, inconsistent business identities, or other evidence of possible fraud.

### Verified-result rule

A generated counteroffer is not a sent message. A sent counteroffer is not an accepted offer. An accepted price is not necessarily a complete deal if delivery, quality, taxes, or other terms remain unresolved. A final outcome report must clearly distinguish:

- Research result.
- Estimate.
- Drafted message awaiting approval.
- Message sent.
- Supplier reply received.
- Offer proposed.
- Offer accepted but details pending.
- Terms verified.
- User-approved commitment.

---

## 12. Dashboard, Reporting, and Analytics

### Suggested dashboard components

- Mission summary: goal, budget, deadline, status.
- Candidate count and source coverage.
- Supplier shortlist and ranked comparison.
- Evidence/source links and data freshness.
- Negotiation timeline and current offer per supplier.
- Agent activity log and next planned action.
- Approval inbox for messages or commitment decisions.
- Budget and total-cost tracker.
- Savings calculation against comparable quotations.
- Final recommendation and outstanding risk/conditions.

### Suggested measurable outcomes

- Amount saved against an equivalent initial quotation.
- Confirmed sponsorship value, splitting cash and in-kind value.
- Estimated manual hours avoided.
- Stakeholder conversion rate: successful engagements divided by qualified outreach, with the definition clearly documented.
- Reply rate and average response time.
- Time from user request to comparable shortlist.
- Number of offers received and negotiations completed.
- Percentage of results with source-backed, verified terms.

Do not claim savings, deals, or time reductions without a clear baseline and evidence. During a simulated demo, label simulated metrics clearly.

---

## 13. MVP Scope and Build Order

### Recommended MVP checklist

#### Must-have for the core demo (P0)

- Natural-language goal input.
- Goal/requirement extraction for product, quantity, budget, deadline, and quality.
- Supplier discovery and comparison for at least three candidates where data is available.
- WorkBuddy MCP integration in which WorkBuddy actually calls custom tools.
- Negotiation logic with a target price, hard budget, maximum rounds, and stopping rules.
- Approved email outreach or a clearly labelled controlled demo simulation.
- Reply classification and negotiation state updates.
- Live mission/activity dashboard.
- Shared persistent mission state.
- Budget/quality constraints, approval gates, audit history, and final report.

#### Strong extensions (P1)

- Automated follow-up.
- Calendar/meeting scheduling.
- Sponsorship deck generation.
- Meeting summary and action-item extraction.
- Multilingual support.
- Parallel research and workflow checkpoints.
- Sponsorship pipeline, relationship CRM, and report exports.

#### Longer-term/stretch (P2)

- Multi-agent negotiation war room.
- Relationship intelligence graph.
- Price history and cross-mission benchmarking.
- Advanced relationship health monitoring.
- Multi-organisation management and advanced analytics.

### Recommended build order

1. **Foundation:** Frontend goal form, mission database, basic dashboard, and a working WorkBuddy MCP connection.
2. **Module A:** Search suppliers, collect evidence, calculate total cost, and rank candidates.
3. **Module B:** Draft messages, simulate or retrieve responses, prepare counteroffers, and manage negotiation rounds.
4. **Integration:** Pass supplier results into negotiation; feed failed negotiations back into discovery and reranking.
5. **Verification:** Enforce budget limits, approvals, audit logs, and a final report.
6. **Expansion:** Add sponsorship, calendars, meeting notes, and team collaboration only after the main loop works.

### Suggested development checklist

- [ ] Natural-language goal input.
- [ ] Supplier discovery/comparison.
- [ ] WorkBuddy MCP integration.
- [ ] Negotiation agent.
- [ ] Email communication or controlled simulation.
- [ ] Live agent activity dashboard.
- [ ] Automated follow-up.
- [ ] Calendar scheduling.
- [ ] Sponsorship deck generation.
- [ ] Meeting summarisation.

---

## 14. Hackathon Demo Scenario

### Demo request

> “I’m organising a technology event for 200 students. I need 300 custom tote bags within RM1,500, delivered before 25 October. Find the best suppliers, compare their quality, negotiate for a better price, and present the best available deal for my approval.”

### What judges should see

1. **Goal analysis:** The agent extracts requirements, budget, quantity, and deadline.
2. **Autonomous research:** Searches suppliers and presents at least three plausible candidates with sources.
3. **Comparison:** Displays price, total costs, quality signals, delivery, and uncertainties.
4. **Negotiation:** Prepares and, with approval, sends a counteroffer.
5. **Reply handling:** Receives a controlled demo reply or a real authorised reply and classifies it.
6. **Dynamic replanning:** If the supplier rejects the target, proposes revised terms or moves to the next-ranked supplier.
7. **Verified outcome:** Shows offer history, final terms, comparable savings, outstanding conditions, and user approval status.

### Dashboard mock data

| Metric | Illustrative value |
|---|---:|
| Initial quote | RM1,800 |
| Final offer | RM1,450 |
| Difference | RM350 |
| Difference as % of initial quote | 19.4% |

Illustrative activity timeline:

- Requirements analysed: budget RM1,500, quantity 300.
- Three suppliers evaluated: price, quality, delivery compared.
- Counteroffer accepted: simulated supplier agreed to RM1,450.
- Final deal awaiting approval: no purchase order issued.

**Clearly label mock data and simulated suppliers/negotiations.** A controlled mock supplier-email service can guarantee a reply during the presentation; a separate live search integration can demonstrate real sourcing. Do not present simulated acceptance as a real transaction or realised savings.

---

## 15. Judging Strategy

| Judging criterion | How StakeMate should demonstrate it |
|---|---|
| Real problem and user value | Saves time in procurement, sponsorship, and stakeholder coordination for student clubs and small businesses. |
| Agentic workflow | Plans, searches, compares, communicates, negotiates, interprets replies, and replans. |
| Meaningful use of WorkBuddy | WorkBuddy genuinely invokes custom MCP tools and orchestrates the workflow. |
| End-to-end execution | Advances one user goal from requirements to an evidence-backed recommendation or verified agreement. |
| Usable and verifiable results | Shows quotations, evidence links, communication logs, approvals, and measurable outcomes. |

### Strong closing statement

> “Today, AI can write an email asking for sponsorship or a discount. But it is still up to us to find the right person, send the email, follow up, negotiate, and close the deal. StakeMate changes that. We don’t just help you communicate with stakeholders. We help you achieve outcomes.”

### Product closing line

**StakeMate AI — From First Contact to Final Agreement.**

---

## 16. Beginner Guide: Integrating Tencent WorkBuddy

> This section is a practical starting point. WorkBuddy screens, connector schemas, account eligibility, and Enterprise/API access can change; verify exact details against the current official documentation before relying on them during the hackathon.

### Step 1 — Install and explore WorkBuddy

1. Visit the official WorkBuddy website: <https://www.workbuddy.ai/>.
2. Follow its current installation/sign-in instructions.
3. Learn how to give WorkBuddy a goal and ask it to plan a workflow.
4. Try this prompt:

   “You are StakeMate, an AI procurement assistant. Help me plan a workflow for finding three qualified tote bag suppliers within RM1,500. Break down the tasks and explain what tools you need.”

At this point WorkBuddy can plan the workflow, but it will not yet have access to StakeMate's custom database or negotiation functions.

### Step 2 — Create a project and Python environment

```bash
mkdir stakemate-ai
cd stakemate-ai
python -m venv .venv
```

Windows PowerShell activation:

```powershell
.\.venv\Scripts\activate
```

Install the Python MCP SDK:

```bash
pip install "mcp[cli]"
```

Create `server.py` in the project folder.

### Step 3 — Implement custom MCP tools

The starter code is in [Section 17](#17-starter-mcp-server-code). It defines:

- `search_suppliers`: searches a small, simulated supplier list and marks whether prices are within budget.
- `prepare_counteroffer`: constructs a message for approval without sending it.

The data is deliberately simulated so that the first milestone is to prove that WorkBuddy can call the Python functions successfully.

### Step 4 — Connect the server to WorkBuddy

The earlier documented route is **Settings → MCP → Add MCP Server**, though the current screen may differ by version. Use the current WorkBuddy MCP/connector guide to verify the exact configuration method.

For a local stdio server, an example configuration shape is:

```json
{
  "mcpServers": {
    "stakemate": {
      "type": "stdio",
      "command": "C:\\path\\to\\stakemate-ai\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\path\\to\\stakemate-ai\\server.py"
      ]
    }
  }
}
```

Replace the example paths with the actual absolute paths on your machine. The format/entry point may differ by WorkBuddy version, so confirm it in the official connector docs. Keep the local server running/available as required by the configured transport.

### Step 5 — Test the integration

Try asking WorkBuddy:

> “Use the StakeMate tools to compare suppliers for 300 tote bags with a budget of RM1,500. Select the best budget-compatible supplier and prepare a counteroffer for another supplier. Do not send any messages.”

**First integration milestone:** WorkBuddy calls the Python tools and returns their results. This proves the essential connection between WorkBuddy and custom functionality.

### Step 6 — Replace demo tools with real integrations

| Capability | Suggested approach |
|---|---|
| Supplier discovery | A search API such as Brave Search or Tavily, subject to access, terms, and availability |
| Email sending/reading | Gmail API or Microsoft Graph with scoped authorisation |
| Meeting scheduling | Google Calendar API or Microsoft Graph |
| Persistent storage | Supabase PostgreSQL |
| Document generation | Python PDF generation |
| Frontend | Next.js + Tailwind CSS |
| Backend | FastAPI where a separate application API is useful |
| WorkBuddy connection | Custom MCP server; investigate Enterprise Managed Agents APIs if the dashboard must initiate WorkBuddy sessions directly |

A recommended stack is **Next.js + FastAPI + Supabase + WorkBuddy MCP**. The frontend manages the workflow, WorkBuddy orchestrates reasoning and tool calls, the backend enforces business logic/permissions, and the database preserves state.

WorkBuddy Enterprise Managed Agents APIs may provide ways to create agents and sessions, but access requirements and availability must be verified before making the hackathon architecture depend on them.

---

## 17. Starter MCP Server Code

This minimal demo uses simulated data. It does not perform internet search, send emails, or make real supplier contact.

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("StakeMate")

# Demo data. Replace with live supplier APIs later.
suppliers = [
    {"name": "Supplier A", "price": 1800, "rating": 4.6},
    {"name": "Supplier B", "price": 1450, "rating": 4.2},
    {"name": "Supplier C", "price": 1600, "rating": 4.8},
]

@mcp.tool()
def search_suppliers(product: str, budget: float) -> dict:
    """Compare demo suppliers against a budget."""
    ranked = sorted(suppliers, key=lambda x: x["price"])
    return {
        "product": product,
        "budget": budget,
        "suppliers": [
            {**s, "within_budget": s["price"] <= budget}
            for s in ranked
        ],
        "data_source": "demo"
    }

@mcp.tool()
def prepare_counteroffer(
    supplier_name: str,
    quoted_price: float,
    target_price: float
) -> dict:
    """Prepare a negotiation proposal for approval."""
    if target_price <= 0 or quoted_price <= 0:
        return {"error": "Prices must be positive"}

    return {
        "supplier": supplier_name,
        "proposed_price": target_price,
        "message": (
            f"Thank you for your quotation of RM{quoted_price:.2f}. "
            f"Would you consider RM{target_price:.2f}? "
            "We would be happy to discuss mutually "
            "beneficial terms."
        ),
        "status": "awaiting_user_approval",
        "sent": False
    }

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### What this code demonstrates

- Registers `StakeMate` as an MCP server.
- Exposes `search_suppliers` as a callable tool.
- Exposes `prepare_counteroffer` as a callable tool.
- Sorts demo supplier data by price and marks suppliers within budget.
- Drafts a counteroffer but explicitly returns `sent: False` and `awaiting_user_approval`.

Before using this in production, add robust input validation, typed schemas where appropriate, error handling, logging, authentication for real user data, persistent storage, and approval enforcement in the backend—not just in the model prompt.

---

## 18. Supplier Handoff Data Contract

Use structured data so that Module A and Module B share the same mission and supplier facts.

```json
{
  "mission_id": "MISSION-001",
  "product": "Custom tote bags",
  "quantity": 300,
  "budget_myr": 1500,
  "delivery_deadline": "2026-10-25",
  "minimum_quality": 4.0,
  "supplier": {
    "id": "SUP-001",
    "name": "Example Supplier A",
    "quoted_unit_price": null,
    "total_quoted_price": null,
    "delivery_cost": null,
    "estimated_lead_days": null,
    "contact_channel": "email",
    "contact_verified": false
  },
  "negotiation_rules": {
    "target_total_myr": 1350,
    "hard_budget_myr": 1500,
    "max_rounds": 3,
    "require_approval_before_sending": true,
    "require_approval_before_purchase": true
  },
  "status": "shortlisted"
}
```

The prices and rules are examples, not verified market data. Backend logic should populate supplier fields with sourced values or preserve unknowns explicitly instead of inventing quotes.

### Suggested shared database entities

- **Mission:** mission ID, user goal, constraints, status, deadlines, owner.
- **Stakeholder/Supplier:** ID, organisation, official contact channel, source, verification status.
- **Evidence/Source:** URL, retrieval timestamp, claim supported, confidence or caveat.
- **Quotation:** supplier ID, unit/total prices, currency, delivery, tax/fees, validity period, source.
- **Negotiation:** supplier ID, round number, offer, response, conditions, status.
- **Message:** channel, draft/sent/received status, timestamp, body/reference, approval record.
- **Approval:** action, approver, decision, timestamp, limits.
- **Task/Event log:** tool call, input/output reference, result, failure, retry count, timestamp.
- **Outcome:** selected option, terms verified, approval status, calculated savings and caveats.

---

## 19. Suggested Technology Stack and Code Components

### Suggested technologies

- **Frontend:** Next.js + Tailwind CSS.
- **Application backend:** FastAPI (Python).
- **Agent tool bridge:** Custom MCP server using the Python MCP SDK/FastMCP.
- **Orchestration:** Tencent WorkBuddy + a StakeMate Skill.
- **Database:** Supabase PostgreSQL.
- **Search:** Search provider API such as Brave Search or Tavily, subject to access/terms.
- **Email:** Gmail API or Microsoft Graph, with scoped permission and approval controls.
- **Calendar:** Google Calendar API or Microsoft Graph.
- **Documents:** Python-based PDF/document generation.

These are recommendations, not requirements. Choose the smallest set that the team can implement and test within the hackathon time limit.

### Recommended logical components

| Component | Responsibility |
|---|---|
| `goal_manager` | Understands the request and creates a mission |
| `discovery_service` | Searches for stakeholders and supplier candidates |
| `evaluation_engine` | Scores, filters, and compares candidates |
| `negotiation_engine` | Prepares counteroffers, enforces limits, and decides next steps |
| `communication_service` | Sends approved messages and retrieves replies |
| `workflow_orchestrator` | Coordinates Module A/B, manages retries and feedback loops |
| `approval_service` | Enforces approvals for messages and commitments |
| `stakeholder_database` | Stores contacts, quotes, conversations, and mission state |
| `reporting_service` | Generates comparisons, audit logs, and final reports |
| `workbuddy_mcp_server` | Exposes tool functions to WorkBuddy |

Avoid duplication of responsibilities: the negotiation engine should call the discovery/evaluation services for alternatives instead of implementing a second web-search system.

---

## 20. Product Decisions and Important Limitations

1. **Build one coherent workflow first.** Do not attempt the entire feature catalogue during the hackathon.
2. **Use one orchestrator initially.** WorkBuddy can call different specialised tools; separate autonomous agents are a later optimisation.
3. **Make the Module A–B link bidirectional.** Updated negotiations must change ranking and can trigger additional discovery.
4. **Prioritise actual tool calls.** The strongest demo shows WorkBuddy invoking MCP tools rather than merely describing actions.
5. **Avoid pretending simulated operations are real.** Mark demo suppliers, prices, messages, replies, and savings as simulated.
6. **Do not claim universal cheapest-vendor coverage.** Search coverage is finite and terms may be incomplete.
7. **Use equivalent cost comparisons.** Consider quantity, specifications, delivery, fees, taxes where applicable, lead time, and quote validity.
8. **Keep autonomy bounded.** The user sets budgets, minimum requirements, negotiation limits, and approvals.
9. **Separate offer acceptance from purchasing.** Final financial or binding commitments require explicit approval.
10. **Design for failure.** A supplier may not reply, search may fail, an API may rate-limit, or terms may be inconsistent. Retry safely, record failures, switch tools/candidates where appropriate, and escalate when necessary.
11. **Protect external communications.** Use authorised accounts, legitimate contacts, rate limits, opt-out controls, secure tokens, and an audit trail.
12. **Verify WorkBuddy access and API options early.** Do not assume Enterprise Managed Agents APIs or a particular setup interface is available to the hackathon account.

---

## 21. Closing Pitch

> “Today, AI can write an email asking for sponsorship or a discount. But it is still up to us to find the right person, send the email, follow up, negotiate, and close the deal. StakeMate changes that. We don’t just help you communicate with stakeholders. We help you achieve outcomes.”

**StakeMate AI — From First Contact to Final Agreement.**

An agentic stakeholder liaison system that connects discovery, evaluation, communication, negotiation, coordination, and verification into one goal-driven workflow.

---

## 22. Official References

Verify the current version and access requirements before implementing against these sources:

- WorkBuddy website: <https://www.workbuddy.ai/>
- WorkBuddy MCP Guide: <https://www.workbuddy.ai/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/MCP-Guide>
- WorkBuddy Connector Development Guide: <https://open.workbuddy.cn/en/docs/connector>
- Model Context Protocol: <https://modelcontextprotocol.io/>

**Documentation caveat:** Product UIs, schemas, APIs, account permissions, and feature availability can change. Confirm the exact MCP configuration and any managed-agent API access from the current official documentation before the hackathon demo.
