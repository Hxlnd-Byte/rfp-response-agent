# Setup guide: Windows workstation

About 20 minutes, plus the model download. Licence cost: nothing. These steps were written from the tools' documentation and have not been run on Windows by the author. Please report anything that differs.

## Option A: double-click start (recommended first)

1. Open **PowerShell** and install the two programs:
```powershell
winget install Python.Python.3.12
winget install Ollama.Ollama
```
If winget is missing, download them from python.org (tick "Add python.exe to PATH") and ollama.com. Close and reopen PowerShell.

2. Download the AI model once (about 5 GB):
```powershell
ollama pull qwen2.5:7b
```

3. Get the project: download the zip from GitHub and unzip it, or
```powershell
git clone https://github.com/Hxlnd-Byte/rfp-response-agent
```

4. Double-click **start_windows.bat** in the project folder. A browser tab opens at http://localhost:8765. Leave the black window open while you work; close it to stop the tool.

There is no `pip install` step and no virtual environment. The tool uses only what comes with Python 3.11 or newer.

## Using the screen

A banner on every page says the one thing to do next, and a row of steps shows how far the bid has got.

| Page | What you do |
|---|---|
| Start | Add an RFP (upload or paste) or a spec sheet, then press **Prepare draft with AI**. Use **Try it without AI (demo)** for a first look. |
| Our fit | A ring chart and a list: which requirements we meet, partly meet or do not offer, and which past answers were reused. |
| Competition | A radar chart for each competitor, a topic-by-topic grid, and talking points. Open a row to see the source behind a claim. |
| Customer | What the customer has said in public, what the RFP did not ask about, and what to handle with care. |
| Approve | Edit any answer, then both leads sign. Record won or lost later. Answers that need fixing are listed first. |
| Products | The catalogue. Upload a spec sheet to get suggested entries; you choose the status before anything is added. |
| Learn | Run the six-month review. See what the library knows, test results and the audit log. |

## Option B: Docker

```powershell
winget install Docker.DockerDesktop
docker compose up -d
docker compose exec ollama ollama pull qwen2.5:7b
```
Then open http://localhost:8765. Stop with `docker compose down`. If the model container cannot see your graphics card, delete the `deploy:` block in `compose.yaml`; it will run on the processor, more slowly. **Not yet run end to end.**

## Live web search (optional)

The demo reads a saved set of invented web pages. For real companies, start the open-source search engine and switch the mode:
```powershell
docker compose --profile web up -d
```
then set `mode = "searxng"` in `config.toml`. SearXNG must have its JSON output switched on in its own settings. Only a company name plus one approved topic word is ever sent (see PRIVACY_AND_GUARDRAILS.md). **Not yet run end to end.**

## Stop the agent

Set `enabled = false` in `config.toml`, or create an empty file called `STOP` in the project folder.

## Tests (no AI needed)

```powershell
python -m unittest discover tests -v
```
The tests work on a temporary copy, so they never touch your data.

## Check it works before you publish

Work down this list. It takes about 20 minutes.

1. **Tests.** In PowerShell, in the project folder, run `python -m unittest discover tests -v`. The last line should say `OK` after 18 tests.
2. **Demo without AI.** Double-click `start_windows.bat`. On the Start page press **Try it without AI (demo)**. Look at Our fit, Competition and Customer.
3. **Sign-off.** On the Approve page, sign as the technical lead with one name, then as the account lead with a different name. Press **We won**.
4. **Review.** On the Learn page press **Run the review now**. The library should go from 44 to 62 answers.
5. **The real AI run.** Close the black window. Delete the `outbox` and `output` folders so you start clean. Make sure Ollama is running, start the tool again and press **Prepare draft with AI**. Note how long it takes.
6. **Record the result.** Open `output\report.md` and copy the figures into the table in `docs\TESTING_AND_RESULTS.md`.
7. **Reset the demo data** so the published copy is clean: `python make_demo_data.py`.

If step 5 fails or the figures are poor, that is a real finding. Write it down honestly; do not publish the stand-in figures as if they were AI results.

## Publish to GitHub

1. On github.com, create a new **empty** repository called `rfp-response-agent` (no README, no licence; the project already has both).
2. Install Git if you have not: `winget install Git.Git`, then reopen PowerShell.
3. In the project folder:
```powershell
git init
git add .
git status
git commit -m "RFP Response Agent: first release"
git branch -M main
git remote add origin https://github.com/Hxlnd-Byte/rfp-response-agent.git
git push -u origin main
```
Read the list that `git status` prints before you commit. The `outbox` and `output` folders are left out automatically. Everything in `data` **is** uploaded, so check that `data\rfp` and `data\specs` hold only invented files. Never upload a real RFP, a real past bid or a real customer's name.

If you named the repository differently, change the address in the last two commands and in `README.md`.

## If something goes wrong

| What you see | What to do |
|---|---|
| "This tool needs Python 3.11 or newer" | Install Python 3.12 and reopen PowerShell |
| "Is Ollama running?" on the screen | Open the Ollama app, or choose the stand-in reader |
| The page does not open | Check the black window is still open; go to http://localhost:8765 by hand |
| "has already been approved" | Approved packs are never overwritten. Rename the RFP reference to draft again |
| Very slow | Run `ollama ps` and check it says GPU; try the other laptop or a smaller model |
