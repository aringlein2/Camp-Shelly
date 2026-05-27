# Deploy Camp Shelly Hub on the internet

This walks you through getting the site live on a URL you can share. About 15 minutes.

## What you'll end up with

A URL like `https://camp-shelly-hub.onrender.com` that you can text to everyone going on the trip. The site has a built-in privacy gate — only the phone numbers you add will be able to sign in.

## What you need

- A GitHub account (free, takes 2 minutes if you don't have one).
- A Render.com account (free, sign in with your GitHub account).
- A credit card on Render for the $7/month plan (recommended; keeps the database persistent).

---

## Step 1 — Create a GitHub account if you don't have one

Go to https://github.com/signup and follow the prompts.

## Step 2 — Install GitHub Desktop

This is the easy way to push code without using the command line. Download from https://desktop.github.com and install. Open it and sign in with your GitHub account.

## Step 3 — Publish the project to GitHub

1. In GitHub Desktop, click **File → Add Local Repository**.
2. Browse to `C:\Users\aring\Desktop\Competition\camp-shelly-hub` and select it.
3. If it asks "this directory does not appear to be a Git repository", click **create a repository** in that dialog.
4. Name it `camp-shelly-hub`, leave the description blank, and click **Create Repository**.
5. At the top of the GitHub Desktop window, click **Publish repository**.
6. **IMPORTANT:** check the box **"Keep this code private"**. (Public is fine too, since the site has its own login gate and there are no secrets in the code, but private is safer.)
7. Click **Publish Repository**.

Your code is now on GitHub.

## Step 4 — Deploy to Render

1. Go to https://dashboard.render.com and sign in with GitHub.
2. Click **New +** in the top right → **Blueprint**.
3. Connect your GitHub account if prompted, and authorize Render to see your `camp-shelly-hub` repository.
4. Pick the `camp-shelly-hub` repo and click **Connect**.
5. Render reads the `render.yaml` file in the repo and shows you what it'll create. Click **Apply**.
6. You'll be asked to set **ADMIN_PHONE** — enter your phone number (any format). This is how you'll sign in as the first admin. Click **Save**.
7. Render starts building. It takes about 3–5 minutes the first time. You'll see logs scrolling.

When it finishes, the page shows a green "Live" badge and a URL like `https://camp-shelly-hub-XXXX.onrender.com`. **That's your site.**

## Step 5 — Sign in and add everyone else

1. Open your Render URL in your browser.
2. Sign in with the phone number you set in step 4.
3. Go to **Admin → People → + Add person** and add each family.
4. Text or email the URL to everyone. They each sign in with the phone you entered for them.

## Picking a plan

The `render.yaml` is set to the **Starter** plan ($7/month). This gets you:
- Always-on (no 30-second cold start when someone visits)
- 1 GB persistent disk so your SQLite database doesn't reset on every redeploy
- Custom domain support if you want `camp-shelly.uucil.org` later

If you'd rather try the **Free** plan first to test: edit `render.yaml`, change `plan: starter` to `plan: free`, remove the `disk:` block (free plan can't have persistent disks), and re-push. Caveats: the site sleeps after 15 min of no traffic and takes ~30 sec to wake up, and any data people post gets wiped if you redeploy. Fine for a quick test, not great for the actual trip.

## Updating the site later

Any changes you make locally and push through GitHub Desktop will auto-deploy on Render (because `autoDeploy: true` is in `render.yaml`).

## If you get stuck

Tell me what step you're on and what message Render shows, and I'll unblock you.
