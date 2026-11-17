# Privacy and guardrails

## What leaves the machine

| Run mode | What leaves |
|---|---|
| Demo (saved web pages) | Nothing. |
| Live web search switched on | Search phrases only: a company name plus one approved topic word, such as "Norvane Systems pricing". Every phrase is written to the audit log. |
| AI model | Nothing. The model runs locally through Ollama. |

The RFP text, past bids, the catalogue and the drafts are never sent anywhere. The code that builds a search phrase refuses anything that is not a short company name plus a word from the approved list in `config.toml`, and a test proves it.

Be aware that a search for a customer's name can itself hint that you are bidding. If that matters, keep web mode on `snapshot` or `off`.

## People

The customer view uses public, professional sources only: press releases, annual reports, conference talks and job adverts. It records a role ("Chief Information Officer"), not a name. It does not look at personal social media. The AI is told never to give a name, but this is an instruction, not a guarantee, so the reviewer should remove any name that slips through.

## Checks run by code

On every customer-facing answer:
- it must cite the catalogue entry it relies on, and only sources it was given
- no number that is not in its sources
- no competitor name and no name of a past customer
- no sales words such as "guarantee" or "world-class"
- where the catalogue says partial or gap, no "fully"; a gap must be stated plainly
- a word limit

On every competitor claim and customer statement: the quote must appear in the page it cites, or it is removed and counted.

On every talking point: it must cite a source that exists.

Before the AI sees a past answer, code removes any sentence that names the old customer.

## Controls on the agent

- It cannot send anything. There is no email or upload code. Approved responses are saved to a folder.
- Two different people must sign. Any edit clears earlier sign-offs. A draft with a failing answer cannot be signed.
- Approved packs are never overwritten.
- Kill switch: `enabled = false` in `config.toml` or a file called `STOP`.
- A cap on AI calls per run, and an audit log of every run, edit, signature and search.

## What the checks do not catch

- **A wrong reading.** If the AI files a requirement under the wrong topic, the answer will be well-formed and wrong. A person catches that.
- **A true quote that misleads.** A quote can be real and still be out of date or out of context. The date and link are shown so the team can judge.
- **Tone and strategy.** The checks stop bad claims. They do not make a response persuasive.
