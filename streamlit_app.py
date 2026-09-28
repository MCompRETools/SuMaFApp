"""
Sustainability Maturity Tool  (Streamlit)

Setup:   pip install "streamlit>=1.36" pandas
Run:     streamlit run app.py

Data is stored locally in ./data (one JSON file per project, evidence files
in ./data/evidence/<project>/<activity-id>/).
"""
import json
import re
from datetime import date
from math import ceil
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Sustainability Maturity Tool", page_icon="🌿", layout="wide")

DATA_DIR = Path("data")
PROJECTS_FILE = DATA_DIR / "projects.json"
PAGE_SIZE = 5
STATUSES = ["Not started", "In progress", "Completed"]
STATUS_DOT = {"Not started": "⚪", "In progress": "🟡", "Completed": "🟢"}
COLS = [0.7, 1.6, 2.6, 1.4, 1.7, 1.5, 0.5]
HEADERS = ["ID", "Indicators", "What is Expected?", "Date", "Evidence", "Status", ""]

LEVELS = {
    1: {
        "name": "Scope Definition",
        "desc": "Sustainability is recognized as a project concern, but practices are largely ad hoc. "
                "Sustainability objectives and dimensions are not yet systematically defined.",
        "tip": "Record the activities, discussions and documents that show early consideration "
               "of sustainability in your DevOps project.",
        "defaults": [
            ("Stakeholder Awareness of Sustainability Inclusion", "At project initiation, stakeholders communicate sustainability objectives with the client and team members. Such as ESG compliance at EU. They openly discuss what is possible and what not in order to comply with guidelines or standards."),
            ("Awareness of environmental, technical and social sustainability", "Team members take a mandatory course or training on sustainability concepts."),
            ("Awareness of energy or resource implications", "Team members discuss how DevOps activities such as builds, testing, deployments and infrastructure usage can have energy and resource implications"),
            ("Awareness of technical debt impact", "Team lead or Technical Architect provide guidance on how technical debt can affect maintainability, software longevity, development effort and long-term sustainability. Technical Debt induced byAI generated Codes and their propagation."),
            ("Awareness of developer well-being and burnout risks", "Manager openly communicate on how workload, excessive overtime, repetitive activities, cognitive load and other factors that may affect developer well-being and long-term productivity."),
            ("Sustainability objectives discussed during planning", "Sustainability objectives are explicitly discussed during project planning, including the relevant environmental, technical, and social concerns and their implications for project decisions."),
            ("Sustainability dimensions prioritized for the project", "Relevant sustainability dimensions (environmental, technical, social, and, where applicable, economic) are identified and recorded in project dashboard"),
            ("Initial identification of DevOps tools supporting sustainability assessment", "Teams actively reviews capability of each tool from their sustainability understanding"),
            ("Awareness of existing tool capabilities and limitations", "Team knowledge dissemination regarding different build or testing tools and their capabilities"),
        ],
    },
    2: {
        "name": "Sustainability Awareness",
        "desc": "Defined sustainability requirements and repeatable practices are embedded into CI/CD planning.",
        "tip": "Record how sustainability requirements shape your CI/CD planning and how the team shares knowledge.",
        "defaults": [
            ("Define sustainability requirements", "Wrote requirements the pipeline must meet (e.g. max build time, idle-runner policy)."),
            ("Knowledge-sharing workshop", "Ran a prioritisation exercise on competing features with the team."),
            ("Reuse CI/CD components", "Pipeline steps are called from a shared catalog instead of copied."),
            ("Add sustainability to CI/CD planning", "Sustainability check added to the pipeline planning template."),
        ],
    },
    3: {
        "name": "Measurement",
        "desc": "The pipeline systematically tracks qualitative and quantitative metrics across build, test and infrastructure phases.",
        "tip": "Record which metrics you collect, where they are stored and how often they are reviewed.",
        "defaults": [
            ("Track build metrics", "Build duration and compute minutes are logged per run."),
            ("Track test metrics", "Test runtime and flaky-test rate are recorded."),
            ("Track infrastructure usage", "Runner and environment utilisation is collected."),
            ("Publish a metrics dashboard", "Team dashboard shows trends over time."),
        ],
    },
    4: {
        "name": "Optimization",
        "desc": "Metric analytics are used to actively optimize resource usage and pipeline efficiency.",
        "tip": "Record the optimizations you made and the measured effect they had.",
        "defaults": [
            ("Analyse metrics for hotspots", "Identified the slowest and most resource-hungry pipeline stages."),
            ("Optimize resource usage", "Added caching, parallelism or right-sized runners."),
            ("Review efficiency gains", "Compared before/after metrics in a retrospective."),
        ],
    },
    5: {
        "name": "Autonomous Sustainability",
        "desc": "AI models and predictive analytics automatically recommend or execute pipeline optimizations.",
        "tip": "Record which recommendations or actions are automated and the guardrails around them.",
        "defaults": [
            ("Predictive analytics on pipeline data", "Model forecasts resource use per change."),
            ("Automated recommendations", "Pipeline suggests optimizations in pull requests."),
            ("Guarded automatic optimization", "Approved optimizations run automatically with rollback."),
        ],
    },
}

