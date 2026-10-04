# Sign in with Google

Without Google settings, the course has no sign-in and saves progress on the computer running it. With them, lessons stay open to everyone, and signing in saves each person's progress and turns on the tutor for them.

## 1. Make a Google sign-in client (once)

1. Open https://console.cloud.google.com/ and create a project (any name, such as "Python from zero").
2. Set up the consent screen (**Google Auth Platform**, then **Branding** and **Audience**). App name "Python from zero", your email as the support contact, audience **External**. While the app is in **Testing**, only the Google accounts you add as test users can sign in. That's a good way to start.
3. Go to the **Clients** page, press **Create client**, choose **Web application**, and add these **Authorized redirect URIs**:
   - `http://localhost:8765/auth/callback` (to try it on your computer)
   - `https://YOUR-ADDRESS/auth/callback` (once it's online)

   Leave **Authorized JavaScript origins** empty: sign-in runs on the server.
4. Copy the client ID and client secret. Google only shows the secret once.

## 2. Turn it on

Put the two values in `.env` (`GOOGLE_CLIENT_ID=` and `GOOGLE_CLIENT_SECRET=`), set `OWNER_EMAIL=` to your Google email, and restart the app. A **Sign in with Google** button appears at the top right.

The owner sees a **Course overview** at `/admin` (accounts, today's AI use, and feedback learners send). The first time the owner signs in, any progress saved before sign-in was turned on moves into their account.

The client secret is a password for your app. Keep it in `.env` or your server's settings, never in a file you share or commit. `.gitignore` already leaves `.env` out.

## Settings

| Setting | What it does |
|---|---|
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Turn sign-in on. |
| `PUBLIC_URL` | The address people use, such as `https://python.example.com` (no slash at the end). Default `http://localhost:8765`. |
| `OWNER_EMAIL` | Your Google email: you get the overview page and the progress saved before sign-in. |
| `ALLOWED_EMAILS` | Optional. Only these emails may sign in, comma separated. |
| `TUTOR_DAILY_LIMIT` | AI requests per person per day (default 100 with sign-in). |
| `TUTOR_TOTAL_DAILY_LIMIT` | AI requests per day for everyone together (default 2000), so one busy day can't run up your Gemini bill. |

## Moving progress

Everyone can use **Download my progress** and **Upload a progress file** in the account menu, for example to move from a copy on their own computer to a hosted one.

## How sign-in is protected

- Google's authorization-code flow with PKCE, a one-time `state` tied to the browser by a cookie, and a `nonce` checked in the ID token.
- Sessions last 30 days in an HttpOnly, SameSite=Lax cookie (Secure, with the `__Host-` prefix, on https). Only a hash of each session cookie is stored.
- Requests that change data are refused if they come from another website, and sign-in, saving and the tutor are rate limited.
- People can delete their account from the account menu, which removes their progress, chats and sign-ins.

`python tools/test_app.py` checks all of this against a stand-in for Google, so it needs no real account. `python tools/test_app.py --serve` keeps that test app running at http://localhost:8772 for clicking through.
