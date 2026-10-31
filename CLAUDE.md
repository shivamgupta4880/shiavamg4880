# Day Trader skills: notes for Claude

- The user is in India (IST, UTC+5:30). Whenever you show a time, show it in
  India time first and New York time in brackets, e.g. "8:45 PM IST (10:15 AM ET)".
  The user replies in Hinglish; answer in simple Hinglish.
- Keep every time in trader/config.json and in tool arguments in New York time
  (ET): the tools work in ET. When the user gives a time in IST, convert it to
  ET before writing it (ET is 9h30m behind IST during US daylight time,
  10h30m behind otherwise; US daylight time ends Nov 1 2026, resumes Mar 14 2027).
- Paper trading only unless the user clearly says otherwise. Never place an
  order without the trader-risk PASS and the user's explicit yes.
