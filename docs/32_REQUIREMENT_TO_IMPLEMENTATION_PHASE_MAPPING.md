# 32 — Requirement to Implementation Phase Mapping

This mapping is implementation-order based, not PDF-order based. Some requirements appear partially in one phase and become fully operational later.

| Requirement IDs | Implementation phase | Phase name | Business capability |
| --- | --- | --- | --- |
| ARCH-19.1, ARCH-19.2, API-18.1, API-18.2, CICD-20.1, CICD-20.2, DEPLOY-17.1 | Phase 0 | Repo, Local Infrastructure, and Engineering Standards | No customer-facing capability; delivers engineering execution reliability. |
| MT-1.1, MT-1.2, DATA-13.1, DATA-13.4, DATA-13.5, EVT-13.2, API-18.1, SEC-3.6, SEC-3.7, SEC-3.8 | Phase 1 | Database Baseline and Shared Foundations | Trusted persistence and shared service foundation. |
| SEC-3.1, SEC-3.2, SEC-3.3, SEC-3.8, MT-1.3 partial, API-18.1, API-18.3 partial | Phase 2 | Identity Service | Secure login and realm separation. |
| MT-1.3, MT-1.4, MT-1.5, MT-1.6 partial, SEC-3.4, SEC-3.5, RBAC-6.1, RBAC-6.2, RBAC-6.3, RBAC-6.4, API-18.3 partial | Phase 3 | Tenant Core, RBAC, and ABAC Authorization | Tenant admins can configure organization and secure access. |
| PA-2.1-PA-2.16, MT-1.2, MT-1.3, MT-1.4, MT-1.10, SEC-3.8 | Phase 4 | Platform Admin Service | gNxtHire operators can govern tenants without tenant-user APIs. |
| CFG-11.1, CFG-11.2, CFG-11.3, MT-1.5, MT-1.6, MT-1.7, HITL-14.4 partial | Phase 5 | Configuration Framework | Safe tenant/platform configuration without engineering changes. |
| SEC-3.9, DATA-13.1, DATA-13.5, CAT-4.7 partial, AAT-7.6, INT-10.3 partial | Phase 6 | Candidate Service | Recruiters can manage candidate data safely. |
| CAT-4.1-CAT-4.11, INT-10.3 partial, INT-10.4 partial, INT-10.5 partial | Phase 7 | Corporate ATS Service | Corporate tenants can run a manual requisition-to-offer lifecycle. |
| WF-5.1-WF-5.7, CAT-4.3, RBAC-6.2, RBAC-6.3, HITL-14.4 partial | Phase 8 | Workflow and Approval Engine | Governed approvals and workflow execution. |
| AAT-7.1-AAT-7.7, MT-1.6, SEC-3.5, SEC-3.9 | Phase 9 | Agency ATS Service | Agency tenants can manage client mandates and placements safely. |
| EVT-13.2, EVT-13.3, DATA-13.4, NOTIF-15.1, NOTIF-15.2, NOTIF-15.3, SEC-3.8 | Phase 10 | Event/Outbox, Audit Foundation, and Notification Service | Reliable asynchronous platform and multi-channel notifications. |
| INT-10.1-INT-10.5, API-18.4, MT-1.11, SEC-3.7, DATA-13.4 | Phase 11 | Integration Framework | Tenants can connect external systems consistently. |
| AIR-8.1-AIR-8.5, CAT-4.4, CAT-4.5, CAT-4.6, CAT-4.10, PA-2.12, PA-2.16 | Phase 12 | AI Recruiter Service | Advisory AI recruiter outputs with audit and review-required signals. |
| AIB-9.1, AIB-9.2, AIB-9.5, TEL-9.3, TEL-9.4, AIR-8.4, MOB-21.2 partial | Phase 13 | AI Interview and Telephony Service | AI interviews collect consented responses and produce review-required evaluations. |
| HITL-14.1-HITL-14.4, WF-5.5, AIR-8.5, AIB-9.5, PA-2.12, PA-2.16 | Phase 14 | Human-in-the-Loop Review Service | Humans approve/modify/reject AI outputs with audit and governance feedback. |
| BILL-16.1-BILL-16.4, MT-1.10, PA-2.2-PA-2.5 | Phase 15 | Billing, Subscription, and Metering Service | Monetization and usage visibility. |
| RPT-12.1-RPT-12.3, DATA-13.4, DATA-13.5, Phase 7 KPIs, PA-2.11, PA-2.12 | Phase 16 | Reporting and Analytics Service | Operational, commercial, AI, and platform dashboards. |
| SEC-3.8, SEC-3.9, DATA-13.5, PA-2.13, PA-2.14, RPT-12.3, Phase 7 risk/readiness | Phase 17 | Compliance, Privacy, and Retention Service | Enterprise privacy and compliance readiness. |
| MOB-21.1, MOB-21.2, BRAND-21.3, I18N-21.4, I18N-21.5, MT-1.6, MT-1.8 | Phase 18 | White-Labeling, Internationalization, and Mobile Readiness | Enterprise branded, localized, mobile-ready UX. |
| DEPLOY-17.1-DEPLOY-17.5, CICD-20.1-CICD-20.4, API-18.2, PA-2.11, PA-2.14, Phase 7 readiness | Phase 19 | Production Hardening, SRE, and Enterprise Readiness | Enterprise pilot/GA operational readiness. |


## Special notes

- HITL table/config foundations appear before AI activation; full review operations are Phase 14.
- AI phases build advisory/review-required functionality first; candidate-impacting automation waits for Phase 14.
- Billing waits for usage events.
- Reporting waits for event/fact foundations.
- Compliance erasure waits for mature domain data and audit surfaces.
