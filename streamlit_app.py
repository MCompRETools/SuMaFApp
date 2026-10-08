import json, re, uuid
from pathlib import Path
from datetime import date
from math import ceil
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title='Sustainability Maturity Tool', page_icon='🌿', layout='wide')

st.session_state.setdefault('page', 'overview')
DATA_DIR=Path('data'); PROJECTS_FILE=DATA_DIR/'projects.json'; PAGE_SIZE=5
QUAL=['','Actively in Place','In place but without visible evidence']; BOOL=['','True','False']; YES_NO_SKIP=['Yes','No / Skip']

L1=[
('L1-01','Awareness of sustainability goals','At project initiation, do project lead communicate sustainability objectives with the client and team members, including relevant guidelines or standards, and discuss what is and is not feasible?',['notes','upload'],'qualitative',None,'desirable'),
('L1-02','Awareness of environmental, technical and social sustainability','Do team members participate or enroll in mandatory courses or training on environmental, technical, and social sustainability concepts?',['notes','upload'],'boolean',None,'required'),
('L1-03','Awareness of energy or resource implications','Do team members discuss how builds, testing, deployments and infrastructure usage can have energy and resource implications?As internal brainstorming sessions.',['notes'],'qualitative_numeric','Number of sessions done','desirable'),
('L1-04','Awareness of technical debt impact','Does the team lead or Technical Architect provides guidance on how technical debt can affect maintainability, software longevity, development effort and long-term sustainability? Technical architect assesses and discusses impacts of architectural choices.',['notes'],'boolean',None,'desirable'),
('L1-05','Awareness of developer well-being and burnout risks','Does the manager or HR communicate how workload, excessive overtime, repetitive activities, cognitive load and related factors may affect developer well-being and long-term productivity? Is there a dedicated session for the team?',['notes'],'boolean',None,'required'),
('L1-06','Sustainability objectives discussed during planning','Are sustainability objectives explicitly discussed during project planning, including relevant environmental, technical, and social concerns and their implications for project decisions? Analysis of software features.',['notes','upload'],'numeric','Number of sustainability categories/dimensions','desirable'),
('L1-07','Sustainability dimensions identified for the project','Are relevant sustainability dimensions (environmental, technical, social, and, where applicable, economic) identified and recorded in the project dashboard, making it visible to concerned team? Noting down discussion or outcomes for future visibility and reference.',['notes','upload'],'boolean',None,'desirable'),
('L1-08','Initial identification of DevOps tools supporting sustainability assessment','Does the team members actively review the capabilities of DevOps tools from a sustainability perspective? Selection of tools based on their sustainability reporting ( For instance Jira does this actively)',['notes'],'qualitative',None,'optional'),
('L1-09','Awareness of existing tool capabilities and limitations','Does the team share knowledge about build, testing, and related tools, including their capabilities and limitations for sustainability? Can your team make choices between available tools consisdering sustainability?',['notes'],'boolean',None,'optional'),
]
L2=[
('L2-01','Sustainability skill acquired','Does the team members have done prior course or completed ones before design starts? Not just certifications but technical and real social sustainability concerns are covered.',['upload'],'qualitative',None,'required'),
('L2-02','Collaboration and knowledge-sharing practices','Does the team lead conducts exercises to build collective knowledge such as- given a set of competing features and observe what they prioritise to motivate to integrate knowledge into real practices? Workshops or small sessions to observe individual working patterns, that might affect your oganization\'s sustainability reporting.',['notes','upload'],'numeric','Number of sessions done','required'),
('L2-03','Awareness of accessibility and inclusivity','Does the team members use documented diverse personas/stakeholder groups and discussion of their needs (role-based sustainability concerns)? Figuring out how different user-roles may have different sustainability concern. This may very much depend on the project at hand, i.e., whether such assessment is at all required..',['notes','upload'],'qualitative_numeric','Number of role based sustainability goals identified', 'desirable'),
('L2-04','Sustainability as a parameter during backlog prioritization','Are sustainability considerations explicitly discussed and documented when prioritizing competing features or user stories, with relevant environmental, technical, and social impacts considered alongside business and technical priorities? Are you really making a choice while actual planning?',['notes'], 'qualitative_numeric','Number of items or features resolved for sustainability impact','desirable'),
('L2-05','Reuse of CI/CD components encouraged','Does the team actively identifies existing CI/CD workflows, scripts, actions, configurations, and pipeline components rather than unnecessarily creating duplicate components? This is more of an architectural level goal.',['notes'], 'numeric','Number of reused components estimated','required'),
('L2-06','Burnout risks considered during planning','Does sprint planning evaluate team workload and capacity against delivery demands at any instance \(k\), identify potential burnout risks, and adjust task allocation or delivery commitments when excessive workload or overtime is identified? Not just sessions, but actual efforts to reduce or manage workloads.',['notes','upload'],'numeric','Estimated overtime hours','required'),
('L2-07','Knowledge sharing incorporated into workflows','Are activities such as sprint planning, reviews, retrospectives, technical discussions, and workshops shared among team members? Unequal information share often results in backlogging works. Are you observing such scenarios!!',['notes'],'qualitative',None,'desirable'),
('L2-08','Tool support for reusable workflows','Does the planned pipeline integrate common CI/CD workflow components to reduce unnecessary duplication of workflow configurations? This is at implementation level, if you are reusing things.',['notes'],'boolean',None,'desirable'),
('L2-09','Available IDE support for identifying inefficient code','Does the selected IDE provide mechanisms, such as static analysis tools or plugins, to identify potentially inefficient or resource-intensive code during development?',['notes'],'numeric','Number of sustainability categories/dimensions','optional'),
]

PRECONDITIONS = {
    'L1-01': [],
    'L1-02': [],
    'L1-03': ['L1-02'],
    'L1-04': ['L1-02'],
    'L1-05': [],
    'L1-06': ['L1-02'],
    'L1-07': [],
    'L1-08': ['L1-04'],
    'L1-09': ['L1-04'],

    'L2-01': ['L1-02', 'L1-03', 'L1-04'],
    'L2-02': ['L1-06'],
    'L2-03': [],
    'L2-04': ['L1-06'],
    'L2-05': [],
    'L2-06': ['L1-05'],
    'L2-07': ['L2-02'],
    'L2-08': ['L2-05'],
    'L2-09': [],
}

