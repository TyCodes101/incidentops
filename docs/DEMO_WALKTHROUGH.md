# Suspected account compromise walkthrough

1. Explicitly seed the local synthetic demo and sign in as demo.admin. Dashboard counts come from persisted records.
2. Open Analyzer. Import `docs/example-logins.csv` or paste its text. Analyze twelve authorized synthetic records. The demo.finance account has five failures in ten minutes followed by success. This is not proof of intrusion.
3. Select Create investigation incident. Read the rule, sources, and time in the new incident description. It begins open at medium severity because it needs human triage.
4. As admin, assign demo.admin (or create an Analyst on Team and assign them). Change status to investigating. Raise severity when the fictional scenario warrants it.
5. Add an observation: “Account owner contacted; unfamiliar sign-in acknowledged. Authorization for reset confirmed.” Record containment as notes; IncidentOps does not reset external accounts or revoke their sessions.
6. Edit the summary when context arrives. History records each change and actor. Add a resolution rationale, then Resolve incident and accept the confirmation.
7. Return to Dashboard. Totals and recent activity reflect the case. Search/filter the queue for the resolved report. Open Activity to inspect the trail. Sign out.

Use fictional content during recruiter demos. A Viewer can inspect cases but cannot create, update, assign or add notes. An Analyst may investigate but assignment is reserved to admins.
