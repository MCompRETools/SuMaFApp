import json, re
from pathlib import Path
from datetime import date
from math import ceil
import pandas as pd
import streamlit as st

st.set_page_config(page_title='Sustainability Maturity Tool', page_icon='🌿', layout='wide')
DATA_DIR=Path('data'); PROJECTS_FILE=DATA_DIR/'projects.json'; PAGE_SIZE=5
QUAL=['Active','Suggested','Not evident']; BOOL=['True','False']

L1=[
('L1-01','Stakeholder awareness of sustainability goals','At project initiation, stakeholders communicate sustainability objectives with the client and team members, including relevant guidelines or standards, and discuss what is and is not feasible.',['notes','upload'],'qualitative',None,'desirable'),
('L1-02','Awareness of environmental, technical and social sustainability','Team members complete a mandatory course or training on environmental, technical and social sustainability concepts.',['upload'],'boolean',None,'required'),
('L1-03','Awareness of energy or resource implications','Team members discuss how builds, testing, deployments and infrastructure usage can have energy and resource implications.',['notes'],'qualitative_numeric','Number of sessions done','desirable'),
('L1-04','Awareness of technical debt impact','The team lead or Technical Architect provides guidance on how technical debt can affect maintainability, software longevity, development effort and long-term sustainability.',['notes'],'boolean',None,'desirable'),
('L1-05','Awareness of developer well-being and burnout risks','The manager communicates how workload, excessive overtime, repetitive activities, cognitive load and related factors may affect developer well-being and long-term productivity.',['notes'],'boolean',None,'required'),
('L1-06','Sustainability objectives discussed during planning','Sustainability objectives are explicitly discussed during project planning, including relevant environmental, technical and social concerns and their implications for project decisions.',['notes','upload'],'numeric','Number of sustainability categories/dimensions','desirable'),
('L1-07','Sustainability dimensions identified for the project','Relevant sustainability dimensions (environmental, technical, social and, where applicable, economic) are identified and recorded in the project dashboard.',['notes','upload'],'boolean',None,'desirable'),
('L1-08','Initial identification of DevOps tools supporting sustainability assessment','Teams actively review the capabilities of DevOps tools from a sustainability perspective.',['notes'],'qualitative',None,'optional'),
('L1-09','Awareness of existing tool capabilities and limitations','The team shares knowledge about build, testing and related tools, including their capabilities and limitations for sustainability.',['notes'],'boolean',None,'optional'),
]

LEVELS={1:{'name':'Scope Definition','desc':'Sustainability is recognized as a project concern, but practices are largely ad hoc. Sustainability objectives and dimensions are not yet systematically defined.','indicators':L1},2:{'name':'Sustainability Awareness','desc':'Defined sustainability requirements and repeatable practices are embedded into CI/CD planning.','indicators':[]},3:{'name':'Measurement','desc':'The pipeline systematically tracks qualitative and quantitative sustainability metrics.','indicators':[]},4:{'name':'Optimization','desc':'Metric analytics are used to actively optimize resource usage and pipeline efficiency.','indicators':[]},5:{'name':'Autonomous Sustainability','desc':'AI models and predictive analytics support or automate sustainability-oriented pipeline optimization.','indicators':[]}}

