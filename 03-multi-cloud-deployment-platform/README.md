# Multi-Cloud Deployment Platform

A control plane that deploys a standardized application stack to multiple cloud
providers (AWS, GCP, Azure) from a single declarative spec, using Terraform for
provisioning and a Python orchestrator for workflow.

## Problem

Teams that go multi-cloud (for resilience, cost, or customer-data-residency
reasons) end up maintaining three divergent, copy-pasted deployment pipelines.
Drift creeps in, security baselines differ per cloud, and "deploy to all
regions" becomes a manual, error-prone ritual.

## Solution

- **One spec, many clouds.** A `deployment.yaml` describes the app, regions, and
  target providers. The orchestrator renders provider-specific Terraform from
  reusable modules.
- **Reusable Terraform modules** for the common primitives (network, compute,
  object storage) with a consistent variable interface across providers.
- **Idempotent, plan-first workflow.** The orchestrator always runs
  `terraform plan` and requires explicit approval (or `--auto-approve` in CI)
  before `apply`.

## Tech Stack

- **Terraform** — declarative, provider-agnostic IaC with state management.
- **Python + Click** — orchestration CLI (render, plan, apply, destroy).
- **Pydantic** — validate `deployment.yaml` before anything touches a cloud.
- **AWS / GCP / Azure providers** — pluggable backends.

## Usage

```bash
pip install -r requirements.txt
cp deployment.example.yaml deployment.yaml   # edit to taste

python -m orchestrator plan  --spec deployment.yaml
python -m orchestrator apply --spec deployment.yaml   # prompts for approval
```

Cloud credentials are taken from the standard provider environment variables
(`AWS_*`, `GOOGLE_APPLICATION_CREDENTIALS`, `ARM_*`) — never from the spec file.

## Security Considerations

- **No credentials in spec or code.** Provider auth uses each cloud's standard
  environment/credential-chain mechanism. The spec is safe to commit.
- **Least privilege.** Generated IAM roles request only the permissions the
  modules need; the README documents the minimal policy per provider.
- **Plan-first, fail-closed.** `apply` never runs without a reviewed plan;
  destructive actions require an explicit confirmation.
- **Remote, encrypted state.** State is configured for an encrypted remote
  backend (S3+DynamoDB / GCS / Azure Blob) with locking to prevent corruption.
- **Spec validation.** Pydantic rejects malformed specs before provisioning,
  preventing half-applied infrastructure.

## Lessons Learned

- A thin Python orchestrator over Terraform beat trying to do everything in HCL —
  validation, templating, and approval flow live where they're easiest to test.
- Keeping a single variable interface across provider modules is what made
  "deploy the same app to three clouds" actually one command.
- Plan-first with mandatory review caught more mistakes than any amount of
  post-deploy monitoring.