CSS = """
<style>
:root{--g:#1f7a4d;--gl:#e6f2ea;--gb:#cfe5d6;}
[data-testid="stSidebar"]{background:#f4f8f5;}
.brand{font-size:22px;font-weight:600;line-height:1.2;}
.brand span{font-size:13px;font-weight:400;color:#5b6b62;}
.avatar{width:40px;height:40px;border-radius:50%;background:#8a9a91;color:#fff;display:flex;
  align-items:center;justify-content:center;font-weight:600;margin-left:auto;}
.banner{display:flex;gap:20px;align-items:center;background:var(--gl);border:1px solid var(--gb);
  border-radius:12px;padding:20px 24px;margin-bottom:12px;}
.banner h2{margin:0 0 4px 0;padding:0;color:#14532d;}
.banner p{margin:0;color:#3d4a43;}
.badge{min-width:60px;height:60px;border-radius:50%;background:var(--g);color:#fff;font-size:28px;
  font-weight:600;display:flex;align-items:center;justify-content:center;}
.tip{background:#fff;border:1px solid var(--gb);border-radius:10px;padding:12px 16px;
  min-width:260px;max-width:340px;font-size:13px;color:#3d4a43;}
.hdr{font-weight:600;font-size:14px;color:#33413a;}
button[data-testid="stBaseButton-primary"]{background:var(--g);border-color:var(--g);}
</style>
"""


# ---------- storage ----------
def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "project"


def new_project_data():
    return {
        str(n): {
            "activities": [
                {"id": f"L{n}-{i:02d}", "title": t, "description": h,
                 "date": None, "status": "Not started", "evidence": []}
                for i, (t, h) in enumerate(lv["defaults"], 1)
            ],
            "notes": "",
            "complete": False,
        }
        for n, lv in LEVELS.items()
    }


def load_projects():
    if PROJECTS_FILE.exists():
        return json.loads(PROJECTS_FILE.read_text())
    return ["Example DevOps Project"]


def save_projects():
    PROJECTS_FILE.write_text(json.dumps(st.session_state.projects))


def load_project(name):
    path = DATA_DIR / f"{slug(name)}.json"
    return json.loads(path.read_text()) if path.exists() else new_project_data()


def save_project(name=None):
    ss = st.session_state
    name = name or ss.loaded_project
    (DATA_DIR / f"{slug(name)}.json").write_text(json.dumps(ss.data, indent=2))


def switch_project():
    save_project(st.session_state.loaded_project)  # persist the project we are leaving


def init_state():
    DATA_DIR.mkdir(exist_ok=True)
    ss = st.session_state
    ss.setdefault("projects", load_projects())
    ss.setdefault("project", ss.projects[0])
    ss.setdefault("page", "dashboard")
    ss.setdefault("user", "JD")
    if ss.get("loaded_project") != ss.project:
        ss.data = load_project(ss.project)
        ss.loaded_project = ss.project


# ---------- model helpers ----------
def level(n):
    return st.session_state.data[str(n)]


def counts(n):
    acts = level(n)["activities"]
    return sum(a["status"] == "Completed" for a in acts), len(acts)


def level_status(n):
    done, total = counts(n)
    if level(n)["complete"]:
        return "Complete"
    return "In progress" if any(a["status"] != "Not started" for a in level(n)["activities"]) else "Not started"