LEVELS={1:{'name':'Sustainability Awareness','desc':'Sustainability is recognized as a project concern, but practices are largely ad hoc. Sustainability objectives and dimensions are not yet systematically defined.','indicators':L1},2:{'name':'Sustainability Planning','desc':'Defined sustainability requirements and repeatable practices are embedded into CI/CD planning.','indicators':L2},3:{'name':'Sustainability Tracking','desc':'The pipeline systematically tracks qualitative and quantitative sustainability metrics.','indicators':[]},4:{'name':'Sustainability Optimization','desc':'Metric analytics are used to actively optimize resource usage and pipeline efficiency.','indicators':[]},5:{'name':'Sustainability AI-enhanced','desc':'AI models and predictive analytics support or automate sustainability-oriented pipeline optimization.','indicators':[]}}

CSS='''<style>
:root{--g:#1f7a4d;--gl:#e6f2ea;--gb:#cfe5d6}
[data-testid="stSidebar"]{background:#f4f8f5}.brand{font-size:22px;font-weight:600;line-height:1.2}.brand span{font-size:13px;font-weight:400;color:#5b6b62}.avatar{width:40px;height:40px;border-radius:50%;background:#8a9a91;color:white;display:flex;align-items:center;justify-content:center;font-weight:600;margin-left:auto}.banner{display:flex;gap:20px;align-items:center;background:var(--gl);border:1px solid var(--gb);border-radius:12px;padding:20px 24px;margin-bottom:12px}.banner h2{margin:0 0 4px;color:#14532d}.banner p{margin:0;color:#3d4a43}.badge{min-width:60px;height:60px;border-radius:50%;background:var(--g);color:white;font-size:28px;font-weight:600;display:flex;align-items:center;justify-content:center}.tip{background:white;border:1px solid var(--gb);border-radius:10px;padding:12px 16px;min-width:260px;max-width:360px;font-size:13px;color:#3d4a43}.card{border:1px solid #dfe7e2;border-radius:12px;padding:18px;margin-bottom:14px;background:#fff}.title{font-weight:650;font-size:16px;color:#26352e}.id{color:var(--g);font-weight:700;margin-right:8px}.obs{color:#4b5a52;font-size:14px;line-height:1.45;margin-top:6px}.label{font-weight:600;color:#33413a;margin-bottom:4px}.hint{color:#68776f;font-size:12px}[data-testid="stBaseButton-primary"]{background:var(--g);border-color:var(--g)}

.level-progress{
    display:flex;
    width:100%;
    height:92px;
    border-radius:10px;
    overflow:hidden;
    border:1px solid #d8e1dc;
    margin:8px 0 16px 0;
    background:#f5f7f6;
}

.progress-segment{
    flex:1;
    min-width:0;
    padding:10px 14px;
    border-right:1px solid rgba(255,255,255,.85);
    display:flex;
    flex-direction:column;
    justify-content:center;
}

.progress-segment:last-child{
    border-right:none;
}

.progress-segment.red{
    background:#f3c7c7;
    color:#6f2020;
}

.progress-segment.yellow{
    background:#f4df9a;
    color:#654d00;
}

.progress-segment.green{
    background:#bfe3c9;
    color:#155b32;
}

.progress-title{
    font-weight:700;
    font-size:15px;
}

.progress-detail{
    font-size:13px;
    font-weight:600;
    margin-top:2px;
}

.progress-rule{
    font-size:11px;
    opacity:.85;
    margin-top:2px;
}
.progress-insights-hover{
    position:relative;
    display:inline-block;
    margin:8px 0 12px 0;
}

.progress-insights-title{
    font-size:20px;
    font-weight:600;
    color:#26352e;
    cursor:help;
}

.progress-insights-tooltip{
    visibility:hidden;
    opacity:0;
    position:absolute;
    z-index:9999;
    left:0;
    top:calc(100% + 8px);
    width:360px;
    background:#222;
    color:white;
    padding:10px 12px;
    border-radius:6px;
    font-size:13px;
    font-weight:400;
    line-height:1.45;
    text-align:left;
    box-shadow:0 4px 12px rgba(0,0,0,.2);
    transition:opacity .15s ease;
}

.progress-insights-tooltip::after{
    content:"";
    position:absolute;
    bottom:100%;
    left:24px;
    border-width:6px;
    border-style:solid;
    border-color:transparent transparent #222 transparent;
}

.progress-insights-hover:hover .progress-insights-tooltip{
    visibility:visible;
    opacity:1;
}
</style>'''


# ---------- multi-respondent storage ----------
# Each browser session gets its own response_id. The ID is kept in
# Streamlit session state so independently opened browsers remain isolated.
DATA_DIR = Path("data")
RESPONSES_DIR = DATA_DIR / "responses"
PROJECTS_FILE = DATA_DIR / "projects.json"

def slug(x):
    return re.sub(r'[^a-z0-9]+','-',x.lower()).strip('-') or 'project'

def new_response_id():
    return uuid.uuid4().hex

def response_file(response_id):
    return RESPONSES_DIR / f"{response_id}.json"

def template(d):
    return {
        'id': d[0],
        'title': d[1],
        'description': d[2],
        'evidence': [],
        'notes': '',
        'date': date.today().isoformat(),
        'status': (
            'Not evident'
            if d[4] == 'qualitative'
            else 'False'
            if d[4] == 'boolean'
            else None
        ),
        'numeric_value': None,
        'requirement_type': d[6]
    }

def new_data():
    return {
        str(n): {
            'indicators': [template(d) for d in lv['indicators']],
            'notes': '',
            'complete': False
        }
        for n, lv in LEVELS.items()
    }

def load_projects():
    # Projects are now model labels, not the storage key.
    # Keeping this list preserves the existing UI.
    try:
        return json.loads(PROJECTS_FILE.read_text()) if PROJECTS_FILE.exists() else ['Example DevOps Project']
    except Exception:
        return ['Example DevOps Project']

def save_projects():
    PROJECTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROJECTS_FILE.write_text(json.dumps(st.session_state.projects, indent=2))

