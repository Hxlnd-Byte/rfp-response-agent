#!/usr/bin/env python3
"""Builds the invented world used to test the agent. Everything here is fictional.

  python make_demo_data.py

Writes data/ (what the agent reads) and data/truth/ (the answer key the agent never reads in a real run).
"""
import json
import os
from pathlib import Path

ROOT = Path(os.environ.get("RFP_HOME") or Path(__file__).resolve().parent)
DATA = ROOT / "data"

VENDOR = "Vantora Software"
CUSTOMER = "Brackenfield Health Network"
COMPETITORS = ["Norvane Systems", "Kestrelline Cloud", "Ironvale Security"]

TAXONOMY = [
    ("THREAT_DETECTION", "Threat detection and response"), ("AI_EXPLAINABILITY", "Explanations for AI decisions"),
    ("DATA_RESIDENCY", "Data residency and sovereignty"), ("ITSM_INTEGRATION", "Service desk integration"),
    ("IDENTITY", "Sign-in and access control"), ("REPORTING_COMPLIANCE", "Compliance reporting"),
    ("AUTOMATION", "Automated patching and remediation"), ("DEPLOYMENT_ONPREM", "Running in the customer's own data centre"),
    ("SUPPORT_24X7", "Round-the-clock support"), ("IMPLEMENTATION", "Implementation and timeline"),
    ("TRAINING", "Training and skills"), ("MOBILE", "Mobile app"), ("MEDICAL_DEVICES", "Medical device monitoring"),
    ("PRICING_MODEL", "Pricing model"), ("REFERENCES", "Customer references"), ("BACKUP_RECOVERY", "Backup and recovery"),
    ("TOOL_CONSOLIDATION", "Fewer tools, one console"), ("SCALING_GROWTH", "Growth and new sites"),
]

# status: available -> STRONG, partial -> PARTIAL, roadmap / not_offered -> GAP.  The honest notes matter.
CATALOG = [
    ("C-01", "Vantora Sentry", "THREAT_DETECTION", "available", "Vantora Sentry detects and responds to threats across endpoints, servers and cloud workloads using behavioural models, and groups related alerts so an analyst can triage them in one view.", ""),
    ("C-02", "Vantora Sentry", "THREAT_DETECTION", "available", "Sentry detection models are updated monthly, and analyst feedback on each alert is used to reduce false alarms over time.", ""),
    ("C-03", "Vantora Sentry", "AI_EXPLAINABILITY", "available", "Every automated alert or block in Sentry comes with a plain-language explanation and the evidence behind it, which an analyst can review and overrule.", ""),
    ("C-04", "Vantora Sentry and Conductor", "DATA_RESIDENCY", "available", "All data and all AI processing can stay inside the customer's country, either in the customer's own data centre or in an in-country cloud region.", ""),
    ("C-05", "Vantora Conductor", "ITSM_INTEGRATION", "available", "Conductor creates and updates tickets in ServiceNow and Jira Service Management through supported connectors.", ""),
    ("C-06", "Vantora Conductor", "ITSM_INTEGRATION", "partial", "Other service desk and collaboration tools can be connected through an open interface.", "This needs integration work during the project; it is not a ready-made connector."),
    ("C-07", "Vantora Sentry and Conductor", "IDENTITY", "available", "Both products support single sign-on and role-based access control.", ""),
    ("C-08", "Vantora Sentry", "REPORTING_COMPLIANCE", "partial", "Sentry includes compliance report templates for common security standards.", "Templates specific to healthcare regulation are on the roadmap and are not available today."),
    ("C-09", "Vantora Conductor", "AUTOMATION", "available", "Conductor automates patching and remediation, and keeps a human approval step for any change marked high-risk.", ""),
    ("C-10", "Vantora Sentry and Conductor", "DEPLOYMENT_ONPREM", "available", "Both products, including their AI models, can run entirely in the customer's own data centre, with no connection to an outside service.", ""),
    ("C-11", "Vantora Assure", "SUPPORT_24X7", "available", "Vantora Assure provides support 24 hours a day, 7 days a week, with a 30 minute response target for critical incidents.", ""),
    ("C-12", "Vantora Launch", "IMPLEMENTATION", "available", "Vantora Launch is a fixed-scope implementation service that reaches full operation in 12 weeks, in three stages.", ""),
    ("C-13", "Vantora Academy", "TRAINING", "available", "Vantora Academy trains administrators and analysts, with hands-on labs and a certification, included in the subscription.", ""),
    ("C-14", "Vantora Conductor", "MOBILE", "roadmap", "A mobile app for approvals is planned.", "Today, on-call staff use the web console on a phone browser. There is no mobile app."),
    ("C-15", "Vantora Sentry", "MEDICAL_DEVICES", "not_offered", "Sentry does not discover or monitor medical devices itself.", "It can take in a feed from a specialist medical device tool chosen by the customer."),
    ("C-16", "Vantora Sentry and Conductor", "PRICING_MODEL", "available", "Pricing is a subscription per device, with no charges based on data volume.", ""),
    ("C-17", "Vantora Software", "REFERENCES", "partial", "Vantora can provide customer references in finance, government and education.", "Only one healthcare reference is available today."),
    ("C-18", "Vantora Sentry", "BACKUP_RECOVERY", "not_offered", "Vantora does not provide backup and recovery.", "Sentry and Conductor work alongside the customer's backup tool and can trigger its recovery steps."),
    ("C-19", "Vantora Sentry and Conductor", "TOOL_CONSOLIDATION", "available", "Sentry and Conductor share one console and one software agent, so security and management run from a single place.", ""),
    ("C-20", "Vantora Sentry and Conductor", "SCALING_GROWTH", "available", "Per-device pricing bands are agreed up front, so new sites can be added at a known price.", ""),
]

