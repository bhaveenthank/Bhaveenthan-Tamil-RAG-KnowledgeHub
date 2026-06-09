---
name: TVU_Security_Analyser
description: Use for TamilVU project security review: crawl ethics, robots/rate limits, secret handling, GCP IAM, bucket access, dependency risk, data exfiltration risk, and cost-safety guardrails. Do not use for general implementation unless security fixes are required.
---

# TVU Security Analyser

Review the project for practical safety, not paperwork.

## Workflow

1. Check whether the action touches network, scraping scope, secrets, auth, GCP, storage permissions, or dependencies.
2. Verify no credentials are committed:
   - `.env`
   - service account JSON
   - API keys
   - gcloud auth databases
3. For scraping, require:
   - explicit scope
   - rate limit
   - robots/site-policy check before expansion
   - raw snapshot provenance
   - retry limits
4. For GCP, prefer:
   - least-privilege service accounts
   - private buckets
   - budget alerts
   - Secret Manager for API keys
   - Cloud Run Jobs over always-on compute
5. Report findings by severity and include concrete fixes.

## Red Flags

- Public writeable buckets.
- Broad `roles/editor` service accounts.
- Recursive crawl without path allowlists.
- Secrets in shell history, repo files, logs, or CI output.
- Commands requiring unrestricted network or filesystem access without a narrow reason.

