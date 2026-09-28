import json, re
from pathlib import Path
from datetime import date
from math import ceil
import pandas as pd
import streamlit as st

st.set_page_config(page_title='Sustainability Maturity Tool', page_icon='🌿', layout='wide')

st.session_state.setdefault('page', 'dashboard')
DATA_DIR=Path('data'); PROJECTS_FILE=DATA_DIR/'projects.json'; PAGE_SIZE=5
QUAL=['Active','Suggested','Not evident']; BOOL=['True','False']

L1=[
('L1-01','Stakeholder awareness of sustainability goals','At project initiation, stakeholders communicate sustainability objectives with the client and team members, including relevant guidelines or standards, and discuss what is and is not feasible.',['notes','upload'],'qualitative',None,'desirable'),
('L1-02','Awareness of environmental, technical and social sustainability','Team members participate on a mandatory course or training on environmental, technical and social sustainability concepts.',['notes','upload'],'boolean',None,'required'),
('L1-03','Awareness of energy or resource implications','Team members discuss how builds, testing, deployments and infrastructure usage can have energy and resource implications.',['notes'],'qualitative_numeric','Number of sessions done','desirable'),
('L1-04','Awareness of technical debt impact','The team lead or Technical Architect provides guidance on how technical debt can affect maintainability, software longevity, development effort and long-term sustainability.',['notes'],'boolean',None,'desirable'),
('L1-05','Awareness of developer well-being and burnout risks','The manager communicates how workload, excessive overtime, repetitive activities, cognitive load and related factors may affect developer well-being and long-term productivity.',['notes'],'boolean',None,'required'),
('L1-06','Sustainability objectives discussed during planning','Sustainability objectives are explicitly discussed during project planning, including relevant environmental, technical and social concerns and their implications for project decisions.',['notes','upload'],'numeric','Number of sustainability categories/dimensions','desirable'),
('L1-07','Sustainability dimensions identified for the project','Relevant sustainability dimensions (environmental, technical, social and, where applicable, economic) are identified and recorded in the project dashboard.',['notes','upload'],'boolean',None,'desirable'),
('L1-08','Initial identification of DevOps tools supporting sustainability assessment','Teams actively review the capabilities of DevOps tools from a sustainability perspective.',['notes'],'qualitative',None,'optional'),
('L1-09','Awareness of existing tool capabilities and limitations','The team shares knowledge about build, testing and related tools, including their capabilities and limitations for sustainability.',['notes'],'boolean',None,'optional'),
]
L2=[
('L2-01','Sustainability skill acquired','Team member have done prior course or completed ones before design starts',['upload'],'qualitative',None,'required'),
('L2-02','Collaboration and knowledge-sharing practices','Team lead conducts exercises to build collective knowledge such as- given a set of competing features and observe what they prioritise.',['notes','upload'],'numeric','Number of sessions done','required'),
('L2-03','Awareness of accessibility and inclusivity','Team members use documented diverse personas/stakeholder groups and discussion of their needs (role-based sustainability concerns)',['notes','upload'],'qualitative_numeric','Number of role based sustainability goals identified', 'desirable'),
('L2-04','Sustainability as a parameter during backlog prioritization','Sustainability considerations are explicitly discussed and documented when prioritizing competing features or user stories. Relevant environmental, technical, and social impacts are considered alongside business and technical priorities.',['notes'], 'qualitative_numeric','Number of items or features resolved for sustainability impact','desirable'),
('L2-05','Reuse of CI/CD components encouraged','The team actively identifies existing CI/CD workflows, scripts, actions, configurations, and pipeline components rather than unnecessarily creating duplicate components.',['notes'], 'numeric','Number of reused components estimated','required'),
('L2-06','Burnout risks considered during planning','Sprint planning evaluates team workload and capacity against delivery demands at any instance k. Also identifies potential burnout risks, and adjusts task allocation or delivery commitments where excessive workload or overtime is identified.',['notes','upload'],'numeric','Estimated overtime hours','required'),
('L2-07','Knowledge sharing incorporated into workflows','Activities such as sprint planning, reviews, retrospectives, technical discussions, or workshops shared among team.',['notes'],'qualitative',None,'desirable'),
('L2-08','Tool support for reusable workflows','Planned pipeline integrates common CI/CD workflow components reducing unnecessary duplication of workflow configurations.',['notes'],'boolean',None,'desirable'),
('L2-09','Available IDE support for identifying inefficient code','IDE selected provides mechanisms such as static analysis, or plugins that can identify potentially inefficient or resource- intensive code during development',['notes'],'numeric','Number of sustainability categories/dimensions','optional'),
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

LEVELS={1:{'name':'Scope Definition','desc':'Sustainability is recognized as a project concern, but practices are largely ad hoc. Sustainability objectives and dimensions are not yet systematically defined.','indicators':L1},2:{'name':'Sustainability Awareness','desc':'Defined sustainability requirements and repeatable practices are embedded into CI/CD planning.','indicators':L2},3:{'name':'Measurement','desc':'The pipeline systematically tracks qualitative and quantitative sustainability metrics.','indicators':[]},4:{'name':'Optimization','desc':'Metric analytics are used to actively optimize resource usage and pipeline efficiency.','indicators':[]},5:{'name':'Autonomous Sustainability','desc':'AI models and predictive analytics support or automate sustainability-oriented pipeline optimization.','indicators':[]}}

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

</style>'''

def slug(x): return re.sub(r'[^a-z0-9]+','-',x.lower()).strip('-') or 'project'
def template(d):
    return {
        'id': d[0], 'title': d[1], 'description': d[2],
        'evidence': [], 'notes': '', 'date': None,
        'status': ('Not evident' if d[4]=='qualitative' else 'False' if d[4]=='boolean' else None),
        'numeric_value': None, 'requirement_type': d[6]
    }

def new_data(): return {str(n):{'indicators':[template(d) for d in lv['indicators']],'notes':'','complete':False} for n,lv in LEVELS.items()}
def load_projects():
    try:return json.loads(PROJECTS_FILE.read_text()) if PROJECTS_FILE.exists() else ['Example DevOps Project']
    except:return ['Example DevOps Project']
def save_projects(): PROJECTS_FILE.write_text(json.dumps(st.session_state.projects,indent=2))
def load_project(name):
    p=DATA_DIR/f'{slug(name)}.json'
    if not p.exists():
        return new_data()

    try:
        existing = json.loads(p.read_text())
    except:
        return new_data()

    # Migrate saved project data when new indicators are added to the
    # maturity model. Existing evidence/status/notes are preserved.
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

                # Preserve user-entered project data.
                indicator['evidence'] = saved.get('evidence', [])
                indicator['notes'] = saved.get('notes', '')
                indicator['date'] = saved.get('date')
                indicator['status'] = saved.get('status')
                indicator['numeric_value'] = saved.get('numeric_value')

                # Keep the current model's requirement classification.
                indicator['requirement_type'] = LEVELS[n]['indicators'][
                    next(
                        idx for idx, d in enumerate(LEVELS[n]['indicators'])
                        if d[0] == iid
                    )
                ][6]

        data[key]['notes'] = old_level.get('notes', '')
        data[key]['complete'] = old_level.get('complete', False)

    return data
def save_project(): (DATA_DIR/f'{slug(st.session_state.project)}.json').write_text(json.dumps(st.session_state.data,indent=2))
def init():
    DATA_DIR.mkdir(exist_ok=True); s=st.session_state
    s.setdefault('projects',load_projects()); s.setdefault('project',s.projects[0]); s.setdefault('page','dashboard'); s.setdefault('user','JD')
    if s.get('loaded_project')!=s.project:s.data=load_project(s.project);s.loaded_project=s.project
def lv(n):return st.session_state.data[str(n)]
def defs(n):return {d[0]:d for d in LEVELS[n]['indicators']}
def inds(n):return lv(n).get('indicators',[])
def satisfied(i,d):
    typ=d[4]
    if typ=='qualitative': return i.get('status')=='Active'
    if typ=='boolean': return i.get('status')=='True'
    if typ=='qualitative_numeric': return i.get('status')=='Active' and i.get('numeric_value') is not None and i.get('numeric_value')>0
    if typ=='numeric': return i.get('numeric_value') is not None and i.get('numeric_value')>0
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
    p=DATA_DIR/'evidence'/slug(st.session_state.project)/iid;p.mkdir(parents=True,exist_ok=True);return p/Path(fn).name

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
        st.markdown(f"**Observable condition:** {description}")

        # Hover over the lock to see the prerequisite information.
        st.markdown(
            f'<span title="Complete prerequisite indicator(s): {prereq_text}">'
            f'🔒 Locked — complete prerequisite indicator(s): {prereq_text}'
            f'</span>',
            unsafe_allow_html=True
        )



def indicator_card(n,i,d):
    iid=i['id']; key=f'{slug(st.session_state.project)}-{iid}'; typ=d[4]; requirement=d[6].title()

    unlocked, unresolved = precondition_status(iid)
    if not unlocked:
        render_locked_indicator(
            iid,
            i['title'],
            i['description'],
            requirement,
            unresolved
        )
        return

    # Use native Streamlit rendering for the indicator description.
    # This avoids literal HTML appearing in the UI.
    with st.container(border=True):
        st.markdown(f"**{iid}  {i['title']}**")
        st.caption(f"Type: {requirement}")
        st.markdown(f"**Observable condition:** {i['description']}")
    e,m=st.columns([1.5,1],gap='large')
    with e:
        st.markdown("<div class='label'>Evidence</div>",unsafe_allow_html=True)
        if 'notes' in d[3]:
            i['notes']=st.text_area('Notes',i.get('notes',''),key=key+'-notes',height=95,placeholder='Record the activity, discussion, decision, or observation...')
        if 'upload' in d[3]:
            files=st.file_uploader('Supporting document',accept_multiple_files=True,key=key+'-files')
            save_uploads(i,files)
            if i['evidence']:
                st.caption(f"📎 {len(i['evidence'])} supporting file(s) saved")
                for fn in i['evidence']:
                    p=evidence_path(iid,fn)
                    if p.exists():st.download_button(f'View/download {fn}',p.read_bytes(),file_name=fn,key=key+'-dl-'+slug(fn))
    with m:
        st.markdown("<div class='label'>Status / measurement</div>",unsafe_allow_html=True)
        if typ=='qualitative':
            cur=i.get('status') or 'Not evident';i['status']=st.selectbox('Status',QUAL,index=QUAL.index(cur),key=key+'-status')
        elif typ=='boolean':
            cur=i.get('status') or 'False';i['status']=st.selectbox('Status',BOOL,index=BOOL.index(cur),key=key+'-status')
        elif typ=='qualitative_numeric':
            cur=i.get('status') or 'Not evident';i['status']=st.selectbox('Qualitative status',QUAL,index=QUAL.index(cur),key=key+'-status')
            i['numeric_value']=st.number_input(d[5],min_value=0,step=1,value=0 if i.get('numeric_value') is None else int(i['numeric_value']),key=key+'-num')
        elif typ=='numeric':
            i['numeric_value']=st.number_input(d[5],min_value=0,step=1,value=0 if i.get('numeric_value') is None else int(i['numeric_value']),key=key+'-num')
    c1,c2=st.columns([1,1])
    with c1:
        cur=date.fromisoformat(i['date']) if i.get('date') else None
        x=st.date_input('Recorded date',value=cur,format='YYYY-MM-DD',key=key+'-date');i['date']=x.isoformat() if x else None
    with c2: st.caption('Changes are saved with “Save Draft”.')
    st.divider()

def indicators_tab(n):
    a=inds(n); ds=defs(n)
    if not a: st.info(f'Level {n} does not have indicators configured yet.');return
    st.subheader(f'Level {n} Indicators');st.caption('Evidence and assessment fields are defined separately for each indicator.')
    pages=max(1,ceil(len(a)/PAGE_SIZE));pk=f'pg-{n}';pg=min(st.session_state.get(pk,0),pages-1)
    for i in a[pg*PAGE_SIZE:(pg+1)*PAGE_SIZE]:indicator_card(n,i,ds[i['id']])
    lo=pg*PAGE_SIZE+1;hi=min((pg+1)*PAGE_SIZE,len(a));_,info,prev,nxt=st.columns([6,1.2,.5,.5]);info.caption(f'{lo}-{hi} of {len(a)}');prev.button('‹',disabled=pg==0,key=f'p-{n}',on_click=lambda:st.session_state.__setitem__(pk,pg-1));nxt.button('›',disabled=pg>=pages-1,key=f'n-{n}',on_click=lambda:st.session_state.__setitem__(pk,pg+1))
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
    x=LEVELS[n];st.markdown(f"<div class='banner'><div class='badge'>{n}</div><div style='flex:1'><h2>Level {n} – {x['name']}</h2><p>{x['desc']}</p></div><div class='tip'><b>💡 Evidence recording</b><br>Each indicator has its own evidence and assessment fields.<br><br>🔒 Indicators with unmet prerequisites remain locked.</div></div>",unsafe_allow_html=True)
    if lv(n)['complete']:st.success(f'Level {n} is marked complete.')
    a,b,c,d=st.tabs(['Indicators','Evidence Summary','Level Notes','Progress'])
    with a:indicators_tab(n)
    with b:evidence_tab(n)
    with c:lv(n).__setitem__('notes',st.text_area('Level notes',lv(n).get('notes',''),height=180,key=f'ln-{n}'))
    with d:progress_tab(n)
    st.divider();back,_,save,complete_btn=st.columns([1.3,4,1,1.6]);back.button('← Back to Overview',on_click=lambda:st.session_state.__setitem__('page','assessment'),use_container_width=True)
    if save.button('Save Draft',use_container_width=True):save_project();st.toast('Draft saved',icon='💾')
    #if lv(n)['complete']:
        #if complete_btn.button('Reopen Level',use_container_width=True):lv(n)['complete']=False;save_project();st.rerun()
    #elif complete_btn.button(f'Mark Level {n} as Complete',type='primary',use_container_width=True):
        #if t:=counts(n)[1]:
            #if counts(n)[0]==t:lv(n)['complete']=True;save_project();st.toast(f'Level {n} marked complete',icon='🎉');st.rerun()
            #else:st.warning(f'{t-counts(n)[0]} indicator(s) still require a valid assessment.')
def header():
    s=st.session_state;c1,c2,c3=st.columns([5,3,.6],vertical_alignment='center');c1.markdown("<div class='brand'>🌿 Sustainability Maturity Tool<br><span>Measure • Improve • Build a Greener DevOps</span></div>",unsafe_allow_html=True);c2.selectbox('Project',s.projects,key='project',on_change=lambda:None);c3.markdown(f"<div class='avatar'>{s.user}</div>",unsafe_allow_html=True);st.divider()
def sidebar():
    p=st.session_state.page;nav=[('dashboard','🏠 Dashboard'),('assessment','📊 Maturity Assessment')]+[(f'level-{n}',f'{n} · Level {n} – {x["name"]}') for n,x in LEVELS.items()]+[('reports','📄 Reports'),('settings','⚙️ Settings')]
    with st.sidebar:
        for k,label in nav:st.button(label,key='nav-'+k,use_container_width=True,on_click=lambda k=k:st.session_state.__setitem__('page',k),type='primary' if p==k else 'secondary')
        st.divider();st.caption('🌿 Smaller footprints. Stronger software.')
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
    desirable_optional_ratio = (
        desirable_optional_satisfied / len(desirable_optional)
        if desirable_optional
        else 0
    )

    sufficient_plus = (
        desirable_optional_ratio > 0.30
    )

    # Condition 3: at least 80% of all indicators.
    overall_ratio = all_satisfied / len(a)

    advanced = overall_ratio >= 0.80

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
    """Render one horizontal three-section maturity progress bar."""
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
            return "green"
        if partial:
            return "yellow"
        return "red"

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
        all_satisfied > 0 and all_satisfied / all_total < 0.80
        if all_total else False
    )

    colours = {
        "red": "#f8d7da",
        "yellow": "#fff3cd",
        "green": "#d1e7dd",
    }

    segments = [
        (
            "Sufficient",
            sufficient_colour,
            f"{required_satisfied}/{required_total} required",
        ),
        (
            "Sufficient+",
            sufficient_plus_colour,
            f"{dopt_satisfied}/{dopt_total} desirable + optional",
        ),
        (
            "Advanced",
            advanced_colour,
            f"{all_satisfied}/{all_total} indicators",
        ),
    ]

    segment_html = "".join(
        f"""
        <div style="
            flex:1;
            background:{colours[colour]};
            padding:12px 14px;
            min-height:82px;
            border-right:1px solid #d9d9d9;
        ">
            <div style="font-weight:700;margin-bottom:6px;">{title}</div>
            <div style="font-size:13px;">{detail}</div>
        </div>
        """
        for title, colour, detail in segments
    )

    st.markdown(
        f"""
        <div style="
            display:flex;
            width:100%;
            overflow:hidden;
            border:1px solid #d9d9d9;
            border-radius:8px;
            margin-top:8px;
        ">
            {segment_html}
        </div>
        """,
        unsafe_allow_html=True,
    )



def dashboard():
    st.subheader('Dashboard')

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
        f"Level {reached}"
        if reached
        else "Not yet at Level 1",
    )

    m2.metric(
        "Indicators satisfied",
        f"{all_done} / {all_total}",
    )

    m3.metric(
        "Next level",
        (
            f"Level {reached + 1}"
            if reached < len(LEVELS)
            else "All levels done"
        ),
    )

    st.divider()
    st.subheader("Level progress conditions")
    st.caption(
        "Each level progresses through three conditions: Sufficient, "
        "Sufficient+, and Advanced."
    )

    for n, lv in LEVELS.items():
        if not inds(n):
            continue

        with st.container(border=True):
            st.markdown(
                f"**Level {n} – {lv['name']}**"
            )
            dashboard_progress_bar(n)


    st.divider()

    #for col, (n, lv) in zip(
        #st.columns(len(LEVELS)),
        #LEVELS.items(),
    #):
        #with col.container(border=True):
            #st.markdown(f"**Level {n}**")
            #st.caption(lv['name'])

            #st.button(
                #"Open",
                #key=f"open-{n}",
                #use_container_width=True,
                #on_click=go,
                #args=(f"level-{n}",),
            #)


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
    rows=[]
    for n,x in LEVELS.items():
        d,t=counts(n); rows.append({'Level':n,'Name':x['name'],'Satisfied':f'{d}/{t}','Progress %':round(100*d/t) if t else 0,'Status':status(n)})
    st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
    active_levels=[n for n in LEVELS if inds(n)]
    if active_levels:
        st.divider(); st.subheader('Satisfied indicators by requirement type')
        for n in active_levels: requirement_type_chart(n)

def reports():
    st.subheader('Reports');rows=[]
    for n,x in LEVELS.items():
        ds=defs(n)
        for i in inds(n):rows.append({'Level':n,'Requirement type':ds[i['id']][6].title(),'Indicator ID':i['id'],'Indicator':i['title'],'Measurement type':ds[i['id']][4],'Status':i.get('status'),'Numeric value':i.get('numeric_value'),'Satisfied':satisfied(i,ds[i['id']]),'Notes':i.get('notes'),'Date':i.get('date'),'Evidence files':'; '.join(i.get('evidence',[]))})
    df=pd.DataFrame(rows);st.dataframe(df,hide_index=True,use_container_width=True);stem=slug(st.session_state.project);c1,c2=st.columns(2);c1.download_button('Download CSV',df.to_csv(index=False),f'{stem}-assessment.csv','text/csv');c2.download_button('Download JSON',json.dumps(st.session_state.data,indent=2),f'{stem}-assessment.json','application/json')
def settings():
    s=st.session_state;st.subheader('Settings');s.user=st.text_input('Your initials',s.user,max_chars=3).upper();name=st.text_input('New project',placeholder='e.g. Payments platform')
    if st.button('Add project'):
        if name.strip() and name.strip() not in s.projects:s.projects.append(name.strip());save_projects();st.success(f'Added {name.strip()}')
        else:st.error('Enter a new project name.')

init();st.markdown(CSS,unsafe_allow_html=True);header();sidebar();p=st.session_state.page
if p.startswith('level-'):level_page(int(p.split('-')[1]))
elif p=='assessment':assessment()
elif p=='reports':reports()
elif p=='settings':settings()
else:dashboard()