def load_response(response_id):
    p = response_file(response_id)

    if not p.exists():
        return new_data()

    try:
        existing = json.loads(p.read_text())
    except Exception:
        return new_data()

    # Migrate the saved response against the current maturity model.
    data = new_data()

    for n in LEVELS:
        key = str(n)
        old_level = existing.get(key, {})
        old_indicators = {
            i.get('id'): i
            for i in old_level.get('indicators', [])
            if i.get('id')
        }

        for indicator in data[key]['indicators']:
            iid = indicator['id']

            if iid in old_indicators:
                saved = old_indicators[iid]

                indicator['evidence'] = saved.get('evidence', [])
                indicator['notes'] = saved.get('notes', '')
                indicator['date'] = saved.get('date')
                indicator['status'] = saved.get('status')
                indicator['numeric_value'] = saved.get('numeric_value')

                # Preserve the new Yes / No-Skip gate. For older responses,
                # infer Yes when a substantive assessment existed.
                choice = saved.get('assessment_choice')
                if choice in YES_NO_SKIP:
                    indicator['assessment_choice'] = choice
                else:
                    typ = current_type = next(
                        d[4] for d in LEVELS[n]['indicators'] if d[0] == iid
                    )
                    if typ == 'qualitative':
                        indicator['assessment_choice'] = (
                            'Yes' if saved.get('status') in QUAL else None
                        )
                    elif typ == 'boolean':
                        indicator['assessment_choice'] = (
                            'Yes' if saved.get('status') == 'True' else None
                        )
                    else:
                        indicator['assessment_choice'] = (
                            'Yes' if (
                                saved.get('numeric_value') is not None
                                or saved.get('status') in QUAL
                            ) else None
                        )

                # Keep the current maturity-model classification.
                current = next(
                    d for d in LEVELS[n]['indicators']
                    if d[0] == iid
                )
                indicator['requirement_type'] = current[6]

        data[key]['notes'] = old_level.get('notes', '')
        data[key]['complete'] = old_level.get('complete', False)

    return data

def save_response():
    """
    Save only the current respondent's response.
    The response_id is unique per respondent/browser.
    """
    RESPONSES_DIR.mkdir(parents=True, exist_ok=True)

    payload = {
        'response_id': st.session_state.response_id,
        'respondent_code': st.session_state.respondent_code,
        'project': st.session_state.project,
        'user': st.session_state.user,
        'created_at': st.session_state.created_at,
        'updated_at': pd.Timestamp.utcnow().isoformat(),
        'data': st.session_state.data,
    }

    response_file(st.session_state.response_id).write_text(
        json.dumps(payload, indent=2)
    )

# Backwards-compatible name used by the existing UI.
save_project = save_response

def init():
    DATA_DIR.mkdir(exist_ok=True)
    RESPONSES_DIR.mkdir(exist_ok=True)

    s = st.session_state

    # IMPORTANT:
    # Do NOT automatically put a generated response_id into the URL.
    # If the first browser's URL is copied to another browser, both browsers
    # would otherwise intentionally use the same response_id.
    #
    # A fresh Streamlit browser session gets a fresh UUID in session_state.
    # This guarantees that two independently opened browsers have different
    # response IDs.
    if 'response_id' not in s:
        s.response_id = new_response_id()
        s.created_at = pd.Timestamp.utcnow().isoformat()

    s.setdefault('created_at', pd.Timestamp.utcnow().isoformat())
    s.setdefault('respondent_code', '')
    s.setdefault('projects', load_projects())
    s.setdefault('project', s.projects[0])
    s.setdefault('page', 'overview')
    s.setdefault('user', '')
    s.setdefault('level_indicator_index', {n: 0 for n in LEVELS})
    s.setdefault('next_level_message', None)

    if s.get('loaded_response_id') != s.response_id:
        saved = load_response(s.response_id)

        # Support both the new wrapped response format and the older
        # project-data-only format.
        if isinstance(saved, dict) and 'data' in saved:
            s.data = saved['data']
            s.respondent_code = saved.get('respondent_code', '')
            s.project = saved.get('project', s.projects[0])
            s.user = saved.get('user', '')
            s.created_at = saved.get('created_at', s.created_at)
        else:
            s.data = saved

        s.loaded_response_id = s.response_id

def lv(n):return st.session_state.data[str(n)]
def defs(n):return {d[0]:d for d in LEVELS[n]['indicators']}
def inds(n):return lv(n).get('indicators',[])
def satisfied(i,d):
    # "No / Skip" is equivalent to the former "Not evident" state.
    if i.get('assessment_choice') != 'Yes':
        return False

    typ=d[4]
    if typ=='qualitative':
        return i.get('status') == 'Actively in Place'
    if typ=='boolean':
        return i.get('status')=='True'
    if typ=='qualitative_numeric':
        return (
            i.get('status') == 'Actively in Place'
            and i.get('numeric_value') is not None
            and i.get('numeric_value') > 0
        )
    if typ=='numeric':
        return i.get('numeric_value') is not None and i.get('numeric_value') > 0
    return False

def complete(i,d):
    return satisfied(i,d)
def counts(n):
    a=inds(n); ds=defs(n); return sum(complete(i,ds[i['id']]) for i in a),len(a)
def status(n):
    d,t=counts(n)
    if lv(n)['complete']:return 'Complete'
    return 'In progress' if d else 'Not started'
def achieved():
    r=0
    for n in LEVELS:
        if lv(n)['complete']:r=n
        else:break
    return r
def evidence_path(iid,fn):
    # Evidence belongs to the respondent response, not to the shared project.
    p = RESPONSES_DIR / st.session_state.response_id / 'evidence' / iid
    p.mkdir(parents=True, exist_ok=True)
    return p / Path(fn).name

def save_uploads(i,files):
    for f in files or []:
        p=evidence_path(i['id'],f.name)
        if not p.exists():p.write_bytes(f.getbuffer())
        if p.name not in i['evidence']:i['evidence'].append(p.name)

def precondition_status(indicator_id):
    """Return whether an indicator's prerequisite indicators are satisfied."""
    prereqs = PRECONDITIONS.get(indicator_id, [])
    if not prereqs:
        return True, []

    unresolved = []

    for prereq_id in prereqs:
        found = False
        for level_number in LEVELS:
            definitions = defs(level_number)
            for indicator in inds(level_number):
                if indicator.get('id') == prereq_id:
                    found = True
                    if not satisfied(indicator, definitions[prereq_id]):
                        unresolved.append(prereq_id)
                    break
            if found:
                break

        if not found:
            unresolved.append(prereq_id)

    return len(unresolved) == 0, unresolved


def render_locked_indicator(
    indicator_id,
    title,
    description,
    requirement,
    unresolved
):
    """Display a locked indicator with its unmet prerequisites."""
    prereq_text = ", ".join(unresolved)

    with st.container(border=True):
        st.markdown(f"**🔒 {indicator_id}  {title}**")
        st.caption(f"Type: {requirement}")
        st.markdown(f"**What is Required:** {description}")

        # Hover over the lock to see the prerequisite information.
        st.markdown(
            f'<span title="Complete prerequisite indicator(s): {prereq_text}">'
            f'🔒 Locked — complete prerequisite indicator(s): {prereq_text}'
            f'</span>',
            unsafe_allow_html=True
        )