# (id, category, text, expected fit, expected capability)
REQUIREMENTS = [
    ("R-01", "THREAT_DETECTION", "The solution shall detect and respond to threats across endpoints, servers and cloud workloads, and help analysts triage alerts.", "STRONG", "C-01"),
    ("R-02", "AI_EXPLAINABILITY", "Every automated alert or block made by an AI model must come with a plain-language explanation that an analyst can review.", "STRONG", "C-03"),
    ("R-03", "DATA_RESIDENCY", "All patient-related and security data must be stored and processed inside the country. Describe where data and AI processing take place.", "STRONG", "C-04"),
    ("R-04", "DEPLOYMENT_ONPREM", "The vendor shall describe options to run the solution, including its AI models, in the customer's own data centre.", "STRONG", "C-10"),
    ("R-05", "ITSM_INTEGRATION", "The solution must create and update tickets in the customer's existing service desk tool, ServiceNow.", "STRONG", "C-05"),
    ("R-06", "ITSM_INTEGRATION", "Describe how other service desk and collaboration tools can be connected through an open interface.", "PARTIAL", "C-06"),
    ("R-07", "IDENTITY", "The solution shall support single sign-on and role-based access control.", "STRONG", "C-07"),
    ("R-08", "REPORTING_COMPLIANCE", "Provide compliance report templates, including templates suited to healthcare regulation.", "PARTIAL", "C-08"),
    ("R-09", "AUTOMATION", "Describe automated patching and remediation, and how human approval is kept for high-risk changes.", "STRONG", "C-09"),
    ("R-10", "MEDICAL_DEVICES", "The solution should discover and monitor connected medical devices.", "GAP", "C-15"),
    ("R-11", "MOBILE", "Provide a mobile app for on-call staff to review and approve actions.", "GAP", "C-14"),
    ("R-12", "BACKUP_RECOVERY", "Describe backup and recovery capabilities, including tested recovery times.", "GAP", "C-18"),
    ("R-13", "SUPPORT_24X7", "The vendor shall provide support 24 hours a day, 7 days a week, with stated response targets for critical incidents.", "STRONG", "C-11"),
    ("R-14", "IMPLEMENTATION", "Provide an implementation plan and timeline to reach full operation.", "STRONG", "C-12"),
    ("R-15", "TRAINING", "Describe the training provided for administrators and analysts.", "STRONG", "C-13"),
    ("R-16", "PRICING_MODEL", "Describe the pricing model and any charges based on data volume.", "STRONG", "C-16"),
    ("R-17", "REFERENCES", "Provide three customer references, at least two of them in healthcare.", "PARTIAL", "C-17"),
    ("R-18", "THREAT_DETECTION", "Describe how detection models are updated and how false alarms are reduced over time.", "STRONG", "C-02"),
]

