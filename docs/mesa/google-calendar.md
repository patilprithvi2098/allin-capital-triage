# Booking straight onto Google Calendar (one-time setup, about 10 minutes)

The scheduling agent still reads your free/busy times from the secret iCal link. With this setup it also **writes** the
booked meeting onto your Google Calendar. Without it, it falls back to emailing an `.ics` invite. Access asked for:
calendar events only (`calendar.events`), not mail and not other Google data.

## 1. Create the Google OAuth client (in your browser)

1. Open https://console.cloud.google.com/ and sign in with the calendar's Google account.
2. Create a project (top bar → project picker → **New project**), e.g. "All In Capital triage".
3. **APIs & Services → Library**: search **Google Calendar API** → **Enable**.
4. **APIs & Services → OAuth consent screen** (Google Auth Platform):
   - App name "All In Capital triage", your email as support and developer contact.
   - Audience: **External**, keep it in **Testing**, and add your own Gmail under **Test users**.
5. **Clients → Create client** → type **Desktop app** → name it → **Create**.
6. Keep that window open: it shows the **Client ID** and **Client secret**.

## 2. Download the client file

On the client's page click **Download JSON**. It lands in Downloads as `client_secret_….json`; the sign-in script reads
it and saves `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env` (or save them yourself with
`python3 scripts/set_env.py NAME --clipboard`). Delete the downloaded file afterwards.

## 3. Sign in once

    cd /Users/patilprithvi/AllInCapital && python3 scripts/google_auth.py

Your browser opens Google's consent page. Google warns that the app is unverified (it is your own app in Testing):
click **Continue**, allow calendar access, and the script saves `GOOGLE_REFRESH_TOKEN` in `.env`.

## Good to know

- While the consent screen is in **Testing**, Google expires the sign-in after **7 days**. The agent then stops booking
  with "Calendar permission error" (status Stopped) and you run step 3 again. Publishing the app removes that limit.
- On Vercel, put the three `GOOGLE_*` values in the project's environment variables, never in the repo.
- To revoke: https://myaccount.google.com/permissions → All In Capital triage → Remove access.