def indicator_card(n, i, d):
    """Render exactly one indicator, with a Yes / No-Skip gate."""
    iid = i['id']
    key = f'{st.session_state.response_id}-{iid}'
    typ = d[4]
    requirement = d[6].title()

    unlocked, unresolved = precondition_status(iid)
    if not unlocked:
        render_locked_indicator(
            iid, i['title'], i['description'], requirement, unresolved
        )
        return

    with st.container(border=True):
        st.markdown(f"**{iid}  {i['title']}**")
        st.caption(f"Type: {requirement}")
        st.markdown(f"**What is Required:** {i['description']}")

    # First decision: is this indicator applicable/evident enough to assess?
    current_choice = i.get('assessment_choice')
    if current_choice not in YES_NO_SKIP:
        current_choice = None

    choice = st.radio(
        "Is this indicator applicable / present?",
        YES_NO_SKIP,
        index=None if current_choice is None else YES_NO_SKIP.index(current_choice),
        key=key + '-choice',
        horizontal=True,
        help='Select Yes to record evidence and assessment. Select No / Skip to treat this indicator as not evident.'
    )

    # Keep the choice in the in-memory response immediately.
    if choice:
        i['assessment_choice'] = choice

    if choice == 'Yes':
        e, m = st.columns([1.5, 1], gap='large')

        with e:
            st.markdown("**Evidence**")

            if 'notes' in d[3]:
                i['notes'] = st.text_area(
                    'Notes',
                    i.get('notes', ''),
                    key=key + '-notes',
                    height=95,
                    placeholder='Record the activity, discussion, decision, or observation...'
                )

            if 'upload' in d[3]:
                files = st.file_uploader(
                    'Supporting document',
                    accept_multiple_files=True,
                    key=key + '-files'
                )
                save_uploads(i, files)

                if i['evidence']:
                    st.caption(f"📎 {len(i['evidence'])} supporting file(s) saved")
                    for fn in i['evidence']:
                        ep = evidence_path(iid, fn)
                        if ep.exists():
                            st.download_button(
                                f'View/download {fn}',
                                ep.read_bytes(),
                                file_name=fn,
                                key=key + '-dl-' + slug(fn)
                            )

        with m:
            st.markdown("**Status / measurement**")

            if typ == 'qualitative':
                cur = i.get('status')
                if cur not in QUAL:
                    cur = QUAL[0]
                i['status'] = st.selectbox(
                    'Assign a qualitative degree of satisfaction of the activity',
                    QUAL,
                    index=QUAL.index(cur),
                    key=key + '-status'
                )

            elif typ == 'boolean':
                cur = i.get('status')
                if cur not in BOOL:
                    cur = BOOL[0]
                i['status'] = st.selectbox(
                    'Select a binary value based on present status of the activity',
                    BOOL,
                    index=BOOL.index(cur),
                    key=key + '-status'
                )

            elif typ == 'qualitative_numeric':
                cur = i.get('status')
                if cur not in QUAL:
                    cur = QUAL[0]
                i['status'] = st.selectbox(
                    'Assign a qualitative degree of satisfaction of the activity',
                    QUAL,
                    index=QUAL.index(cur),
                    key=key + '-status'
                )
                i['numeric_value'] = st.number_input(
                    d[5],
                    min_value=0,
                    step=1,
                    value=0 if i.get('numeric_value') is None else int(i['numeric_value']),
                    key=key + '-num'
                )

            elif typ == 'numeric':
                i['numeric_value'] = st.number_input(
                    d[5],
                    min_value=0,
                    step=1,
                    value=0 if i.get('numeric_value') is None else int(i['numeric_value']),
                    key=key + '-num'
                )

        c1, c2 = st.columns([1, 1])
        with c1:
            cur = date.fromisoformat(i['date']) if i.get('date') else None
            x = st.date_input(
                'Recorded date',
                value=cur,
                format='YYYY-MM-DD',
                key=key + '-date'
            )
            i['date'] = x.isoformat() if x else None
        with c2:
            st.caption('Complete the fields above, then use one of the save buttons below.')

    elif choice == 'No / Skip':
        # No / Skip is explicitly equivalent to the former Not evident state.
        i['status'] = 'Not evident' if typ in ('qualitative', 'qualitative_numeric') else (
            'False' if typ == 'boolean' else i.get('status')
        )
        i['numeric_value'] = None
        i['notes'] = ''
        st.info('No / Skip recorded. This indicator is treated as not evident and does not contribute to maturity progress.')

    else:
        st.info('Select **Yes** to record evidence and an assessment, or **No / Skip** to treat the indicator as not evident.')


def indicators_tab(n):
    a = inds(n)
    ds = defs(n)

    if not a:
        st.info(f'Level {n} yet to be built!!!!')
        return

    if n == 1:
        st.subheader('Level 1 Indicators')
        st.caption('This is best to do at project initiation. But not restricted to it')
    elif n == 2:
        st.subheader('Level 2 Indicators')
        st.caption('This is best to do at feature planning stage. The indicators assess how sustainable your organization\'s approach is.')

    idx = st.session_state.level_indicator_index.get(n, 0)
    idx = max(0, min(idx, len(a) - 1))
    st.session_state.level_indicator_index[n] = idx

    st.markdown(
        f"### Indicator {idx + 1} of {len(a)}"
    )

    indicator_card(n, a[idx], ds[a[idx]['id']])

def evidence_tab(n):
    rows=[i for i in inds(n) if i.get('notes') or i.get('evidence') or i.get('numeric_value') is not None]
    if not rows:st.info('No indicator evidence or measurements recorded yet.');return
    for i in rows:
        st.markdown(f"### {i['id']} · {i['title']}")
        if i.get('notes'):st.markdown('**Notes**');st.write(i['notes'])
        if i.get('evidence'):
            st.markdown('**Supporting documents**')
            for fn in i['evidence']:
                p=evidence_path(i['id'],fn)
                if p.exists():st.download_button(f'📎 {fn}',p.read_bytes(),file_name=fn,key=f'e-{i["id"]}-{slug(fn)}')
        if i.get('numeric_value') is not None:st.metric('Recorded quantitative value',i['numeric_value'])
        st.divider()
def progress_tab(n):
    a=inds(n);d,t=counts(n);c1,c2,c3=st.columns(3);c1.metric('Indicators assessed',f'{d}/{t}');c2.metric('Indicators with evidence',sum(bool(i.get('notes') or i.get('evidence')) for i in a));c3.metric('Level status',status(n));st.progress(d/t if t else 0)
    ds=defs(n);rows=[]
    for i in a:
        unlocked, unresolved = precondition_status(i['id'])
        rows.append({
            'ID':i['id'],
            'Indicator':i['title'],
            'Status':'Locked' if not unlocked else i.get('status'),
            'Numeric value':None if not unlocked else i.get('numeric_value'),
            'Notes':False if not unlocked else bool(i.get('notes')),
            'Documents':0 if not unlocked else len(i.get('evidence',[])),
            'Complete':False if not unlocked else complete(i,ds[i['id']]),
            'Prerequisites':', '.join(unresolved) if unresolved else ''
        })
    st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