def achieved_level():
    reached = 0
    for n in LEVELS:
        if level(n)["complete"]:
            reached = n
        else:
            break
    return reached


def go(page):
    st.session_state.page = page


def set_pg(key, value):
    st.session_state[key] = value


def add_activity(n):
    ss = st.session_state
    title = ss.get(f"new-title-{n}", "").strip()
    if not title:
        ss[f"add-error-{n}"] = True
        return
    acts = level(n)["activities"]
    nxt = max([int(a["id"].split("-")[1]) for a in acts] or [0]) + 1
    acts.append({"id": f"L{n}-{nxt:02d}", "title": title,
                 "description": ss.get(f"new-desc-{n}", "").strip(),
                 "date": None, "status": "Not started", "evidence": []})
    ss[f"pg-{n}"] = (len(acts) - 1) // PAGE_SIZE
    ss[f"new-title-{n}"] = ""
    ss[f"new-desc-{n}"] = ""
    ss[f"add-error-{n}"] = False


def delete_activity(n, act_id):
    level(n)["activities"] = [a for a in level(n)["activities"] if a["id"] != act_id]


def evidence_path(act_id, filename):
    folder = DATA_DIR / "evidence" / slug(st.session_state.project) / act_id
    folder.mkdir(parents=True, exist_ok=True)
    return folder / Path(filename).name


# ---------- UI pieces ----------
def header():
    ss = st.session_state
    c1, c2, c3 = st.columns([5, 3, 0.6], vertical_alignment="center")
    c1.markdown("<div class='brand'>🌿 Sustainability Maturity Tool<br>"
                "<span>Measure • Improve • Build a Greener DevOps</span></div>", unsafe_allow_html=True)
    c2.selectbox("Project", ss.projects, key="project", on_change=switch_project)
    c3.markdown(f"<div class='avatar'>{ss.user}</div>", unsafe_allow_html=True)
    st.divider()


def sidebar():
    page = st.session_state.page
    nav = [("dashboard", "🏠  Dashboard"), ("assessment", "📊  Maturity Assessment")]
    nav += [(f"level-{n}", f"{n}  ·  Level {n} – {lv['name']}") for n, lv in LEVELS.items()]
    nav += [("reports", "📄  Reports"), ("settings", "⚙️  Settings")]
    with st.sidebar:
        for key, label in nav:
            if key == "reports":
                st.divider()
            st.button(label, key=f"nav-{key}", use_container_width=True, on_click=go, args=(key,),
                      type="primary" if page == key else "secondary")
        st.divider()
        st.caption("🌿 Smaller footprints. Stronger software.")


def activity_row(n, a):
    k = f"{slug(st.session_state.project)}-{a['id']}"
    c = st.columns(COLS, vertical_alignment="center")
    c[0].markdown(f"**{a['id']}**")
    c[1].markdown(a["title"])
    c[2].caption(a.get("description") or a.get("hint", ""))
    picked = c[3].date_input("Date", value=date.fromisoformat(a["date"]) if a["date"] else None,
                             format="YYYY-MM-DD", key=f"{k}-date", label_visibility="collapsed")
    a["date"] = picked.isoformat() if picked else None
    files = c[4].file_uploader("Evidence", accept_multiple_files=True, key=f"{k}-files",
                               label_visibility="collapsed")
    for f in files or []:
        target = evidence_path(a["id"], f.name)
        if not target.exists():
            target.write_bytes(f.getbuffer())
        if target.name not in a["evidence"]:
            a["evidence"].append(target.name)
    if a["evidence"]:
        c[4].caption(f"📎 {len(a['evidence'])} file(s) saved")
    a["status"] = c[5].selectbox("Status", STATUSES, index=STATUSES.index(a["status"]),
                                 format_func=lambda s: f"{STATUS_DOT[s]} {s}", key=f"{k}-status",
                                 label_visibility="collapsed")
    #with c[6].popover("⋯"):
        #st.button("Delete activity", key=f"{k}-del", on_click=delete_activity, args=(n, a["id"]))
    st.divider()