BIDS = [
    ("B-2025-03", "Harrowgate Mutual Bank", "Finance", "2025-03-20", "won"),
    ("B-2025-06", "Port Sellwyn Authority", "Government", "2025-06-12", "lost"),
    ("B-2025-09", "Orchard Vale Hospitals", "Healthcare", "2025-09-04", "won"),
    ("B-2025-11", "Calderbrook Energy", "Energy", "2025-11-27", "lost"),
    ("B-2026-02", "Linmere University", "Education", "2026-02-18", "won"),
    ("B-2026-05", "Westmarch Logistics", "Logistics", "2026-05-08", "lost"),
]

# One reusable answer per category. {cust} sentences mention the old customer on purpose: the agent must not carry them over.
LIB = {
    "THREAT_DETECTION": ("How does the solution detect and respond to threats, and how are detection models kept up to date?", "Sentry watches endpoints, servers and cloud workloads and groups related alerts into a single case, so analysts triage one story and not a list. Models are updated monthly and learn from analyst feedback, which reduces false alarms over time. For {cust} we tuned the first models during the pilot."),
    "AI_EXPLAINABILITY": ("How are AI decisions explained to analysts?", "Each alert or block carries a plain-language explanation and the evidence behind it. An analyst can review the reasoning, overrule the decision, and that correction is recorded. {cust} asked for this in their review board and it was shown live."),
    "DATA_RESIDENCY": ("Where is data stored and processed?", "Data and AI processing stay inside the customer's country, in the customer's data centre or an in-country cloud region. No security data is sent to another country for analysis."),
    "ITSM_INTEGRATION": ("How does the solution integrate with the service desk?", "Conductor creates and updates tickets in ServiceNow and Jira Service Management through supported connectors. Other service desk tools can be connected through an open interface, which needs integration work in the project. {cust} used the ServiceNow connector from the first stage."),
    "IDENTITY": ("How are sign-in and access controlled?", "Both products support single sign-on and role-based access control, so each person sees only what their role allows."),
    "REPORTING_COMPLIANCE": ("What compliance reporting is provided?", "Sentry includes report templates for common security standards, and reports can be scheduled. Sector-specific templates are added over time; where a template is not yet available we say so and agree a plan."),
    "AUTOMATION": ("How are patching and remediation automated?", "Conductor patches and remediates automatically within rules the customer sets. Any change marked high-risk waits for a named person to approve it, and every action is logged."),
    "DEPLOYMENT_ONPREM": ("Can the solution run in our own data centre?", "Yes. Both products and their AI models can run entirely in the customer's data centre with no connection to an outside service. {cust} runs this way."),
    "SUPPORT_24X7": ("What support is provided?", "Vantora Assure provides support 24 hours a day, 7 days a week, with a 30 minute response target for critical incidents and a named service manager."),
    "IMPLEMENTATION": ("What is the implementation plan?", "Vantora Launch is a fixed-scope service that reaches full operation in 12 weeks in three stages: prepare, pilot and roll out. Each stage ends with a review the customer signs off."),
    "TRAINING": ("What training is provided?", "Vantora Academy trains administrators and analysts with hands-on labs and a certification. Training is included in the subscription, so new team members can be trained at no extra charge."),
    "MOBILE": ("Is there a mobile app?", "There is no mobile app today. On-call staff use the web console in a phone browser. A mobile app for approvals is planned, and we do not commit to a date in a proposal."),
    "MEDICAL_DEVICES": ("Does the solution monitor medical devices?", "Sentry does not discover or monitor medical devices itself. It can take in a feed from a specialist medical device tool, so those alerts appear alongside the rest. We told {cust} this plainly and proposed a partner."),
    "PRICING_MODEL": ("How is the solution priced?", "Pricing is a subscription per device. There are no charges based on data volume, so the cost does not rise when more data is collected."),
    "REFERENCES": ("Which customer references can you provide?", "We provide references in the customer's sector where we have them, and say where we do not. References are arranged as calls with people in a similar role."),
    "BACKUP_RECOVERY": ("What backup and recovery is provided?", "Vantora does not provide backup and recovery. Our products work alongside the customer's backup tool and can trigger its recovery steps as part of a response."),
    "TOOL_CONSOLIDATION": ("How does the solution reduce the number of tools?", "Sentry and Conductor share one console and one software agent, so security and management run from a single place and fewer separate tools are needed."),
    "SCALING_GROWTH": ("How does pricing work as we grow?", "Per-device pricing bands are agreed up front, so new sites can be added at a known price without a new negotiation."),
}
LIB_USE = {  # which bids answered which categories
    "B-2025-03": ["THREAT_DETECTION", "DATA_RESIDENCY", "IDENTITY", "REPORTING_COMPLIANCE", "SUPPORT_24X7", "PRICING_MODEL", "DEPLOYMENT_ONPREM", "AI_EXPLAINABILITY"],
    "B-2025-06": ["THREAT_DETECTION", "ITSM_INTEGRATION", "AUTOMATION", "IMPLEMENTATION", "REFERENCES", "MOBILE", "TRAINING"],
    "B-2025-09": ["THREAT_DETECTION", "AI_EXPLAINABILITY", "DATA_RESIDENCY", "MEDICAL_DEVICES", "ITSM_INTEGRATION", "SUPPORT_24X7", "TRAINING", "REFERENCES", "BACKUP_RECOVERY"],
    "B-2025-11": ["AUTOMATION", "DEPLOYMENT_ONPREM", "PRICING_MODEL", "IMPLEMENTATION", "BACKUP_RECOVERY", "IDENTITY"],
    "B-2026-02": ["AI_EXPLAINABILITY", "ITSM_INTEGRATION", "TRAINING", "PRICING_MODEL", "TOOL_CONSOLIDATION", "SCALING_GROWTH", "IMPLEMENTATION", "REPORTING_COMPLIANCE"],
    "B-2026-05": ["THREAT_DETECTION", "AUTOMATION", "SUPPORT_24X7", "MOBILE", "DATA_RESIDENCY", "TOOL_CONSOLIDATION"],
}