def level_page(n):
    x = LEVELS[n]

    # Levels 3–5 are intentionally locked.
    if n in (3, 4, 5):
        st.markdown(
            f"<div class='banner'><div class='badge'>🔒</div>"
            f"<div style='flex:1'><h2>Level {n} – {x['name']}</h2>"
            f"<p>This level is currently under development.</p></div></div>",
            unsafe_allow_html=True
        )
        st.info(f"Level {n} is currently locked while the next maturity-level content is being developed.")
        if st.button("← Back to Dashboard", use_container_width=True):
            go("dashboard")
            st.rerun()
        return

    st.markdown(
        f"<div class='banner'><div class='badge'>{n}</div>"
        f"<div style='flex:1'><h2>Level {n} – {x['name']}</h2>"
        f"<p>{x['desc']}</p></div>"
        f"<div class='tip'><b>💡 Evidence recording</b><br>"
        f"Each indicator has its own evidence and assessment fields.<br><br>"
        f"🔒 Indicators with unmet prerequisites remain locked.</div></div>",
        unsafe_allow_html=True
    )

    if lv(n)['complete']:
        st.success(f'Level {n} is marked complete.')

    # Only retain the indicator/evidence/notes/progress tabs.
    a, b, c, d = st.tabs(
        ['Indicators', 'Evidence Summary', 'Level Notes', 'Progress']
    )

    with a:
        indicators_tab(n)
    with b:
        evidence_tab(n)
    with c:
        lv(n).__setitem__(
            'notes',
            st.text_area(
                'Level notes',
                lv(n).get('notes', ''),
                height=180,
                key=f'ln-{n}'
            )
        )
    with d:
        progress_tab(n)

    st.divider()

    idx = st.session_state.level_indicator_index.get(n, 0)
    total = len(inds(n))
    is_last = total > 0 and idx >= total - 1

    back, _, save_next, save_exit = st.columns([1.2, 3, 2.2, 1.8])

    with back:
        if st.button(
            '← Previous',
            use_container_width=True,
            key=f'level-previous-{n}'
        ):
            save_response()
    
            if idx == 0:
                # First indicator → Dashboard
                go('dashboard')
            else:
                # Otherwise → previous indicator
                st.session_state.level_indicator_index[n] = idx - 1
    
            st.rerun()

    with save_next:
        if is_last:
            button_label = (
                'Save and go to next level'
                if n == 1
                else 'Save and go to next level'
            )
        else:
            button_label = 'Save and go to next'

        if st.button(
            button_label,
            type='primary',
            use_container_width=True,
            key=f'level-save-next-{n}'
        ):
            save_response()

            if is_last:
                if n == 1:
                    st.session_state.level_indicator_index[2] = 0
                    go('level-2')
                    st.rerun()
                elif n == 2:
                    st.session_state.next_level_message = (
                        'The next level is currently being built. '
                        'Your Level 2 assessment has been saved.'
                    )
                    go('dashboard')
                    st.rerun()
            else:
                st.session_state.level_indicator_index[n] = min(
                    idx + 1,
                    total - 1
                )
                st.rerun()

    with save_exit:
        if st.button(
            'Save and exit',
            use_container_width=True,
            key=f'level-save-exit-{n}'
        ):
            save_response()
            go('dashboard')
            st.rerun()

def header():
    s = st.session_state
    c1, c2, c3 = st.columns([5, 3, .8], vertical_alignment='center')
    c1.markdown(
        "<div class='brand'>🌿 Sustainability Maturity Tool<br>"
        "<span>Measure • Improve • Build a Greener DevOps</span></div>",
        unsafe_allow_html=True
    )
    c2.selectbox('Project', s.projects, key='project')
    display_code = s.respondent_code.strip() or 'Participant'
    c3.markdown(
        f"<div class='avatar'>{display_code[:3].upper()}</div>",
        unsafe_allow_html=True
    )
    st.divider()
def sidebar():
    p = st.session_state.page
    nav = [
        ('overview', '📖 Overview'),
        ('dashboard', '🏠 Dashboard'),
        ('assessment', '📊 Maturity Assessment')
    ]

    for n, x in LEVELS.items():
        if n in (3, 4, 5):
            nav.append((f'level-{n}', f'🔒 {n} · Level {n} – {x["name"]}'))
        else:
            nav.append((f'level-{n}', f'{n} · Level {n} – {x["name"]}'))

    nav += [
        ('reports', '📄 Reports'),
        ('settings', '⚙️ Settings')
    ]

    with st.sidebar:
        for k, label in nav:
            if k in ('level-3', 'level-4', 'level-5'):
                st.button(
                    label,
                    key='nav-' + k,
                    use_container_width=True,
                    disabled=True,
                    help='This level is currently under development.'
                )
            else:
                st.button(
                    label,
                    key='nav-' + k,
                    use_container_width=True,
                    on_click=lambda k=k: st.session_state.__setitem__('page', k),
                    type='primary' if p == k else 'secondary'
                )

        st.divider()
        st.caption('🌿 Smaller footprints. Stronger software.')


def go(page):
    """Set the current Streamlit page."""
    st.session_state.page = page


