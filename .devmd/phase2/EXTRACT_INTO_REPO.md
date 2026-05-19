# How to install this fix plan into the repo

From the repository root:

```bash
mkdir -p .devmd/fix-plan
cp -r Finance_SafeGrowth_Agent_FixPlan_MD_EN/* .devmd/fix-plan/
```

Expected structure:

```text
.devmd/
├── mockup/                       # already exists; contains mockup screenshots
└── fix-plan/
    ├── README.md
    ├── 00-review-baseline/
    ├── 01-p0-backend-persistence/
    ├── 02-p0-approval-audit-report/
    ├── 03-p0-gemini-rewrite-context/
    ├── 04-p1-rag-quality/
    ├── 05-p1-frontend-mockup-polish/
    ├── 06-p1-test-ci-docker/
    ├── 07-p2-demo-hardening/
    ├── agent-guides/
    ├── work-orders/
    └── templates/
```

Agent entrypoint:

```text
.devmd/fix-plan/work-orders/agent-start-instruction.md
```
