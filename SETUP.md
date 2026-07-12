# SVG Profile Stats Updater Setup Guide

This document describes how to configure the automated pipeline to update the terminal-themed stats SVG card on your GitHub profile.

## Setup Instructions

### 1. Create a GitHub Personal Access Token (`GH_TOKEN`)

The automation requires a Personal Access Token (PAT) to read your statistics (including private/public repository counts, total commits, followers, contributions) and calculate Lines of Code (LOC) by cloning repositories:

1. Go to your GitHub **Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)** (or Fine-grained tokens).
2. Click **Generate new token (classic)**.
3. Provide a descriptive name (e.g., `Profile Stats Updater Token`).
4. Select the following scopes:
   - **`repo`** (Full control of private and public repositories - required to clone private repositories for LOC calculations).
   - **`read:user`** (To read user profile data).
5. Set an expiration date (or choose "No expiration" if you want it to run indefinitely).
6. Click **Generate token** and copy the token value immediately.

---

### 2. Add the Token to Repository Secrets

To make the token available to the GitHub Action workflow securely:

1. Navigate to your profile repository on GitHub (`Adv41t/Adv41t`).
2. Go to **Settings** > **Secrets and variables** > **Actions**.
3. Click the **New repository secret** button.
4. Name the secret **`GH_TOKEN`**.
5. Paste your Personal Access Token in the **Secret** field.
6. Click **Add secret**.

---

### 3. Enable Read/Write Workflow Permissions

The GitHub Action uses the `stefanzweifel/git-auto-commit-action` to commit the updated SVG back to your repository. This requires write permissions for the default `GITHUB_TOKEN`:

1. In your repository settings, go to **Settings** > **Actions** > **General**.
2. Scroll down to the **Workflow permissions** section.
3. Select **Read and write permissions**.
4. Click **Save**.

---

### 4. Enable First Workflow Run & Manual Dispatch

You can trigger the workflow manually to verify everything is set up correctly:

1. Click on the **Actions** tab of your repository.
2. Select the **Update Profile SVG** workflow from the sidebar on the left.
3. Click the **Run workflow** dropdown button on the right.
4. Keep the branch as `main` and click **Run workflow**.
5. Once the run completes, check the **Actions** logs. If any changes were found, the workflow will automatically commit the updated `assets/profile.svg` back to the repository.
