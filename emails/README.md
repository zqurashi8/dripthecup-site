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

Editing:
- The `<title>` is the subject line. The hidden `preheader` div is the preview text.
- Keep styles inline and layout in tables: mail apps drop `<style>`, flexbox, grid and web fonts.
- Placeholders: `{{site}}`, `{{unsubscribe}}` (welcomes), and for the notifications
  `{{email}}`, `{{source}}`, `{{interest}}`, `{{country}}`, `{{total}}`, `{{company}}`, `{{message}}`.
- No em dashes. Push to main and the next email uses the new file.

Limits: personal Gmail sends up to 500 a day; the worker stops at 450. Anything that
did not go out is retried after the next sign-up. Every send is in the D1 table `email_log`.