# Invented web pages. In a real run these come from a live search; here they are a saved snapshot.
PAGES = [
    ("W-01", "Norvane Systems", "vendor_page", "2026-08-12", "https://norvane.example/products/clinical-shield", "Norvane Clinical Shield",
     "Norvane Clinical Shield discovers and monitors connected medical devices out of the box, with profiles for more than 400 device types. The Norvane mobile app lets on-call staff approve actions from their phone. Norvane serves more than 60 hospital groups."),
    ("W-02", "Norvane Systems", "news", "2026-06-03", "https://techledger.example/norvane-analysis-regions", "Norvane confirms where its AI analysis runs",
     "Norvane confirmed that its AI analysis service runs in two shared cloud regions, and that customers elsewhere have their security data processed outside their own country. An in-country option is planned but has no date."),
    ("W-03", "Norvane Systems", "review", "2026-09-20", "https://peerbench.example/reviews/norvane", "Norvane: what users say",
     "Analysts told us the alerts arrive with a score but no reasoning. 'It is a black box,' said one security lead. Several reviewers also complained about charges based on data volume that were hard to predict."),
    ("W-04", "Kestrelline Cloud", "vendor_page", "2026-10-01", "https://kestrelline.example/pricing", "Kestrelline pricing and plans",
     "Kestrelline is cloud-only by design. There is nothing to install in your data centre. Plans start at a low flat fee per user, and most customers are live within four weeks. Support is available during business hours, Monday to Friday."),
    ("W-05", "Kestrelline Cloud", "news", "2026-07-18", "https://techledger.example/kestrelline-outage", "Kestrelline dashboards down for most of a day",
     "Kestrelline customers lost access to their dashboards for nine hours on Tuesday after a failed update. The company apologised and promised a review."),
    ("W-06", "Kestrelline Cloud", "news", "2026-05-22", "https://techledger.example/kestrelline-data-location", "Where does Kestrelline keep your data?",
     "Asked about data location, Kestrelline said it stores customer data in its global cloud and does not offer a choice of country."),
    ("W-07", "Ironvale Security", "vendor_page", "2026-09-05", "https://ironvale.example/platform", "The Ironvale platform",
     "Ironvale's detection engine is rated highly by independent testers and is tuned by a dedicated research team. Ironvale ships ready-made compliance report templates for healthcare regulators. Ironvale can be deployed in the customer's own data centre."),
    ("W-08", "Ironvale Security", "review", "2026-08-28", "https://peerbench.example/reviews/ironvale", "Ironvale: what users say",
     "Ironvale is a security product only. It has no patching or remediation of its own, and it does not open tickets in a service desk without custom scripting. Training is sold separately at a daily rate."),
    ("W-09", CUSTOMER, "press_release", "2026-09-15", "https://brackenfield.example/news/digital-strategy", "Brackenfield publishes three-year digital strategy",
     "Brackenfield Health Network today published its three-year digital strategy. 'Patient data stays in this country, and that is not negotiable,' said the Chief Information Officer. The strategy also commits to reducing the number of security and management tools from fourteen to no more than five."),
    ("W-10", CUSTOMER, "conference_talk", "2026-10-08", "https://healthtechforum.example/sessions/brackenfield-cio", "Health Tech Forum: running security with a small team",
     "Speaking at the Health Tech Forum, Brackenfield's Chief Information Officer said the security team has six people covering every site. 'I cannot hire my way out of this. And I will not buy another black box that my analysts cannot question,' she said."),
    ("W-11", CUSTOMER, "annual_report", "2026-04-30", "https://brackenfield.example/reports/annual-2025", "Brackenfield Health Network annual report",
     "The Network will open two new clinics in 2027. The Board has asked every department to hold operating costs flat while the Network grows."),
    ("W-12", CUSTOMER, "job_advert", "2026-10-20", "https://brackenfield.example/careers/servicenow-administrator", "Careers: ServiceNow administrator",
     "Brackenfield Health Network is hiring a ServiceNow administrator to run its service desk platform across all sites."),
    ("W-13", CUSTOMER, "news", "2026-03-11", "https://regionalhealthnews.example/brackenfield-supplier-incident", "Brackenfield reviews recovery plans after supplier incident",
     "After a ransomware incident at one of its suppliers last year, Brackenfield's Board asked for proof that critical systems can be recovered within four hours."),
]

