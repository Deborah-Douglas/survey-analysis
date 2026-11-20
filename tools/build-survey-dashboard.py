import csv
import json
import re
import sys
from pathlib import Path

with open(sys.argv[1], encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    wording = next(reader)
    next(reader)
    records = list(reader)

eligible = [r for r in records if r["Status"] != "Survey Preview" and r["Q2"] == "Yes"]

def direct(r):
    return r["Q4"] in ("Regularly - government is my primary focus", "Most of it")

cohorts = [
    ("all", "All respondents", "", lambda r: True),
    ("direct", "Government is primary or most of work", "Government coverage", direct),
    ("less", "Government is less central to work", "Government coverage", lambda r: bool(r["Q4"]) and not direct(r)),
    ("reporter", "Reporters / correspondents", "Primary role", lambda r: r["Q8"] == "Reporter / correspondent"),
    ("editor", "Editors / managers / executive leaders", "Primary role", lambda r: r["Q8"].startswith(("Editor /", "Executive"))),
    ("early", "10 years or less", "Experience", lambda r: r["Q7"] in ("Under 5 years", "5-10 years")),
    ("experienced", "11 years or more", "Experience", lambda r: r["Q7"] in ("11-20 years", "Over 20 years")),
    ("local", "Local, county, regional or state", "Government level most relevant", lambda r: r["Q5"] in ("Local / municipal", "County or regional", "State")),
    ("federal", "Federal", "Government level most relevant", lambda r: r["Q5"] == "Federal"),
]

charts = {}
def add(id, title, note, specs, sort=False, detail=None):
    out = {"title": title, "note": note, "sort": sort, "detail": detail or " / ".join(dict.fromkeys(wording[k].split(" - ")[0] for _, k, _, _ in specs)), "rows": []}
    for label, field, include, match in specs:
        row = {"label": label, "values": {}}
        for cid, _, _, select in cohorts:
            vals = [r[field].strip() for r in eligible if select(r) and include(r[field].strip())]
            n, base = sum(match(v) for v in vals), len(vals)
            if cid != "all" and (base < 30 or n < 5 or base - n < 5):
                n = None
            row["values"][cid] = [n, base]
        out["rows"].append(row)
    charts[id] = out

def match_options(field, pairs):
    # Anchored matching against unique option prefixes preserves internal commas.
    return [(label, field, bool, lambda v, start=start: re.search(r"(?:^|,)" + re.escape(start), v) is not None) for label, start in pairs]

def exact(label, field, *choices, skip=()):
    return (label, field, lambda v: bool(v) and v not in skip, lambda v: v in choices)

def matrix(prefix, names, *choices, skip=()):
    return [exact(name, f"{prefix}_{i}", *choices, skip=skip) for i, name in enumerate(names, 1)]

add("federal", "Federal actions with local effects", "Share who reported a material effect since January 2025. Multiple selections allowed.", match_options("Q9", [
    ("Federal funding or grants", "Threats to or changes in federal funding"), ("Immigration enforcement", "Immigration enforcement"),
    ("Health, environmental, labor or benefits policy", "Health, environmental"), ("Civil rights or education policy", "Civil rights or education"),
    ("Federal–state or federal–local legal conflict", "Federal-state or federal-local"), ("Restrictions on data, records or press access", "Restrictions on government data"),
    ("Policing, protest or public safety enforcement", "Policing, protest"), ("Election administration or voting", "Election administration"), ("Other", "Other [Write-in]"), ("None of these / not sure", "None of these")]), True)
add("frequency", "Recurring reporting assignments", "Often or very often in the past 12 months. Excludes N/A.", matrix("Q10", [
    "Federal immigration enforcement", "Conflict between federal and other institutions", "Federal policy effects on vulnerable communities",
    "Unclear or changing local effects of federal actions", "Efforts to discredit local journalism", "Reduced access to government information or sites"], "Often", "Very Often", skip=("N/A",)), True)
add("connection", "Making the policy connection explicit", "How often respondents link a development on their beat to a government policy decision. Excludes not applicable.", [
    exact(v, "Q14", v, skip=("Not applicable to my beat",))
    for v in ("In most cases", "Often", "Sometimes", "Rarely", "Never")])
add("pressure", "Direct reporting pressures", "Experiences in the past 12 months. Multiple selections allowed.", match_options("Q11", [
    ("Sources newly declined to go on the record", "Sources (clinicians"), ("Officials denied, delayed or restricted access", "An official denied"),
    ("Newsroom discussions about a story being “too political”", "Internal newsroom discussions"), ("Officials challenged legitimacy of reporting", "Officials or agencies publicly challenged"),
    ("Online harassment, doxxing, threats or abuse", "Online harassment"), ("Pressure to narrow, delay, soften or drop a story", "Pressure from supervisors"),
    ("Concern personal identity increased risk", "Concerns that your personal identity"), ("In-person intimidation, interference or surveillance", "In-person intimidation"),
    ("Subpoenas, legal threats or source pressure", "Subpoenas"), ("Detention, threat of detention or equipment demands", "Detention,"), ("None of the above", "None of the above"), ("Prefer not to answer", "Prefer not to answer")]))
add("overlap", "When access problems overlap", "Respondents who selected both, either, or neither. Excludes “Prefer not to answer.”", [
    (label, "Q11", lambda v: bool(v) and v != "Prefer not to answer", fn) for label, fn in [
        ("Both access problems", lambda v: "Sources (clinicians" in v and "An official denied" in v),
        ("Only sources going off the record", lambda v: "Sources (clinicians" in v and "An official denied" not in v),
        ("Only an official access restriction", lambda v: "Sources (clinicians" not in v and "An official denied" in v),
        ("Neither access problem", lambda v: "Sources (clinicians" not in v and "An official denied" not in v)]])
add("politicized", "When routine stories become contested", "Whether a previously routine or nonpolitical story became politically contested.", [
    exact(v, "Q15", v) for v in ("Yes, substantially", "Yes, somewhat", "No", "Unsure")])
add("editorial", "Editorial judgment and support", "Share who agreed or strongly agreed with each statement.", matrix("Q16", [
    "Newsroom discussed policy disputes vs. democratic threats", "Confident explaining enforcement without repeating official framing uncritically",
    "Worry “both-sides” reporting can obscure asymmetry", "Adequate support to call claims false and add context",
    "Worry terms such as “authoritarian” could invite retaliation", "Changed story choices due to safety, legal, access or financial concerns"], "Agree", "Strongly Agree"))
add("contested", "Handling contested claims", "Default approach to contested claims about elections, courts, agency authority or science.", [
    exact(label, "Q18", full) for label, full in [
        ("Depends on the story", "Depends entirely on the story"), ("Adjudicate factual disputes", "Adjudicating factual disputes explicitly within the story"),
        ("Present competing accounts", "Presenting competing accounts and letting the audience judge"), ("Explain the procedure or process", "Explaining the underlying procedure or process rather than highlighting the dispute"),
        ("Cover practical effects on people", "Covering practical effects on people and avoiding political framing disputes"), ("Defer to expert or institutional consensus", "Deferring to expert or institutional consensus")]])
add("change", "How much should coverage change?", "The statement closest to each respondent’s overall view.", [
    exact(label, "Q19", full) for label, full in [
        ("Substantial change is needed", "Journalism as a whole needs substantial change in how it covers this period; standard approaches are inadequate."),
        ("Modest adjustments are needed", "Practice needs modest adjustments in specific areas."),
        ("Existing standards need consistent application", "Existing standards are sound; the challenge is applying them consistently."),
        ("Unsure", "Unsure."), ("Some coverage has overcorrected", "Some coverage has overcorrected - treating ordinary politics as exceptional damages credibility.")]])
add("ranking", "What limits coverage most", "Share who ranked each constraint first. See Methods for the order sensitivity check.", matrix("Q21", [
    "Staffing", "Time", "Legal risk", "Access to sources or information", "Audience trust", "Internal editorial disagreement", "Funding", "Personal safety", "Uncertainty about beat scope"], "1"), True)
add("safety", "Safeguards outlets provide", "Share answering yes. No and unsure remain in the denominator.", matrix("Q22", [
    "Pre-assignment risk assessment", "Written field-safety or detention protocols", "Digital-security or anti-doxxing support",
    "Encrypted communication or secure document tools", "Access to newsroom counsel", "Confidential source-protection support", "Emergency contacts and check-ins",
    "Mental health, trauma or peer support", "Clear escalation for harassment and threats", "Personal protective gear"], "Yes"), True)
add("familiar", "Familiarity with existing resources", "Share familiar with or having used a resource. Multiple selections allowed.", match_options("Q23", [
    ("State press associations or local media-law groups", "State press associations"), ("Committee to Protect Journalists", "Committee to Protect"),
    ("Reporters Committee for Freedom of the Press", "Reporters Committee"), ("Reporters Without Borders", "Reporters Without Borders"),
    ("International Women’s Media Foundation", "International Women's"), ("Global Investigative Journalism Network", "Global Investigative"),
    ("Protect Democracy’s Authoritarian Playbook", "Protect Democracy"), ("U.S. Journalist Assistance Network", "U.S. Journalist"),
    ("Other", "Other [Write-in]"), ("None of these", "None of these")]), True)
add("resources", "Most requested resources", "Respondents were asked to choose three. All nonblank responses are included.", match_options("Q24", [
    ("Public-records, FOIA and data-access help", "Public-records, FOIA"), ("Grant funding or staffing", "Direct grant funding"),
    ("Cross-newsroom collaboration", "Cross-newsroom"), ("Editorial guidance on language and framing", "Editorial guidance"),
    ("Fast access to media-law counsel", "Fast access"), ("Unsealing court records", "Unsealing court records"),
    ("Digital security and anti-doxxing", "Digital-security"), ("Immigration-law and detention expertise", "Immigration-law"),
    ("Community engagement and trauma-informed sourcing", "Community engagement"), ("Mental health and peer support", "Mental health"),
    ("Physical field-safety protocols", "Physical field safety"), ("Prepublication legal review", "Prepublication"),
    ("Subpoena defense and source protection", "Subpoena defense")]), True)
add("tenure", "Years in journalism", "Experience among eligible respondents.", [exact(name, "Q7", name) for name in ("Under 5 years", "5-10 years", "11-20 years", "Over 20 years")])
add("outlet", "Primary outlet type", "Respondents selected one primary outlet type.", [
    exact("Other" if name == "Other [Write-in]" else name, "Q6", name) for name in dict.fromkeys(r["Q6"] for r in eligible) if name], True)
add("kpis", "", "", [
    exact("Routine stories became contested", "Q15", "Yes, somewhat", "Yes, substantially"),
    ("Staffing or time ranked first", "Q21_1", bool, lambda _: False)])
for cid, _, _, select in cohorts:
    ranked = [r for r in eligible if select(r) and r["Q21_1"]]
    n = sum(r["Q21_1"] == "1" or r["Q21_2"] == "1" for r in ranked)
    b = len(ranked)
    charts["kpis"]["rows"][1]["values"][cid] = [n if cid == "all" or (b >= 30 and n >= 5 and b - n >= 5) else None, b]

assert len(eligible) == 421 and sum(r["Finished"] == "True" for r in eligible) == 298
assert [r["values"]["all"] for r in charts["resources"]["rows"]] == [[n,280] for n in [157,146,91,87,64,67,46,43,29,24,18,15,7]]
assert [r["values"]["all"] for r in charts["pressure"]["rows"]] == [[n,352] for n in [200,175,109,96,85,70,67,34,34,6,42,6]]
assert [r["values"]["all"] for r in charts["federal"]["rows"]] == [[n,358] for n in [253,218,184,170,170,151,135,111,30,24]]
assert [r["values"]["all"] for r in charts["familiar"]["rows"]] == [[n,300] for n in [159,139,136,89,69,42,12,8,13,52]]
assert [r["values"]["all"] for r in charts["kpis"]["rows"]] == [[199,321],[222,302]]
assert [r["values"]["all"] for r in charts["connection"]["rows"]] == [[n,294] for n in [183,87,20,3,1]]

bundle = {"cohorts": [{"id": cid, "name": label, "group": group, "size": sum(select(r) for r in eligible)} for cid, label, group, select in cohorts], "charts": charts}
Path(sys.argv[2]).write_text("window.SURVEY = " + json.dumps(bundle, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
