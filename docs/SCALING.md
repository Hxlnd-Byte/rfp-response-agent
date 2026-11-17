# Scaling: from one workstation to a larger team

| Stage | What it is | When it fits |
|---|---|---|
| 1. One workstation | Python and Ollama installed directly, started with a double-click | One presales team, a pilot |
| 2. Docker Compose | The agent, the model and (optionally) search as containers on one server | A shared team server; handing it to IT |
| 3. Kubernetes | The same containers across several machines | Many account teams in several regions sharing one service |

**Stage 2** is in the setup guide. **Stage 3** has a starting file in `deploy/k8s/app.yaml`. Neither has been run end to end; the files were checked for valid syntax only.

Before stage 3 the tool would also need sign-in and per-team access, a proper database in place of files, and a shared model server. Those are real work and are not built.

## Another PoV

An RFP tool is used by a handful of people a few times a week. One server is plenty for most companies. Kubernetes makes sense when IT already runs everything on it, or when many regions need the same service. Otherwise it is decoration.

## Sovereignty

At every stage the model and the data stay in your own environment. The only outside traffic is the search phrases described in PRIVACY_AND_GUARDRAILS.md, and that can be switched off.