# Answer key: (entity, category, stance, exact quote, page)
CLAIMS = [
    ("Norvane Systems", "MEDICAL_DEVICES", "strength", "discovers and monitors connected medical devices out of the box", "W-01"),
    ("Norvane Systems", "MOBILE", "strength", "mobile app lets on-call staff approve actions from their phone", "W-01"),
    ("Norvane Systems", "REFERENCES", "strength", "serves more than 60 hospital groups", "W-01"),
    ("Norvane Systems", "DATA_RESIDENCY", "weakness", "customers elsewhere have their security data processed outside their own country", "W-02"),
    ("Norvane Systems", "AI_EXPLAINABILITY", "weakness", "alerts arrive with a score but no reasoning", "W-03"),
    ("Norvane Systems", "PRICING_MODEL", "weakness", "charges based on data volume that were hard to predict", "W-03"),
    ("Kestrelline Cloud", "DEPLOYMENT_ONPREM", "weakness", "cloud-only by design", "W-04"),
    ("Kestrelline Cloud", "PRICING_MODEL", "strength", "Plans start at a low flat fee per user", "W-04"),
    ("Kestrelline Cloud", "IMPLEMENTATION", "strength", "most customers are live within four weeks", "W-04"),
    ("Kestrelline Cloud", "SUPPORT_24X7", "weakness", "Support is available during business hours, Monday to Friday", "W-04"),
    ("Kestrelline Cloud", "SUPPORT_24X7", "weakness", "lost access to their dashboards for nine hours", "W-05"),
    ("Kestrelline Cloud", "DATA_RESIDENCY", "weakness", "does not offer a choice of country", "W-06"),
    ("Ironvale Security", "THREAT_DETECTION", "strength", "rated highly by independent testers", "W-07"),
    ("Ironvale Security", "REPORTING_COMPLIANCE", "strength", "ready-made compliance report templates for healthcare regulators", "W-07"),
    ("Ironvale Security", "DEPLOYMENT_ONPREM", "strength", "can be deployed in the customer's own data centre", "W-07"),
    ("Ironvale Security", "AUTOMATION", "weakness", "no patching or remediation of its own", "W-08"),
    ("Ironvale Security", "ITSM_INTEGRATION", "weakness", "does not open tickets in a service desk without custom scripting", "W-08"),
    ("Ironvale Security", "TRAINING", "weakness", "Training is sold separately at a daily rate", "W-08"),
]
# (category, exact quote, page, who said it - a role, never a personal name)
PRIORITIES = [
    ("DATA_RESIDENCY", "Patient data stays in this country, and that is not negotiable", "W-09", "Chief Information Officer"),
    ("TOOL_CONSOLIDATION", "reducing the number of security and management tools from fourteen to no more than five", "W-09", "Company strategy"),
    ("TRAINING", "I cannot hire my way out of this", "W-10", "Chief Information Officer"),
    ("AI_EXPLAINABILITY", "I will not buy another black box that my analysts cannot question", "W-10", "Chief Information Officer"),
    ("SCALING_GROWTH", "will open two new clinics in 2027", "W-11", "Annual report"),
    ("PRICING_MODEL", "hold operating costs flat while the Network grows", "W-11", "Board, in the annual report"),
    ("ITSM_INTEGRATION", "hiring a ServiceNow administrator", "W-12", "Job advert"),
    ("BACKUP_RECOVERY", "proof that critical systems can be recovered within four hours", "W-13", "Board, reported by the press"),
]