def activities_tab(n):
    acts = level(n)["activities"]
    left, right = st.columns([5, 1], vertical_alignment="center")
    left.subheader(f"Level {n} Activities")
    left.caption(f"Record the activities your team is performing related to Level {n}.")
    with right.popover("＋ Add Activity", use_container_width=True):
        st.text_input("Activity", key=f"new-title-{n}", placeholder="e.g. Sustainability kick-off")
        st.text_area("Description", key=f"new-desc-{n}", height=80,
                     placeholder="What the team is expected to do or show")
        if st.session_state.get(f"add-error-{n}"):
            st.error("Enter an activity name first.")
        st.button("Add", key=f"add-{n}", type="primary", on_click=add_activity, args=(n,))

    for col, h in zip(st.columns(COLS), HEADERS):
        col.markdown(f"<div class='hdr'>{h}</div>", unsafe_allow_html=True)
    st.divider()

    pg_key = f"pg-{n}"
    pages = max(1, ceil(len(acts) / PAGE_SIZE))
    pg = min(st.session_state.get(pg_key, 0), pages - 1)
    for a in acts[pg * PAGE_SIZE:(pg + 1) * PAGE_SIZE]:
        activity_row(n, a)

    if not acts:
        st.info("No activities yet. Select “Add Activity” to record the first one.")

    lo, hi = pg * PAGE_SIZE + 1, min((pg + 1) * PAGE_SIZE, len(acts))
    _, info, prev, nxt = st.columns([6, 1.2, 0.5, 0.5], vertical_alignment="center")
    info.caption(f"{lo if acts else 0}–{hi} of {len(acts)}")
    prev.button("‹", key=f"prev-{n}", disabled=pg == 0, on_click=set_pg, args=(pg_key, pg - 1))
    nxt.button("›", key=f"next-{n}", disabled=pg >= pages - 1, on_click=set_pg, args=(pg_key, pg + 1))


def evidence_tab(n):
    rows = [a for a in level(n)["activities"] if a["evidence"]]
    if not rows:
        st.info("No evidence uploaded yet. Add files from the Activities tab.")
    for a in rows:
        st.markdown(f"**{a['id']} · {a['title']}**")
        for name in a["evidence"]:
            path = evidence_path(a["id"], name)
            if path.exists():
                st.download_button(f"📎 {name}", path.read_bytes(), file_name=name, key=f"dl-{a['id']}-{name}")


def notes_tab(n):
    lv = level(n)
    lv["notes"] = st.text_area("Notes", lv["notes"], height=220, key=f"notes-{n}",
                               placeholder="Context, open questions, decisions…")


def progress_tab(n):
    done, total = counts(n)
    acts = level(n)["activities"]
    m1, m2, m3 = st.columns(3)
    m1.metric("Completed", f"{done} / {total}")
    m2.metric("In progress", sum(a["status"] == "In progress" for a in acts))
    m3.metric("Not started", sum(a["status"] == "Not started" for a in acts))
    st.progress(done / total if total else 0.0)
    df = pd.DataFrame({"Activities": [sum(a["status"] == s for a in acts) for s in STATUSES]}, index=STATUSES)
    st.bar_chart(df, color="#1f7a4d")


def footer(n):
    lv = level(n)
    done, total = counts(n)
    st.divider()
    back, _, save, complete = st.columns([1.3, 4, 1, 1.6])
    back.button("←  Back to Overview", use_container_width=True, on_click=go, args=("assessment",))
    if save.button("Save Draft", use_container_width=True):
        save_project()
        st.toast("Draft saved", icon="💾")
    if lv["complete"]:
        if complete.button("Reopen Level", use_container_width=True):
            lv["complete"] = False
            save_project()
            st.rerun()
    elif complete.button(f"Mark Level {n} as Complete", type="primary", use_container_width=True):
        if total and done == total:
            lv["complete"] = True
            save_project()
            st.toast(f"Level {n} marked complete", icon="🎉")
            st.rerun()
        else:
            st.warning(f"{total - done} activit{'y is' if total - done == 1 else 'ies are'} not completed yet. "
                       "Set every activity to Completed first.")


