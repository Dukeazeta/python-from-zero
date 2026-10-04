# Put the course online: Google Cloud's free server

The course runs on one small Linux server from Google Cloud's Always Free tier (an e2-micro), straight from Python, with [Caddy](https://caddyserver.com) in front for https. `deploy/pack.py` bundles the course and `deploy/install.sh` installs it.

## A. Make the server (once)

The quickest way is **Cloud Shell**, the terminal button at the top of the Google Cloud console. Use the same project as your sign-in client. Paste each command on its own and wait for the prompt to come back (in that terminal, Ctrl+C stops the running command).

1. **Billing:** link a billing account to the project (Google needs a card even for the free tier). Then add a $1 budget alert, so any charge reaches you straight away:
   ```bash
   gcloud services enable compute.googleapis.com billingbudgets.googleapis.com
   gcloud billing budgets create --billing-account=YOUR-BILLING-ACCOUNT-ID --display-name="Course alert" --budget-amount=1USD --threshold-rule=percent=0.5 --threshold-rule=percent=1.0
   ```
2. **Open web traffic and create the server.** Only `us-central1`, `us-west1` and `us-east1` are free:
   ```bash
   gcloud compute firewall-rules create allow-web --network=default --allow=tcp:80,tcp:443 --target-tags=web
   gcloud compute instances create python-from-zero --zone=us-central1-a --machine-type=e2-micro --image-family=ubuntu-2404-lts-amd64 --image-project=ubuntu-os-cloud --boot-disk-size=30GB --boot-disk-type=pd-standard --tags=web
   ```
   The free tier allows one e2-micro per billing account. Check that no other project on the same billing account already runs one.

## B. Give it an address

- **Free, no account:** sslip.io turns the server's IP into a name. For an IP of `35.1.2.3`, the address is `35-1-2-3.sslip.io`:
  ```bash
  IP=$(gcloud compute instances describe python-from-zero --zone=us-central1-a --format='value(networkInterfaces[0].accessConfigs[0].natIP)'); echo "${IP//./-}.sslip.io"
  ```
- **Your own domain** (needed later, when you publish Google sign-in): add an **A record** pointing to the server's IP.
- If you stop and start the server, its IP can change. Update the address when that happens.

## C. Install the course

1. On your computer: `python tools/build.py`, then `python deploy/pack.py`. This makes `deploy/out/python-from-zero.tar.gz` and `deploy/out/install.sh`. Nothing private goes in: no `.env` and no database.
2. In Cloud Shell, choose **⋮ > Upload** and upload both files.
3. Copy them to the server and install, with your address:
   ```bash
   gcloud compute scp python-from-zero.tar.gz install.sh python-from-zero:~ --zone=us-central1-a --quiet && gcloud compute ssh python-from-zero --zone=us-central1-a --quiet --command 'sudo bash install.sh python-from-zero.tar.gz YOUR-ADDRESS' && rm python-from-zero.tar.gz install.sh
   ```
   The installer adds a swap file, installs Caddy, runs the app as a locked-down service that restarts itself, and sets up daily database backups. It ends with `The app is running.`
4. Add your settings. Log in with `gcloud compute ssh python-from-zero --zone=us-central1-a`, run `sudo nano /etc/python-from-zero.env`, and fill in `GEMINI_API_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` and `OWNER_EMAIL` (see [sign-in.md](sign-in.md)). Save with Ctrl+O and Enter, leave with Ctrl+X, then run `sudo systemctl restart python-from-zero` and `exit`.
5. In your Google sign-in client, add `https://YOUR-ADDRESS/auth/callback` to the **Authorized redirect URIs**.
6. Open `https://YOUR-ADDRESS`. The first visit can take a minute while Caddy gets the https certificate.

## D. Updating

Rebuild and pack on your computer, upload the two files to Cloud Shell, and run the step C.3 command without the address. Your settings, the database and the backups stay as they are.

The command deletes the uploads at the end because Cloud Shell doesn't overwrite files with the same name. It saves a new upload as `python-from-zero.tar_(1).gz`, and the old bundle would be installed instead.

## E. Looking after it

- **Logs:** `sudo journalctl -u python-from-zero -f`
- **Backups:** made every day in `/var/lib/python-from-zero/backups`, keeping the last 14. They're on the same disk, so download a copy now and then.
- **Restoring a backup:** `sudo systemctl stop python-from-zero`, copy the backup over `/var/lib/python-from-zero/course.db`, run `sudo chown course:course` on that file, then `sudo systemctl start python-from-zero`.
- **Staying free:** one e2-micro in a free region, a standard disk of 30 GB or less, and 1 GB of outbound traffic a month. Python and the fonts load from other sites, so pages are light. Check the bill after the first few days.

## Before opening it to the public

Already built in:
- account deletion and progress download
- AI limits per person and for everyone
- rate limits
- a tutor that sticks to programming
- security headers (Content-Security-Policy, HSTS on https)
- error logging, with `/api/health` for an uptime monitor
- learner feedback, read at `/admin`

Your steps:
1. **Legal pages:** fill in every [bracketed] detail in `privacy.html` and `terms.html`, have them checked, then remove the draft notice.
2. **Gemini:** use a paid (billed) API key, and say in the privacy policy which tier you use.
3. **Publish Google sign-in:** in Google Auth Platform, under **Branding**, add your home page, `/privacy` and `/terms` addresses. Add your domain under **Authorized domains** and prove you own it in Google Search Console, then press **Publish app** under **Audience**. A free sslip.io address can't be verified, so you'll need your own domain for this.
4. **Soft launch** with 10 to 20 test users first, and read their feedback at `/admin`.
