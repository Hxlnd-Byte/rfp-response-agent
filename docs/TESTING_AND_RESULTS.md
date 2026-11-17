# Testing and results

## The invented test

| Built into the test | Detail |
|---|---|
| RFP | 18 requirements from a fictional healthcare customer |
| Product catalogue | 20 entries: 14 available, 3 partial, 3 not offered or on the roadmap |
| Right answers | 12 requirements we meet, 3 partly, 3 gaps |
| Past bids | 6 bids (3 won, 3 lost), 44 reusable answers |
| Web pages | 13 invented pages: 8 about three competitors, 5 about the customer |
| Planted facts | 18 competitor claims and 8 customer statements, each with an exact quote |

Because the test is invented, the right answers are known and the agent can be marked like an exam.

## What is already proven (no AI involved)

Run `python -m unittest discover tests -v`. All 18 tests pass. They show that:
- code finds all 18 requirements, the right catalogue entry and the right fit when the topic is right
- a relevant past answer is in the top 3 for 18 of 18 requirements, and won, recent bids rank first
- a quote that is not in its page is removed
- invented numbers, competitor names, old-customer names, sales words and hidden gaps are caught
- a search phrase containing RFP text is refused
- two different people must sign; edits clear sign-offs; approved packs are not overwritten
- the six-month review adds approved answers once, and only after a result is recorded
- a spec sheet only suggests catalogue entries; a person must choose the status and give a name
- the kill switch stops a run

A stand-in reader that makes mistakes on purpose (`--mode noisy_mock`) gets 15 of 18 topics right; its 4 false claims are removed by the quote check and its 2 answers with a planted old-customer name and invented number fail their checks. That shows the checks and the scoring notice mistakes. It says nothing about how a real model performs.

## Still to measure: the real AI model

Run on your workstation:
```powershell
python run_demo.py
```
and fill in:

| Measure | Result on your machine |
|---|---|
| Model and graphics card | to fill |
| Requirements sorted into the right topic, out of 18 | to fill |
| Fit correct, out of 18 | to fill |
| Draft answers passing every check, out of 18 | to fill |
| Answers needing a retry | to fill |
| Competitor claims found with a verified quote, out of 18 | to fill |
| Customer statements found with a verified quote, out of 8 | to fill |
| Statements removed (quote not in page) | to fill |
| Minutes for the full run | to fill |

## The time model

`python value_model.py` reads `assumptions.toml`. The one benchmark is the average of 33 hours per RFP response from the Loopio and APMP 2026 survey (https://link.loopio.com/hubfs/Content%20Pieces/FY26%20Trends%20Report/trends-report-2026-digital-Master.pdf). Every other input is an assumption to replace with your own figure. The low case loses money on purpose: with few RFPs a year the setup time is not repaid.
