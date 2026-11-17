# Putting it in a customer environment

The code does not change. You replace four data files and add RFPs.

| File | What it holds | How to fill it |
|---|---|---|
| `data/company.json` | Your company name and the competitors to research | Edit by hand |
| `data/taxonomy.json` | The topics RFPs ask about (a code and a plain label) | Start from the demo list; add your own |
| `data/catalog.json` | Each product or service capability, its topic and an honest status: available, partial, roadmap or not_offered | Product and presales leads agree this. Upload spec sheets on the Products page to get suggested entries, then set each status by hand. It is the most important file |
| `data/library.json` | Past RFP answers with won or lost | `python import_library.py your_answers.csv` |
| `data/rfp/` | New RFPs as .txt or .docx (PDF if you install pymupdf) | Use **Add an RFP** on the Start page, or paste it there |

Then set `mode = "searxng"` in `config.toml` for live research, or leave it on `off`. Delete `data/truth` and `data/web_snapshot.json`; they belong to the demo.

## A sensible first month

1. Week 1: agree the catalogue with product leads. Be strict about "partial".
2. Week 2: import answers from the last 10 to 20 bids. Remove anything confidential to another customer.
3. Week 3: run two recent RFPs you have already answered and compare the draft with what was sent.
4. Week 4: use it on one live bid, with the usual process as a safety net. Time both.

## Things to check first

- **Requirement numbering.** The parser expects numbered requirements (R-01 or 3.1.2 style). RFPs laid out as tables or questionnaires need a small change to `parse_rfp`.
- **Confidentiality.** Past bids may contain another customer's details or terms covered by a non-disclosure agreement. Clean the library before loading it.
- **Who owns the catalogue.** If nobody keeps it current, the agent will confidently position last year's product.
- **Rules on competitor statements.** Legal should agree how competitor evidence may be used.

## The six-month review

On the Learn page, press **Run the review now**, or schedule `python -c "from rfpagent import learn; learn.review()"` with Windows Task Scheduler. It adds approved answers that have a recorded result to the library and writes a report: what the team edited, which requirements we could not meet, and what was won and lost. A person should read it and decide what to change in the catalogue and library.
