from flask import Flask, render_template, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
from src.engine import extract_upload, answer_question, make_summary
from io import BytesIO, StringIO
import csv, json, os, uuid, datetime, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
app=Flask(__name__); app.secret_key=os.environ.get('SECRET_KEY','loreforge-local-development-key-change-me')
app.config['MAX_CONTENT_LENGTH']=30*1024*1024
ALLOWED={'pdf','pptx','docx','txt'}
# Single-process in-memory workspace, appropriate for local/demo use. Production multi-worker storage needs a database.
WORKSPACES={}
def workspace():
    sid=session.get('sid')
    if not sid: sid=uuid.uuid4().hex; session['sid']=sid
    return WORKSPACES.setdefault(sid,{'units':[],'documents':[],'history':[]})
def err(msg,code=400): return jsonify({'ok':False,'error':msg}),code

def enrich_with_explicit_rules(question, result, units):
    """Apply the assignment's explicit domain rules when their source patterns exist."""
    try:
        from knowledge_base import build_knowledge_base
        from reasoning_engine import process_with_reasoning
        source='\n'.join(u['text'] for u in units)
        kb=build_knowledge_base(source)
        if not kb: return result
        rule_answer=process_with_reasoning(question,kb)
        if rule_answer and 'could not be identified' not in rule_answer.lower():
            result['answer']=rule_answer
            result['trace'].append('Applied the explicit domain-specific rule set extracted into the structured knowledge base.')
            result['trace'].append('Rule output is limited to facts and conditions detected in the uploaded source.')
            result['intent']='rule_based_reasoning'
        return result
    except Exception:
        return result
@app.get('/')
def home(): return render_template('index.html')
@app.get('/api/status')
def status():
    w=workspace(); return jsonify(ok=True,documents=w['documents'],unit_count=len(w['units']),history_count=len(w['history']))
@app.post('/api/upload')
def upload():
    w=workspace(); files=request.files.getlist('files') or ([request.files['file']] if 'file' in request.files else [])
    if not files: return err('Choose at least one document.')
    added=[]; failures=[]
    for f in files:
        if not f.filename: continue
        name=secure_filename(f.filename); ext=name.rsplit('.',1)[-1].lower() if '.' in name else ''
        if ext not in ALLOWED: failures.append({'filename':name,'error':'Unsupported format.'}); continue
        try:
            units,meta=extract_upload(f,name); meta['id']=uuid.uuid4().hex[:10]; meta['uploaded_at']=datetime.datetime.now().isoformat(timespec='seconds')
            for unit in units: unit['document_id']=meta['id']
            w['units'].extend(units); w['documents'].append(meta); added.append(meta)
        except Exception as e: failures.append({'filename':name,'error':str(e)})
    if not added: return jsonify(ok=False,error='No files were processed.',failures=failures),400
    return jsonify(ok=True,added=added,failures=failures,unit_count=len(w['units']),message=f'Processed {len(added)} document(s) into {sum(x["units"] for x in added)} knowledge units.')
@app.post('/api/ask')
def ask():
    w=workspace(); q=(request.get_json(silent=True) or {}).get('question','').strip()
    if not q: return err('Enter a question.')
    if not w['units']: return err('Upload a document before asking questions.')
    previous_question=next((h.get('question') for h in reversed(w['history']) if h.get('question')),None)
    result=enrich_with_explicit_rules(q,answer_question(q,w['units'],previous_question=previous_question),w['units']); result['question']=q; result['created_at']=datetime.datetime.now().isoformat(timespec='seconds')
    w['history'].append(result); return jsonify(ok=True,**result)
@app.post('/api/batch')
def batch():
    w=workspace(); data=request.get_json(silent=True) or {}; qs=data.get('questions',[])
    if not w['units']: return err('Upload a document first.')
    if isinstance(qs,str): qs=[x.strip() for x in qs.splitlines() if x.strip()]
    if not qs: return err('Provide one or more questions.')
    results=[]
    for q in qs[:50]:
        r=enrich_with_explicit_rules(str(q),answer_question(str(q),w['units']),w['units']); r['question']=str(q); results.append(r); w['history'].append(r)
    return jsonify(ok=True,results=results)
@app.get('/api/facts')
def facts():
    w=workspace(); q=request.args.get('q','').lower(); limit=min(500,max(1,int(request.args.get('limit',200))))
    data=[{'text':u['text'],'source':u['source'],'page':u.get('page'),'slide':u.get('slide'),'terms':u['terms']} for u in w['units'] if not q or q in u['text'].lower() or q in u['source'].lower()]
    return jsonify(ok=True,total=len(data),facts=data[:limit])