def level_progress_condition(n):
    """
    Dashboard progress conditions.

    Sufficient:
        All required indicators are satisfied.

    Sufficient+:
        More than 30% of desirable + optional indicators are satisfied.

    Advanced:
        At least 80% of all indicators are satisfied.
    """
    a = inds(n)

    if not a:
        return {
            "required_total": 0,
            "required_satisfied": 0,
            "desirable_optional_total": 0,
            "desirable_optional_satisfied": 0,
            "all_total": 0,
            "all_satisfied": 0,
            "sufficient": False,
            "sufficient_plus": False,
            "advanced": False,
        }

    ds = defs(n)

    required = [
        i for i in a
        if ds[i["id"]][6].lower() == "required"
    ]

    desirable_optional = [
        i for i in a
        if ds[i["id"]][6].lower() in ("desirable", "optional")
    ]

    required_satisfied = sum(
        satisfied(i, ds[i["id"]])
        for i in required
    )

    desirable_optional_satisfied = sum(
        satisfied(i, ds[i["id"]])
        for i in desirable_optional
    )

    all_satisfied = sum(
        satisfied(i, ds[i["id"]])
        for i in a
    )

    # Condition 1: all required indicators must be met.
    sufficient = (
        bool(required)
        and required_satisfied == len(required)
    )

    # Condition 2: more than 30% of desirable + optional indicators.
    # Condition 2: Sufficient+
    # ---------------------------------------------------------
    # Condition 2: Sufficient+
    #
    # Sufficient+ is cumulative:
    # Sufficient must already be achieved AND the additional
    # Sufficient+ criterion must be achieved.
    # ---------------------------------------------------------
    
    if n == 1:
        # Level 1:
        # 1. All required indicators must be satisfied.
        # 2. All important desirable indicators that act as
        #    prerequisites for Level 2 must also be satisfied.
    
        next_level_prerequisites = set()
    
        for indicator_id, prerequisites in PRECONDITIONS.items():
            if indicator_id.startswith('L2-'):
                for prerequisite in prerequisites:
                    if prerequisite.startswith('L1-'):
                        next_level_prerequisites.add(prerequisite)
    
        important_desirable = [
            i for i in desirable_optional
            if (
                i['id'] in next_level_prerequisites
                and ds[i['id']][6].lower() == 'desirable'
            )
        ]
    
        important_desirable_satisfied = sum(
            satisfied(i, ds[i['id']])
            for i in important_desirable
        )
    
        sufficient_plus = (
            sufficient
            and bool(important_desirable)
            and important_desirable_satisfied == len(important_desirable)
        )
    
    elif n == 2:
        # Level 2:
        # 1. All required indicators must be satisfied.
        # 2. At least 60% of desirable indicators must be satisfied.
    
        desirable = [
            i for i in a
            if ds[i['id']][6].lower() == 'desirable'
        ]
    
        desirable_satisfied = sum(
            satisfied(i, ds[i['id']])
            for i in desirable
        )
    
        sufficient_plus = (
            sufficient
            and bool(desirable)
            and desirable_satisfied >= ceil(len(desirable) * 0.60)
        )
    
    else:
        sufficient_plus = False

    # Condition 3: at least 80% of all indicators.
    overall_ratio = all_satisfied / len(a)

    advanced = (
        sufficient_plus
        and overall_ratio >= 0.80
    )

    return {
        "required_total": len(required),
        "required_satisfied": required_satisfied,
        "desirable_optional_total": len(desirable_optional),
        "desirable_optional_satisfied": desirable_optional_satisfied,
        "all_total": len(a),
        "all_satisfied": all_satisfied,
        "sufficient": sufficient,
        "sufficient_plus": sufficient_plus,
        "advanced": advanced,
    }



def dashboard_progress_bar(n):
    """Render one horizontal three-section maturity progress bar with hover details."""

    result = level_progress_condition(n)

    required_total = result["required_total"]
    required_satisfied = result["required_satisfied"]
    dopt_total = result["desirable_optional_total"]
    dopt_satisfied = result["desirable_optional_satisfied"]
    all_total = result["all_total"]
    all_satisfied = result["all_satisfied"]

    sufficient = result["sufficient"]
    sufficient_plus = result["sufficient_plus"]
    advanced = result["advanced"]

    def state_colour(met, partial):
        if met:
            return "#d1e7dd"       # green
        if partial:
            return "#fff3cd"       # yellow
        return "#f8d7da"           # red

    sufficient_colour = state_colour(
        sufficient,
        required_satisfied > 0 and required_satisfied < required_total
    )

    sufficient_plus_partial = (
        dopt_total > 0
        and dopt_satisfied > 0
        and dopt_satisfied / dopt_total <= 0.30
    )

    sufficient_plus_colour = state_colour(
        sufficient_plus,
        sufficient_plus_partial
    )

    advanced_colour = state_colour(
        advanced,
        (
            all_satisfied > 0
            and all_total > 0
            and all_satisfied / all_total < 0.80
        )
    )

    # ---------------------------------------------------------
    # Build hover text
    # ---------------------------------------------------------

    level_indicators = inds(n)
    definitions = defs(n)

    # Required indicator IDs
    required_ids = [
        i["id"]
        for i in level_indicators
        if definitions[i["id"]][6].lower() == "required"
    ]

    # Level 1 Sufficient+:
    # desirable indicators that are prerequisites for Level 2
    important_desirable_ids = []

    if n == 1:
        level_2_indicators = inds(2)
        level_2_definitions = defs(2)

        level_2_prereqs = set()

        for indicator in level_2_indicators:
            iid = indicator["id"]
            for prereq in PRECONDITIONS.get(iid, []):
                level_2_prereqs.add(prereq)

        important_desirable_ids = [
            i["id"]
            for i in level_indicators
            if (
                i["id"] in level_2_prereqs
                and level_2_definitions is not None
                and definitions[i["id"]][6].lower() == "desirable"
            )
        ]

    # Level 2 Sufficient+:
    # show all desirable IDs and explain that any 60% qualify
    desirable_ids = [
        i["id"]
        for i in level_indicators
        if definitions[i["id"]][6].lower() == "desirable"
    ]

    if n == 1:
        sufficient_plus_hover = (
            "<b>Indicators to Satisfy:</b><br>"
            + (
               ", " .join(important_desirable_ids)
                if important_desirable_ids
                else "None identified"
            )
        )
    elif n == 2:
        sufficient_plus_hover = (
            "<b>Indicators to Satisfy:</b><br>"
            + (
                ", ".join(desirable_ids)
                if desirable_ids
                else "None identified"
            )
        )
    else:
        sufficient_plus_hover = "<b>Desirable indicators</b>"

    required_hover = (
        "<b>Required indicators:</b><br>"
        + (
            ", ".join(required_ids)
            if required_ids
            else "None identified"
        )
    )

    advanced_hover = (
        "Fulfill more than 70% of desired and optional indicators"
    )

    # ---------------------------------------------------------
    # HTML
    # ---------------------------------------------------------

    html = f"""
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background: transparent;
        }}

        .progress-container {{
            display: flex;
            width: 100%;
            overflow: visible;
            border: 1px solid #d9d9d9;
            border-radius: 8px;
            margin-top: 8px;
            margin-bottom: 70px;
            box-sizing: border-box;
        }}

        .progress-segment {{
            position: relative;
            flex: 1;
            padding: 12px 14px;
            min-height: 82px;
            box-sizing: border-box;
            border-right: 1px solid #d9d9d9;
            cursor: help;
        }}

        .progress-segment:last-child {{
            border-right: none;
        }}

        .segment-title {{
            font-weight: 700;
            margin-bottom: 6px;
            font-size: 15px;
        }}

        .segment-detail {{
            font-size: 13px;
        }}

        .tooltip {{
            visibility: hidden;
            opacity: 0;
            position: absolute;
            z-index: 9999;
            left: 50%;
            top: calc(100% + 8px);
            transform: translateX(-50%);
            width: 270px;
            background: #222;
            color: white;
            padding: 10px 12px;
            border-radius: 6px;
            font-size: 13px;
            line-height: 1.45;
            text-align: left;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            transition: opacity 0.15s ease;
        }}

        .tooltip::after {{
            content: "";
            position: absolute;
            bottom: 100%;
            left: 50%;
            margin-left: -6px;
            border-width: 6px;
            border-style: solid;
            border-color: transparent transparent
        }}

        .progress-segment:hover .tooltip {{
            visibility: visible;
            opacity: 1;
        }}
    </style>

    <div class="progress-container">

        <div class="progress-segment"
             style="background:{sufficient_colour};">

            <div class="segment-title">
                Sufficient
            </div>

            <div class="segment-detail">
                {required_satisfied}/{required_total} required
            </div>

            <div class="tooltip">
                {required_hover}
            </div>

        </div>


        <div class="progress-segment"
             style="background:{sufficient_plus_colour};">

            <div class="segment-title">
                Sufficient+
            </div>

            <div class="segment-detail">
                {dopt_satisfied}/{dopt_total} desirable + optional
            </div>

            <div class="tooltip">
                {sufficient_plus_hover}
            </div>

        </div>


        <div class="progress-segment"
             style="background:{advanced_colour};">

            <div class="segment-title">
                Advanced
            </div>

            <div class="segment-detail">
                {all_satisfied}/{all_total} indicators
            </div>

            <div class="tooltip">
                {advanced_hover}
            </div>

        </div>

    </div>
    """

    components.html(
        html,
        height=190,
        scrolling=False
    )