def w(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(obj, str):
        path.write_text(obj, encoding="utf-8")
    else:
        path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def main(quiet=False):
    w(DATA / "company.json", dict(vendor=VENDOR, competitors=COMPETITORS,
                                  products=sorted({c[1] for c in CATALOG})))
    w(DATA / "taxonomy.json", [dict(code=c, label=l) for c, l in TAXONOMY])
    w(DATA / "catalog.json", [dict(id=i, product=p, category=c, status=s, text=t, note=n) for i, p, c, s, t, n in CATALOG])
    answers, n = [], 0
    for bid, cust, ind, date, outcome in BIDS:
        for cat in LIB_USE[bid]:
            n += 1
            q, a = LIB[cat]
            answers.append(dict(id=f"L-{n:03d}", bid=bid, category=cat, question=q, answer=a.replace("{cust}", cust)))
    w(DATA / "library.json", dict(version=1, learned_packs=[],
                                  bids=[dict(bid=b, customer=c, industry=i, date=d, outcome=o) for b, c, i, d, o in BIDS], answers=answers))
    w(DATA / "web_snapshot.json", [dict(id=i, entity=e, kind=k, date=d, url=u, title=t, text=x) for i, e, k, d, u, t, x in PAGES])
    lines = ["REQUEST FOR PROPOSAL", "", "RFP reference: RFP-2026-014", f"Issued by: {CUSTOMER}", "Response due: 2026-12-18", "",
             "1. Background", "",
             f"{CUSTOMER} runs hospitals and clinics with about 2,100 staff. We are looking for a security and IT management solution to protect and run our systems.",
             "", "2. Requirements", "", "Vendors must answer every numbered requirement and say plainly where a requirement is not met.", ""]
    lines += [f"{rid} {text}\n" for rid, _, text, _, _ in REQUIREMENTS]
    lines += ["3. Submission", "", "Responses must be received by the due date. Late responses will not be considered."]
    w(DATA / "rfp" / "RFP-2026-014_Brackenfield.txt", "\n".join(lines) + "\n")
    w(DATA / "truth" / "truth.json", dict(
        requirements=[dict(id=i, category=c, fit=f, capability=cap) for i, c, _, f, cap in REQUIREMENTS],
        claims=[dict(entity=e, category=c, stance=s, quote=q, source=p) for e, c, s, q, p in CLAIMS],
        priorities=[dict(category=c, quote=q, source=p, role=r) for c, q, p, r in PRIORITIES]))
    if not quiet:
      print(f"Built invented data: {len(REQUIREMENTS)} requirements, {len(CATALOG)} catalogue entries, {len(answers)} library answers "
            f"from {len(BIDS)} past bids, {len(PAGES)} web pages, {len(CLAIMS)} competitor claims, {len(PRIORITIES)} customer statements.")


if __name__ == "__main__":
    main()