@app.post('/api/evaluate')
def evaluate():
    """Lightweight lexical coverage check; not a semantic accuracy metric."""
    w=workspace(); data=request.get_json(silent=True) or {}; cases=data.get('cases',[])
    if not w['units']: return err('Upload a document before evaluation.')
    if not cases: return err('Provide evaluation cases with question and expected_terms.')
    rows=[]
    from src.engine import tokens
    for case in cases[:100]:
        question=str(case.get('question','')).strip(); expected=[str(x).lower() for x in case.get('expected_terms',[])]
        result=answer_question(question,w['units'])
        answer=result['answer'].lower()
        found=[term for term in expected if term in answer]
        coverage=(len(found)/len(expected)*100) if expected else None
        rows.append({'question':question,'status':result['status'],'expected_terms':expected,'found_terms':found,'coverage':round(coverage,1) if coverage is not None else None,'evidence_count':len(result['evidence'])})
    measured=[r['coverage'] for r in rows if r['coverage'] is not None]
    return jsonify(ok=True,warning='Lexical expected-term coverage is not semantic correctness or model accuracy.',cases=rows,mean_expected_term_coverage=round(sum(measured)/len(measured),1) if measured else None,total_cases=len(rows))

@app.get('/api/health')
def health(): return jsonify(ok=True,service='LoreForge Classical AI',engine='deterministic lexical reasoning')

@app.get('/api/summary')
def summary():
    w=workspace()
    if not w['units']: return err('Upload a document first.')
    return jsonify(ok=True,summary=make_summary(w['units']))
@app.delete('/api/document/<docid>')
def delete_document(docid):
    w=workspace(); docs=[d for d in w['documents'] if d['id']==docid]
    if not docs: return err('Document not found.',404)
    w['documents']=[d for d in w['documents'] if d['id']!=docid]; w['units']=[u for u in w['units'] if u.get('document_id')!=docid]
    return jsonify(ok=True,unit_count=len(w['units']))
@app.post('/api/clear')
def clear():
    w=workspace(); w.update(units=[],documents=[],history=[]); return jsonify(ok=True)
@app.get('/api/export/<kind>')
def export(kind):
    w=workspace(); kind=kind.lower()
    if kind=='csv':
        out=StringIO(); writer=csv.writer(out); writer.writerow(['Question','Answer','Status','Evidence source','Page','Slide','Evidence score'])
        for h in w['history']:
            for e in h.get('evidence',[]) or [{}]: writer.writerow([h.get('question',''),h.get('answer',''),h.get('status',''),e.get('source',''),e.get('page',''),e.get('slide',''),e.get('score','')])
        b=BytesIO(out.getvalue().encode('utf-8-sig')); return send_file(b,as_attachment=True,download_name='loreforge_conversation.csv',mimetype='text/csv')
    if kind=='txt':
        content='LOREFORGE ANSWER HISTORY\n'+'='*60+'\n\n'
        for h in w['history']:
            content+=f'QUESTION: {h.get("question")}\nANSWER:\n{h.get("answer")}\n\nEVIDENCE:\n'
            for e in h.get('evidence',[]): content+=f'- {e["source"]} | page {e.get("page")} | slide {e.get("slide")} | {e["text"]}\n'
            content+='\n'+'-'*60+'\n'
        return send_file(BytesIO(content.encode()),as_attachment=True,download_name='loreforge_answers.txt',mimetype='text/plain')
    if kind=='docx':
        from docx import Document
        d=Document(); d.add_heading('LoreForge · Answer Report',0); d.add_paragraph('Classical AI · Evidence-grounded output')
        for h in w['history']:
            d.add_heading(h.get('question','Question'),2); d.add_paragraph(h.get('answer',''))
            if h.get('evidence'):
                d.add_heading('Source evidence',3)
                for e in h['evidence']: d.add_paragraph(f"{e['source']} | page {e.get('page')} | slide {e.get('slide')} | {e['text']}",style='List Bullet')
        b=BytesIO(); d.save(b); b.seek(0); return send_file(b,as_attachment=True,download_name='loreforge_report.docx',mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    if kind=='pdf':
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import mm
        b=BytesIO(); styles=getSampleStyleSheet(); story=[Paragraph('LoreForge · Answer Report',styles['Title']),Spacer(1,6*mm)]
        for h in w['history']:
            story += [Paragraph(h.get('question','Question').replace('&','&amp;'),styles['Heading2']),Paragraph(h.get('answer','').replace('&','&amp;').replace('\n','<br/>'),styles['BodyText']),Spacer(1,4*mm)]
            for e in h.get('evidence',[]): story.append(Paragraph(f"Source: {e['source']} | page {e.get('page')} | slide {e.get('slide')}<br/>{e['text']}",styles['Italic']))
            story.append(Spacer(1,5*mm))
        SimpleDocTemplate(b,pagesize=A4,rightMargin=18*mm,leftMargin=18*mm).build(story); b.seek(0)
        return send_file(b,as_attachment=True,download_name='loreforge_report.pdf',mimetype='application/pdf')
    return err('Supported exports: csv, txt, docx, pdf.')
@app.errorhandler(413)
def too_large(e): return err('Upload too large. Maximum total request size is 30 MB.',413)
if __name__=='__main__': app.run(debug=True,port=5000)