def overview():
    st.subheader("Overview")

    st.markdown(
        """
        <div class="banner">
            <div class="badge">🌿</div>
            <div style="flex:1">
                <h2>Welcome to the Sustainability Maturity Tool</h2>
                <p>
                    A self-assessment tool for evaluating sustainability maturity
                    across software development and DevOps practices.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ---------------------------------------------------------
    # 1. Purpose of the tool
    # ---------------------------------------------------------

    st.markdown(
        """
        <div class="card">
            <div class="title">1. What is the purpose of the tool?</div>
            <div class="obs">
                The tool supports self-assessment of sustainability maturity
                in software development and DevOps practices. It uses the
                Sustainability Maturity Framework (SuMaF) to help users
                understand the current maturity of their sustainability
                practices, identify gaps, and understand areas that may
                require further improvement.
            </div>
            <div class="obs">
                The assessment currently focuses on <b>Level 1 –
                Sustainability Awareness</b> and <b>Level 2 –
                Sustainability Planning</b>. Higher maturity levels are
                planned for future releases.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ---------------------------------------------------------
    # 2. What is expected from the user?
    # ---------------------------------------------------------

    st.markdown(
        """
        <div class="card">
            <div class="title">2. What is expected from the user?</div>
            <div class="obs">
                The user is expected to review each sustainability indicator
                and provide information about the current status of the
                practice within their project or organisation.
            </div>
            <div class="obs">
                For each applicable indicator, the user should:
            </div>
            <ul>
                <li>Indicate whether the practice is applicable / present.</li>
                <li>Provide relevant evidence, notes, or supporting documents where applicable.</li>
                <li>Enter quantitative information where the indicator requires measurement.</li>
                <li>Provide the recorded date for the assessment.</li>
                <li>Use <b>No / Skip</b> where the indicator is not applicable or not currently evident.</li>
            </ul>
            <div class="obs">
                Some indicators may remain locked until their prerequisite
                indicators have been addressed.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ---------------------------------------------------------
    # 3. What does the tool provide as output?
    # ---------------------------------------------------------

    st.markdown(
        """
        <div class="card">
            <div class="title">3. What does the tool provide as output?</div>
            <div class="obs">
                Based on the information and evidence entered by the user,
                the tool provides a structured view of sustainability
                maturity progress.
            </div>
            <ul>
                <li>Current sustainability maturity-level progress.</li>
                <li>Progress against individual sustainability indicators.</li>
                <li>Progress made at each level by satisfying three conditions such as <b>Sufficient</b>,
                    <b>Sufficient+</b>, and <b>Advanced</b>.</li>
                <li>Identification of indicators that remain incomplete or
                    locked because of unmet prerequisites.</li>
                <li>Assessment reports that can be downloaded for further
                    analysis.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ---------------------------------------------------------
    # 4. Future release plans
    # ---------------------------------------------------------

    st.markdown(
        """
        <div class="card">
            <div class="title">4. Future Release Plans</div>
            <div class="obs">
                The current application is a prototype. Future releases
                are planned to extend and refine the SuMaF assessment
                capability.
            </div>
            <div style="margin-top:14px;">
                <b>a. Fine-tuning based on survey outcomes</b>
            </div>
            <div class="obs">
                The framework, indicators, assessment criteria, and tool
                interface will be refined based on feedback and evaluation
                results from the current research survey.
            </div>
            <div style="margin-top:14px;">
                <b>b. Development of Levels 3 to 5</b>
            </div>
            <div class="obs">
                Future releases will extend the assessment to:
                <b>Level 3 – Sustainability Tracking</b>,
                <b>Level 4 – Sustainability Optimization</b>, and
                <b>Level 5 – Sustainability AI-enhanced</b>.
            </div>
            <div style="margin-top:14px;">
                <b>c. Optional AI Mode</b>
            </div>
            <div class="obs">
                An optional AI mode is planned to provide real-time,
                automated sustainability feedback based on the data,
                evidence, and assessments entered against individual
                indicators.
            </div>
            <div class="obs">
                The AI mode will be <b>optional</b>. Users will be able to
                perform the standard assessment without using AI.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ---------------------------------------------------------
    # Start assessment
    # ---------------------------------------------------------

    st.divider()

    if st.button(
        "▶ Start Sustainability Assessment",
        type="primary",
        use_container_width=True,
        key="overview-start-assessment"
    ):
        st.session_state.level_indicator_index[1] = 0
        go("level-1")
        st.rerun()
        
def dashboard():
    st.subheader('Dashboard')

    if st.session_state.get('next_level_message'):
        st.success(st.session_state.next_level_message)
        st.session_state.next_level_message = None


    reached = achieved()

    all_done = sum(
        counts(n)[0]
        for n in LEVELS
    )

    all_total = sum(
        counts(n)[1]
        for n in LEVELS
    )

    m1, m2, m3 = st.columns(3)

    m1.metric(
        "Current maturity level",
        f"Level {reached}" if reached else "Level Progress",
    )

    m2.metric(
        "Indicators satisfied",
        f"{all_done} / {all_total}",
    )

    # Last activity / last update date
    last_update = None
    for n in LEVELS:
        for i in inds(n):
            if i.get('date'):
                try:
                    d = date.fromisoformat(i['date'])
                    if last_update is None or d > last_update:
                        last_update = d
                except Exception:
                    pass

    m3.metric(
        "Last Access",
        last_update.strftime("%Y-%m-%d") if last_update else "Not yet updated",
    )

    st.divider()

    # Start the assessment from Level 1.
    if st.button(
        "▶ Start Assessment",
        type="primary",
        use_container_width=True,
        key="dashboard-start-assessment"
    ):
        st.session_state.level_indicator_index[1] = 0
        go("level-1")
        st.rerun()

    st.subheader("Level progress conditions")
    st.caption(
        "Each level progresses through three conditions: Sufficient, "
        "Sufficient+, and Advanced."
    )

    for n, lv in LEVELS.items():
        if not inds(n):
            continue

        with st.container(border=True):
            st.markdown(f"**Level {n} – {lv['name']}**")
            dashboard_progress_bar(n)


def requirement_type_chart(n):
    """Render the requirement-type percentage chart for a maturity level."""
    # Reuse the existing percentage chart helper when available.
    if "percentage_requirement_chart" in globals():
        return percentage_requirement_chart(n)
    if "requirement_percentage_chart" in globals():
        return requirement_percentage_chart(n)

    # Fallback: display the requirement counts used by the dashboard.
    result = level_progress_condition(n)
    rows = [
        {"Requirement type": "Required",
         "Satisfied": result["required_satisfied"],
         "Total": result["required_total"]},
        {"Requirement type": "Desirable + Optional",
         "Satisfied": result["desirable_optional_satisfied"],
         "Total": result["desirable_optional_total"]},
        {"Requirement type": "All",
         "Satisfied": result["all_satisfied"],
         "Total": result["all_total"]},
    ]
    st.dataframe(rows, use_container_width=True)


def assessment():
    st.subheader('Maturity assessment')

    # Last update across all recorded indicator activity.
    last_update = None
    for n in LEVELS:
        for i in inds(n):
            if i.get('date'):
                try:
                    d = date.fromisoformat(i['date'])
                    if last_update is None or d > last_update:
                        last_update = d
                except Exception:
                    pass

    if last_update:
        st.info(
            f"Last activity: **{last_update.strftime('%Y-%m-%d')}**"
        )
    else:
        st.info("Last activity: **No activity recorded yet**")

    rows = []
    for n, x in LEVELS.items():
        d, t = counts(n)
        rows.append({
            'Level': n,
            'Name': x['name'],
            'Satisfied': f'{d}/{t}',
            'Progress %': round(100 * d / t) if t else 0,
            'Status': status(n)
        })

    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        use_container_width=True
    )

    st.divider()
    # Progress Insights heading with hover explanation
    st.markdown(
    '<div class="progress-insights-hover">'
    '<span class="progress-insights-title">Your Progress Insights</span>'
    '<span class="progress-insights-tooltip">'
    'Tool will analyse entered data and give real time sustainability insights'
    '</span>'
    '</div>',
    unsafe_allow_html=True
    )
    
    suggestions_found = False
    
    if not suggestions_found:
        st.success(
            "Collaborate and share your insights with team..... (Build In Progress!!!)"
        )
def reports():
    st.subheader('Reports');rows=[]
    for n,x in LEVELS.items():
        ds=defs(n)
        for i in inds(n):rows.append({'Level':n,'Requirement type':ds[i['id']][6].title(),'Indicator ID':i['id'],'Indicator':i['title'],'Measurement type':ds[i['id']][4],'Status':i.get('status'),'Numeric value':i.get('numeric_value'),'Satisfied':satisfied(i,ds[i['id']]),'Notes':i.get('notes'),'Date':i.get('date'),'Evidence files':'; '.join(i.get('evidence',[]))})
    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True, use_container_width=True)

    stem = f"response-{st.session_state.response_id}"
    c1, c2 = st.columns(2)
    c1.download_button(
        'Download CSV',
        df.to_csv(index=False),
        f'{stem}-assessment.csv',
        'text/csv'
    )
    c2.download_button(
        'Download JSON',
        json.dumps({
            'response_id': st.session_state.response_id,
            'respondent_code': st.session_state.respondent_code,
            'project': st.session_state.project,
            'user': st.session_state.user,
            'data': st.session_state.data
        }, indent=2),
        f'{stem}-assessment.json',
        'application/json'
    )
def settings():
    s = st.session_state
    st.subheader('Respondent / Survey Session')

    entered_code = st.text_input(
        'Participant code',
        s.respondent_code,
        help='Enter the unique anonymous participant code assigned to you.'
    ).strip().upper()

    if entered_code != s.respondent_code:
        s.respondent_code = entered_code

    s.user = st.text_input(
        'Your initials (optional)',
        s.user,
        max_chars=3
    ).upper()

    st.caption(f"Response ID: `{s.response_id}`")
    st.caption('This response is isolated from other respondents.')

    st.info(
        'Each browser session has a different Response ID. '
        'Do not copy a URL containing a response_id from one participant to another.'
    )

    if st.button('Save respondent details'):
        save_response()
        st.success('Respondent details saved.')

    st.divider()
    st.subheader('Project configuration')
    name = st.text_input('New project', placeholder='e.g. Payments platform')

    if st.button('Add project'):
        if name.strip() and name.strip() not in s.projects:
            s.projects.append(name.strip())
            save_projects()
            st.success(f'Added {name.strip()}')
        else:
            st.error('Enter a new project name.')

init()
st.markdown(CSS, unsafe_allow_html=True)
header()
#if st.session_state.respondent_code:
    #st.caption(
        #f"Independent survey response: **{st.session_state.respondent_code}**"
        #f" · Response ID: `{st.session_state.response_id}`"
    #)
#else:
    #st.info(
        #"Please open Settings and enter your unique anonymous participant code "
        #"before starting the assessment. Each browser session is isolated."
    #)
sidebar()
p = st.session_state.page

if p == 'overview':
    overview()
elif p.startswith('level-'):
    level_page(int(p.split('-')[1]))
elif p == 'assessment':
    assessment()
elif p == 'reports':
    reports()
elif p == 'settings':
    settings()
else:
    dashboard()
