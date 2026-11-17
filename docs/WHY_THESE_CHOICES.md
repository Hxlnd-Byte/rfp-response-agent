# Why these choices

| Choice | Why | What I gave up |
|---|---|---|
| **Ollama with an open-source model (Qwen 2.5 7B)** | Runs on an 8 GB graphics card. RFPs and competitive notes never leave the machine. No fees per use. | A small model reads and writes less well than a large cloud model. That is why code checks its work. |
| **The fit comes from the catalogue, not the AI** | "Do we meet this?" is a commercial commitment. It should come from a list the company controls. | The catalogue has to be kept honest and current. |
| **Keyword search (BM25) for past answers** | Easy to explain, nothing to install, and it works well when RFP wording repeats. This is retrieval-augmented generation in its simplest form: find first, then write from what was found. | It can miss an answer that uses different words. Embedding search is the next step if that shows up in testing. |
| **A quote check on every web claim** | A claim about a competitor with no source is a liability. Code keeps a claim only if its quote is in the page. | A true point phrased differently from the page is dropped. I prefer that mistake to the opposite one. |
| **SearXNG for live search** | Open source and self-hosted, so you choose which search engines are asked and what is logged. | One more thing to run. Not needed for the demo. |
| **Two sign-offs** | The technical consultant knows whether it is true. The account lead knows whether it is right for this customer. | A little more time per bid. |
| **A review cycle, not retraining** | The agent improves because its library improves. That is cheap, visible and reversible. | It does not learn writing style on its own. |
| **A browser screen with no extra packages** | One double-click to start, nothing to install with pip. | Charts are drawn by the tool itself, so nothing is loaded from the internet. It has no sign-in, so it is for one team on one machine. |
| **Docker, with Kubernetes for scale** | Docker makes it start the same way anywhere. Kubernetes only earns its place for many teams. | See SCALING.md. |