def level_page(n):
    lv = LEVELS[n]
    st.markdown(f"<div class='banner'><div class='badge'>{n}</div>"
                f"<div style='flex:1'><h2>Level {n} – {lv['name']}</h2><p>{lv['desc']}</p></div>"
                f"<div class='tip'><b>💡 Tip</b><br>{lv['tip']}</div></div>", unsafe_allow_html=True)
    if level(n)["complete"]:
        st.success(f"Level {n} is marked complete.")
    t_act, t_ev, t_notes, t_prog = st.tabs(["Activities", "Evidence", "Notes", "Progress"])
    with t_act:
        activities_tab(n)
    with t_ev:
        evidence_tab(n)
    with t_notes:
        notes_tab(n)
    with t_prog:
        progress_tab(n)
    footer(n)


def dashboard_page():
    st.subheader("Dashboard")
    reached = achieved_level()
    all_done = sum(counts(n)[0] for n in LEVELS)
    all_total = sum(counts(n)[1] for n in LEVELS)
    m1, m2, m3 = st.columns(3)
    m1.metric("Current maturity level", f"Level {reached}" if reached else "Not yet at Level 1")
    m2.metric("Activities completed", f"{all_done} / {all_total}")
    m3.metric("Next level", f"Level {reached + 1}" if reached < len(LEVELS) else "All levels done")
    st.progress(all_done / all_total if all_total else 0.0)
    for col, (n, lv) in zip(st.columns(len(LEVELS)), LEVELS.items()):
        done, total = counts(n)
        with col.container(border=True):
            st.markdown(f"**Level {n}**")
            st.caption(lv["name"])
            st.progress(done / total if total else 0.0)
            st.caption(f"{done}/{total} · {level_status(n)}")
            st.button("Open", key=f"open-{n}", use_container_width=True, on_click=go, args=(f"level-{n}",))


def assessment_page():
    st.subheader("Maturity assessment")
    reached = achieved_level()
    st.info(f"Current maturity level: **Level {reached}**" if reached
            else "Level 1 is not complete yet. Start with the Level 1 activities.")
    rows = []
    for n, lv in LEVELS.items():
        done, total = counts(n)
        rows.append({"Level": n, "Name": lv["name"], "Completed": f"{done}/{total}",
                     "Progress %": round(100 * done / total) if total else 0, "Status": level_status(n)})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True,
                 column_config={"Progress %": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d%%")})
    if reached < len(LEVELS):
        st.button(f"Continue with Level {reached + 1}", type="primary", on_click=go, args=(f"level-{reached + 1}",))


def reports_page():
    st.subheader("Reports")
    rows = [{"level": n, "level_name": LEVELS[n]["name"], "level_complete": level(n)["complete"],
             "id": a["id"], "activity": a["title"], "description": a.get("description") or a.get("hint", ""), "date": a["date"],
             "status": a["status"], "evidence_files": "; ".join(a["evidence"])}
            for n in LEVELS for a in level(n)["activities"]]
    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True, use_container_width=True)
    c1, c2, _ = st.columns([1, 1, 4])
    stem = slug(st.session_state.project)
    c1.download_button("Download CSV", df.to_csv(index=False), f"{stem}-assessment.csv", "text/csv")
    c2.download_button("Download JSON", json.dumps(st.session_state.data, indent=2),
                       f"{stem}-assessment.json", "application/json")


def settings_page():
    ss = st.session_state
    st.subheader("Settings")
    ss.user = st.text_input("Your initials", ss.user, max_chars=3).upper()
    st.markdown("**Add a project**")
    name = st.text_input("Project name", key="new-project", label_visibility="collapsed",
                         placeholder="e.g. Payments platform")
    if st.button("Add project"):
        if not name.strip():
            st.error("Enter a project name first.")
        elif name.strip() in ss.projects:
            st.error("A project with this name already exists.")
        else:
            ss.projects.append(name.strip())
            save_projects()
            st.success(f"Added “{name.strip()}”. Pick it from the project menu at the top.")


# ---------- main ----------
init_state()
st.markdown(CSS, unsafe_allow_html=True)
header()
sidebar()

page = st.session_state.page
if page.startswith("level-"):
    level_page(int(page.split("-")[1]))
elif page == "assessment":
    assessment_page()
elif page == "reports":
    reports_page()
elif page == "settings":
    settings_page()
else:
    dashboard_page()