CSS='''<style>
:root{--g:#1f7a4d;--gl:#e6f2ea;--gb:#cfe5d6}
[data-testid="stSidebar"]{background:#f4f8f5}.brand{font-size:22px;font-weight:600;line-height:1.2}.brand span{font-size:13px;font-weight:400;color:#5b6b62}.avatar{width:40px;height:40px;border-radius:50%;background:#8a9a91;color:white;display:flex;align-items:center;justify-content:center;font-weight:600;margin-left:auto}.banner{display:flex;gap:20px;align-items:center;background:var(--gl);border:1px solid var(--gb);border-radius:12px;padding:20px 24px;margin-bottom:12px}.banner h2{margin:0 0 4px;color:#14532d}.banner p{margin:0;color:#3d4a43}.badge{min-width:60px;height:60px;border-radius:50%;background:var(--g);color:white;font-size:28px;font-weight:600;display:flex;align-items:center;justify-content:center}.tip{background:white;border:1px solid var(--gb);border-radius:10px;padding:12px 16px;min-width:260px;max-width:360px;font-size:13px;color:#3d4a43}.card{border:1px solid #dfe7e2;border-radius:12px;padding:18px;margin-bottom:14px;background:#fff}.title{font-weight:650;font-size:16px;color:#26352e}.id{color:var(--g);font-weight:700;margin-right:8px}.obs{color:#4b5a52;font-size:14px;line-height:1.45;margin-top:6px}.label{font-weight:600;color:#33413a;margin-bottom:4px}.hint{color:#68776f;font-size:12px}[data-testid="stBaseButton-primary"]{background:var(--g);border-color:var(--g)}
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
    if not p.exists():return new_data()
    try:x=json.loads(p.read_text()); return x if 'indicators' in x.get('1',{}) else new_data()
    except:return new_data()
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

def indicator_card(n,i,d):
    iid=i['id']; key=f'{slug(st.session_state.project)}-{iid}'; typ=d[4]; requirement=d[6].title()
    st.markdown(f"<div class='card'><div class='title'><span class='id'>{iid}</span>{i['title']}</div><div class='obs'><b>Type:</b> {requirement}<br><b>Observable condition:</b> {i['description']}</div></div>",unsafe_allow_html=True)
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
    for i in a:rows.append({'ID':i['id'],'Indicator':i['title'],'Status':i.get('status'),'Numeric value':i.get('numeric_value'),'Notes':bool(i.get('notes')),'Documents':len(i.get('evidence',[])),'Complete':complete(i,ds[i['id']])})
    st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
def level_page(n):
    x=LEVELS[n];st.markdown(f"<div class='banner'><div class='badge'>{n}</div><div style='flex:1'><h2>Level {n} – {x['name']}</h2><p>{x['desc']}</p></div><div class='tip'><b>💡 Evidence recording</b><br>Each indicator has its own evidence and assessment fields.</div></div>",unsafe_allow_html=True)
    if lv(n)['complete']:st.success(f'Level {n} is marked complete.')
    a,b,c,d=st.tabs(['Indicators','Evidence Summary','Level Notes','Progress'])
    with a:indicators_tab(n)
    with b:evidence_tab(n)
    with c:lv(n).__setitem__('notes',st.text_area('Level notes',lv(n).get('notes',''),height=180,key=f'ln-{n}'))
    with d:progress_tab(n)
    st.divider();back,_,save,complete_btn=st.columns([1.3,4,1,1.6]);back.button('← Back to Overview',on_click=lambda:st.session_state.__setitem__('page','assessment'),use_container_width=True)
    if save.button('Save Draft',use_container_width=True):save_project();st.toast('Draft saved',icon='💾')
    if lv(n)['complete']:
        if complete_btn.button('Reopen Level',use_container_width=True):lv(n)['complete']=False;save_project();st.rerun()
    elif complete_btn.button(f'Mark Level {n} as Complete',type='primary',use_container_width=True):
        if t:=counts(n)[1]:
            if counts(n)[0]==t:lv(n)['complete']=True;save_project();st.toast(f'Level {n} marked complete',icon='🎉');st.rerun()
            else:st.warning(f'{t-counts(n)[0]} indicator(s) still require a valid assessment.')
def header():
    s=st.session_state;c1,c2,c3=st.columns([5,3,.6],vertical_alignment='center');c1.markdown("<div class='brand'>🌿 Sustainability Maturity Tool<br><span>Measure • Improve • Build a Greener DevOps</span></div>",unsafe_allow_html=True);c2.selectbox('Project',s.projects,key='project',on_change=lambda:None);c3.markdown(f"<div class='avatar'>{s.user}</div>",unsafe_allow_html=True);st.divider()
def sidebar():
    p=st.session_state.page;nav=[('dashboard','🏠 Dashboard'),('assessment','📊 Maturity Assessment')]+[(f'level-{n}',f'{n} · Level {n} – {x["name"]}') for n,x in LEVELS.items()]+[('reports','📄 Reports'),('settings','⚙️ Settings')]
    with st.sidebar:
        for k,label in nav:st.button(label,key='nav-'+k,use_container_width=True,on_click=lambda k=k:st.session_state.__setitem__('page',k),type='primary' if p==k else 'secondary')
        st.divider();st.caption('🌿 Smaller footprints. Stronger software.')
def dashboard():
    st.subheader('Dashboard');r=achieved();done=sum(counts(n)[0] for n in LEVELS);tot=sum(counts(n)[1] for n in LEVELS);c1,c2,c3=st.columns(3);c1.metric('Current maturity level',f'Level {r}' if r else 'Not yet at Level 1');c2.metric('Indicators assessed',f'{done}/{tot}');c3.metric('Next level',f'Level {r+1}' if r<5 else 'All levels done');st.progress(done/tot if tot else 0)
def requirement_type_chart(n):
    """Show percentage of indicators satisfied within each requirement type."""
    a = inds(n)
    if not a:
        return

    ds = defs(n)
    order = ['Required', 'Desirable', 'Optional']

    totals = {x: 0 for x in order}
    satisfied_counts = {x: 0 for x in order}

    for i in a:
        d = ds[i['id']]
        requirement_type = d[6].title()
        totals[requirement_type] += 1

        if satisfied(i, d):
            satisfied_counts[requirement_type] += 1

    percentages = {
        x: (
            round(100 * satisfied_counts[x] / totals[x], 1)
            if totals[x] else 0
        )
        for x in order
    }

    chart_df = pd.DataFrame({
        'Requirement type': order,
        'Achieved (%)': [percentages[x] for x in order],
    }).set_index('Requirement type')

    st.markdown(
        f"#### Level {n} – {LEVELS[n]['name']}: achievement by indicator type"
    )
    st.caption(
        "Percentage of indicators satisfied within each requirement type. "
        "The denominator is the total number of indicators of that type."
    )

    # Use only arguments supported across current Streamlit versions.
    # The percentages are inherently bounded between 0 and 100.
    st.bar_chart(
        chart_df,
        y='Achieved (%)',
        use_container_width=True,
    )

    summary = pd.DataFrame({
        'Requirement type': order,
        'Achieved': [
            f"{satisfied_counts[x]} / {totals[x]}"
            for x in order
        ],
        'Achievement (%)': [
            percentages[x]
            for x in order
        ],
    })

    st.dataframe(
        summary,
        hide_index=True,
        use_container_width=True,
    )


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
