# Emails

Our own email kit. The worker (`worker/mail.js`) sends these through Gmail as the
Drip the Cup address, using two Worker secrets: `GMAIL_USER` and `GMAIL_APP_PASSWORD`.

| File | When it goes out | To |
|---|---|---|
| `welcome-lab.html` | Sign-up on /learn/dictation | the subscriber |
| `welcome-free.html` | Sign-up on the free path at /learn | the subscriber |
| `welcome-founding.html` | "Save me a founding seat" at /learn | the subscriber |
| `notify-signup.html` | Every sign-up, after their welcome goes | the Drip the Cup inbox |
| `notify-inquiry.html` | Every business request; reply goes to them | the Drip the Cup inbox |
| `day1-did-it-work.html` | 1 day after a lab or free-path sign-up: the 3 things that break version 1 | the subscriber |
| `founding-day2-first-week.html` | 2 days after joining the founding list: pick the first build (reply A to D) | the subscriber |
| `day3-two-models.html` | 3 days after: models that hear vs models that understand | the subscriber |
| `day6-my-story.html` | 6 days after: AI didn't take my job, the method | the subscriber |

The follow-ups are sent by an hourly cron (`runSequence` in worker/mail.js). Each goes once, only to people
still subscribed, and only within two days of its due date, so adding a new step never emails old sign-ups.
A step that sells the Lab needs a postal address in its footer first (US CAN-SPAM).

Editing:
- The `<title>` is the subject line. The hidden `preheader` div is the preview text.
- Keep styles inline and layout in tables: mail apps drop `<style>`, flexbox, grid and web fonts.
- Placeholders: `{{site}}`, `{{unsubscribe}}` (welcomes), and for the notifications
  `{{email}}`, `{{source}}`, `{{interest}}`, `{{country}}`, `{{total}}`, `{{company}}`, `{{message}}`.
- No em dashes. Push to main and the next email uses the new file.

Limits: personal Gmail sends up to 500 a day; the worker stops at 450. Anything that
did not go out is retried after the next sign-up and by the hourly cron. Every send is in the D1 table `email_log`.
