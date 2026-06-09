# Google Cloud Setup

This machine now has Google Cloud CLI installed through Homebrew:

```bash
gcloud --version
```

## Recommended Project Defaults

Use one dedicated GCP project for the TamilVU corpus work.

Suggested values:

```bash
TVU_GCP_REGION="asia-south1"
TVU_GCP_BUCKET="gs://tvu-corpus-$USER"
```

For lower latency from Sri Lanka/India, `asia-south1` is a reasonable default. If quota or services are limited there, use `asia-southeast1` or `us-central1`.

## Login

In your normal terminal:

```bash
gcloud auth login
gcloud auth application-default login
```

Inside Codex/sandboxed commands, use no-browser login:

```bash
gcloud auth login --no-launch-browser
gcloud auth application-default login --no-launch-browser
```

## Initial Configuration

After login:

```bash
gcloud projects list
gcloud config set project "$TVU_GCP_PROJECT"
gcloud config set run/region "$TVU_GCP_REGION"
gcloud config set artifacts/location "$TVU_GCP_REGION"
```

Enable only the services we need for the first pilot:

```bash
gcloud services enable \
  run.googleapis.com \
  storage.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com
```

Create the storage bucket:

```bash
gcloud storage buckets create "$TVU_GCP_BUCKET" \
  --location="$TVU_GCP_REGION" \
  --uniform-bucket-level-access
```

Create corpus folders:

```bash
gcloud storage cp /dev/null "$TVU_GCP_BUCKET/raw/.keep"
gcloud storage cp /dev/null "$TVU_GCP_BUCKET/processed/.keep"
gcloud storage cp /dev/null "$TVU_GCP_BUCKET/reports/.keep"
gcloud storage cp /dev/null "$TVU_GCP_BUCKET/indexes/.keep"
```

## Budget Guardrail

Set budget alerts in the GCP Console before running jobs:

- 25 USD
- 50 USD
- 100 USD
- 200 USD

Avoid always-on VMs for the first pilot. Prefer Cloud Run Jobs and Cloud Storage.

## Zsh Secrets

Do not put secrets in `.zshrc`, `.zprofile`, or this repo. Put project-specific non-secret defaults and secret references in a private file:

```bash
mkdir -p ~/.config/tvu-corpus
chmod 700 ~/.config/tvu-corpus
nano ~/.config/tvu-corpus/secrets.zsh
chmod 600 ~/.config/tvu-corpus/secrets.zsh
```

Example `~/.config/tvu-corpus/secrets.zsh`:

```zsh
export TVU_GCP_PROJECT="your-gcp-project-id"
export TVU_GCP_REGION="asia-south1"
export TVU_GCP_BUCKET="gs://your-tvu-corpus-bucket"
```

Then source it from `~/.zshrc`:

```zsh
# TamilVU corpus private config
if [[ -f "$HOME/.config/tvu-corpus/secrets.zsh" ]]; then
  source "$HOME/.config/tvu-corpus/secrets.zsh"
fi
```

Keep API keys in **Google Secret Manager** when possible:

```bash
printf '%s' "$OPENAI_API_KEY" | gcloud secrets create openai-api-key --data-file=-
```

After storing a key in Secret Manager, remove it from your shell file unless local tools need it.

## Zsh Cleanup Note

Your current `~/.zprofile` contains:

```zsh
eval "$(rbenv init - bash)"
```

For zsh, change that to:

```zsh
eval "$(rbenv init - zsh)"
```

That should remove the startup warning:

```text
command not found: complete
```

