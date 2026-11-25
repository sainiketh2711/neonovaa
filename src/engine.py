"""LOREFORGE: transparent classical-AI document understanding.
Deterministic rules, lexical evidence ranking, source grouping and extractive synthesis.
No LLM, embeddings, vector database, RAG or prohibited NLP pipeline is used.
"""
from __future__ import annotations
import re, math
from collections import Counter, defaultdict

STOP=set('''what which who whom whose where when why how is are was were be been being do does did can could would should may might will shall the a an and or of to in on for from with about tell me please this that it these those according document documents file text explain describe give list show find state define compare difference between versus by as at into than then there their they them he she we you your i our its has have had not no yes if whether while after before during also such more most less many much overview topic topics chapter section main key briefly'''.split())
ALIASES={
 'borrow':['loan','issue','checkout'],'loans':['borrow','borrowing'],'maximum':['max','limit','upto'],'minimum':['min','least'],
 'cost':['price','fee','charge','fine','expense'],'duration':['time','period','length'],'advantages':['benefits','pros','strengths'],
 'disadvantages':['limitations','limitation','drawbacks','drawback','cons','weaknesses','weakness'],'limitation':['limitations','disadvantage','drawback','weakness'],'advantage':['advantages','benefit','benefits','pro'],'purpose':['aim','objective','goal'],'method':['approach','technique','procedure'],
 'result':['outcome','finding','effect'],'requirement':['need','specification','criteria'],'staff':['employee','personnel'],
 'student':['students','learner','learners'],'faculty':['teacher','professor','lecturer'],'weekend':['saturday','sunday'],
 'weekday':['monday','tuesday','wednesday','thursday','friday'],'issue':['problem','complaint','fault','incident'],'resolve':['fix','repair','solve'],
 'submit':['report','raise','create','file'],'explain':['describe','clarify','elaborate'],'important':['key','major','significant','essential'],
 'overview':['summary','outline','introduction'],'process':['workflow','steps','procedure'],'component':['part','element','module'],
 'types':['kinds','categories','classes'],'features':['characteristics','properties','attributes'],'working':['operation','functioning','mechanism'],
 'use':['application','usage','purpose'],'pca':['principal','component','analysis'],'ai':['artificial','intelligence'],'ml':['machine','learning'],'cnn':['convolutional','neural','network'],'rnn':['recurrent','neural','network'],'svm':['support','vector','machine'],'nn':['neural','network']}

def tokens(text):
    raw=re.findall(r"[a-zA-Z]+(?:'[a-z]+)?|\d+(?:\.\d+)?|₹",str(text).lower()); out=[]
    for w in raw:
        if w in STOP or (len(w)<2 and not w.isdigit()): continue
        out.append(w)
        for k,vals in ALIASES.items():
            if w==k or w in vals: out.extend([k]+vals[:2]); break
    return out

def split_units(text,filename,page=None,slide=None):
    units=[]
    for line_no,line in enumerate(str(text).replace('\r','\n').split('\n'),1):
        line=re.sub(r'\s+',' ',line).strip()
        if not line: continue
        for part in re.split(r'(?<=[.!?;])\s+(?=[A-Z0-9₹(])',line):
            part=part.strip(' •\t-')
            if len(part)<5: continue
            units.append({'text':part,'source':filename,'page':page,'slide':slide,'line':line_no,'terms':tokens(part),'length':len(part)})
    return units

def extract_upload(file,filename):
    ext=filename.rsplit('.',1)[-1].lower(); units=[]; chars=0; pages=0
    if ext=='txt':
        text=file.read().decode('utf-8-sig',errors='replace'); pages=1; units+=split_units(text,filename,page=1); chars=len(text)
    elif ext=='pdf':
        from pypdf import PdfReader
        reader=PdfReader(file); pages=len(reader.pages)
        for i,p in enumerate(reader.pages,1):
            text=p.extract_text() or ''; chars+=len(text); units+=split_units(text,filename,page=i)
    elif ext=='docx':
        from docx import Document
        doc=Document(file); pages=1; chunks=[p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows: chunks.append(' | '.join(c.text.strip() for c in row.cells))
        text='\n'.join(chunks); chars=len(text); units+=split_units(text,filename,page=1)
    elif ext=='pptx':
        from pptx import Presentation
        prs=Presentation(file); pages=len(prs.slides)
        for i,slide in enumerate(prs.slides,1):
            chunks=[]
            for shape in slide.shapes:
                if getattr(shape,'has_text_frame',False) and shape.text.strip(): chunks.append(shape.text.strip())
                if getattr(shape,'has_table',False):
                    for row in shape.table.rows: chunks.append(' | '.join(c.text for c in row.cells))
            text='\n'.join(chunks); chars+=len(text); units+=split_units(text,filename,slide=i)
    else: raise ValueError('Unsupported format. Use PDF, PPTX, DOCX or TXT.')
    if not units: raise ValueError('No extractable text found. Scanned/image-only PDFs and image-only slides need OCR, which this assignment version does not include.')
    return units,{'filename':filename,'format':ext.upper(),'pages_or_slides':pages,'characters':chars,'units':len(units)}

def expand_query(question):
    base=tokens(question); expanded=list(base)
    for w in base:
        for key,vals in ALIASES.items():
            if w==key or w in vals: expanded.extend([key]+vals)
    return expanded

def rank(question,units):
    qset=set(expand_query(question))
    if not qset: return []
    N=max(1,len(units)); df=Counter()
    for u in units: df.update(set(u['terms']))
    ranked=[]
    for idx,u in enumerate(units):
        tset=set(u['terms']); overlap=qset&tset
        if not overlap: continue
        weighted=sum(math.log(1+(N/(1+df[w]))) for w in overlap)/max(1e-9,sum(math.log(1+(N/(1+df[w]))) for w in qset))
        coverage=len(overlap)/max(1,len(qset)); density=len(overlap)/max(1,len(tset))
        phrase=1.0 if len(question.strip())>5 and question.lower().strip('? .') in u['text'].lower() else 0.0
        substance=min(1.0,len(u['text'])/150)
        score=min(1.0,.52*weighted+.25*coverage+.10*min(1,density*4)+.08*phrase+.05*substance)
        ranked.append((score,u,sorted(overlap),idx))
    ranked.sort(key=lambda x:(x[0],len(x[2]),-x[1]['length']),reverse=True)
    return ranked

def detect_intent(q):
    q=q.lower().strip()
    if any(x in q for x in ['what is this document about','what is the document about','what does this document cover','what is this about','overview','summarize','summarise','summary','key points','main points','give me an outline']): return 'overview'
    if any(x in q for x in ['compare','difference','versus',' vs ']): return 'comparison'
    if any(x in q for x in ['list all','all the','enumerate','list the','what are the types','what are the features','what are the advantages','what are the disadvantages','what are the limitations','what are the key concepts','key concepts']): return 'list'
    if any(x in q for x in ['how many','total number','count of']): return 'count'
    if any(x in q for x in ['calculate','compute','how much','total cost','fine for']): return 'calculation'
    if any(x in q for x in ['explain','describe','elaborate','teach me','how does','how do','what is','define','meaning of']): return 'explanation'
    return 'question'

def _rank_overview(units):
    """Select representative statements using whole-document term recurrence."""
    freq=Counter(w for u in units for w in set(u['terms']))
    ranked=[]
    for idx,u in enumerate(units):
        terms=set(u['terms'])
        if not terms: continue
        # Recurring document vocabulary indicates central themes; sentence length is capped.
        score=sum(math.log1p(freq[w]) for w in terms)/max(1,math.sqrt(len(terms)))
        score *= min(1.0, len(u['text'])/90)
        ranked.append((score,u,sorted(terms),idx))
    ranked.sort(key=lambda x:x[0],reverse=True)
    if not ranked: return []
    peak=ranked[0][0] or 1
    return [(score/peak,u,m,idx) for score,u,m,idx in ranked]

def _select_evidence(ranked,max_evidence=8,threshold=.075):
    chosen=[]; seen=set(); seen_pages=set()
    for score,u,matched,idx in ranked:
        if score<threshold: continue
        key=re.sub(r'\W+',' ',u['text'].lower())
        if key in seen: continue
        loc=(u.get('source'),u.get('page'),u.get('slide'))
        adjusted=score+(.025 if loc not in seen_pages else 0)
        chosen.append((adjusted,u,matched,idx)); seen.add(key); seen_pages.add(loc)
        if len(chosen)>=max_evidence: break
    return chosen

PLAIN_LANGUAGE_RULES = [
    (r'\bdimensionality reduction technique\b', 'method for reducing the number of features or variables'),
    (r'\bdimensionality reduction\b', 'reducing the number of features or variables'),
    (r'\blabelled training data\b', 'examples that already include the correct answers'),
    (r'\bunlabelled data\b', 'data without predefined answers'),
    (r'\bmethod for reducing the number of features or variables used to reduce the number of features\b', 'method that reduces the number of features'),
    (r'\bpreserving important information\b', 'keeping the most useful information'),
    (r'\bcorrelated variables\b', 'variables that are related to one another'),
    (r'\bprincipal components\b', 'new combined features'),
]

def plain_language(text):
    """Apply a small, explicit glossary of safe phrase substitutions."""
    result=text
    for pattern,replacement in PLAIN_LANGUAGE_RULES:
        result=re.sub(pattern,replacement,result,flags=re.I)
    return result

def _topic_label(question):
    q=re.sub(r'^(please\s+)?(explain|describe|elaborate on|teach me about|what is|define)\s+','',question.strip(),flags=re.I)
    return re.sub(r'\?+$','',q).strip() or 'the requested topic'

def _evidence_objects(items):
    return [{'text':u['text'],'source':u['source'],'page':u.get('page'),'slide':u.get('slide'),'score':round(min(1,s)*100,1),'matched_terms':m} for s,u,m,_ in items]

def answer_question(question,units,max_evidence=8,previous_question=None):
    intent=detect_intent(question); q_for_search=question
    if intent=='overview': q_for_search='purpose objective concept process method result finding feature requirement advantage limitation introduction chapter topic'
    pronoun=bool(re.search(r'\b(it|its|they|them|that|those|these|there|this|their)\b',question.lower()))
    if previous_question and (len(tokens(question))<=5 or pronoun): q_for_search=f'{previous_question} {question}'
    ranked=_rank_overview(units) if intent=='overview' else rank(q_for_search,units)
    chosen=_select_evidence(ranked,max_evidence=max(max_evidence,10) if intent=='overview' else max_evidence,threshold=.025 if intent=='overview' else (.065 if intent=='explanation' else .075))
    if not chosen:
        return {'answer':"I couldn't find enough relevant evidence in the uploaded sources to answer that reliably. Try naming the topic or using a related term from the document. If the source is scanned or image-only, its text may not have been extracted.",'status':'not_found','intent':intent,'evidence':[],'trace':['Question classified using explicit intent rules.',f'Expanded query terms: {", ".join(expand_query(q_for_search)) or "none"}.','No candidate knowledge unit met the evidence threshold.','The system avoided inventing an answer.'],'confidence':0.0}
    if intent=='overview':
        selected=chosen[:min(10,len(chosen))]; ideas=[]
        for _,u,_,_ in selected:
            if u['text'] not in ideas: ideas.append(u['text'])
        files=sorted({u['source'] for _,u,_,_ in selected})
        answer=(f"This workspace contains {len({u['source'] for u in units})} uploaded document(s). Based on the strongest recurring information, the document is mainly about the subjects represented below. This overview is assembled from extracted source statements and may not capture visual-only content.\n\nMAIN IDEAS\n"+'\n'.join('• '+x for x in ideas[:8])+'\n\nSOURCES\n'+'\n'.join('• '+f for f in files))
    elif intent=='explanation':
        selected=chosen[:min(8,len(chosen))]; topic=_topic_label(question); points=[plain_language(u['text'].strip()) for _,u,_,_ in selected]
        answer=(f"{topic}: a source-grounded explanation\n\nThe uploaded material discusses this topic through {len(points)} relevant statement(s). The explanation below reorganises the source and applies a small, fixed plain-language glossary where a safe wording rule exists.\n\n"+'\n'.join(f'{i+1}. {p}' for i,p in enumerate(points))+"\n\nKEY TAKEAWAY\nThis is a deterministic synthesis of the retrieved source statements. The wording rules do not add new factual claims. Open the source evidence to compare the explanation with the original text.")
    elif intent=='comparison':
        selected=chosen[:min(8,len(chosen))]
        answer="Comparison based on the uploaded material:\n\n"+'\n'.join('• '+u['text'] for _,u,_,_ in selected)+"\n\nThese are the available comparison statements; where the document does not state a difference, none has been assumed."
    elif intent=='list':
        selected=chosen[:min(10,len(chosen))]
        qlow=question.lower()
        focus_words=[]
        for word in ('limitation','disadvantage','advantage','benefit','type','feature','step','requirement','objective','component'):
            if word in qlow: focus_words.extend(expand_query(word))
        if focus_words:
            focused=[item for item in selected if set(item[2]) & set(focus_words)]
            if focused: selected=focused
        answer="Relevant points identified in the uploaded material:\n\n"+'\n'.join(f'{i+1}. {u["text"]}' for i,(_,u,_,_) in enumerate(selected))
    elif intent=='count':
        selected=chosen[:min(8,len(chosen))]; answer=f"I found {len(chosen)} distinct relevant knowledge statements, not necessarily the document's exact real-world count. Supporting statements:\n\n"+'\n'.join('• '+u['text'] for _,u,_,_ in selected)
    else:
        selected=chosen[:min(6,len(chosen))]; answer="Here is the most relevant information I found in your sources:\n\n"+'\n'.join('• '+u['text'] for _,u,_,_ in selected)
    avg=sum(x[0] for x in selected)/max(1,len(selected)); evidence=_evidence_objects(selected)
    trace=[f'Question intent: {intent}.',f'Search query after follow-up resolution: {q_for_search}.',f'Expanded with fixed lexical equivalences ({len(set(expand_query(q_for_search)))} unique terms).',f'Ranked {len(ranked)} candidate knowledge units using weighted lexical evidence and source diversity.',f'Synthesised {len(selected)} distinct statements from the uploaded source material.','Answer composition uses deterministic templates, extracted facts and a fixed plain-language glossary; no generative model was used.']
    return {'answer':answer,'status':'answered','intent':intent,'evidence':evidence,'trace':trace,'confidence':round(min(1,avg)*100,1)}

def make_summary(units):
    if not units: return 'No document content is loaded.'
    by_source=defaultdict(list)
    for u in units: by_source[u['source']].append(u)
    output=[]
    for source,source_units in by_source.items():
        freq=Counter(w for u in source_units for w in set(u['terms'])); scored=[]
        for u in source_units:
            terms=set(u['terms']); score=sum(math.log1p(freq[w]) for w in terms)/max(1,math.sqrt(len(terms))); scored.append((score,u))
        scored.sort(key=lambda x:x[0],reverse=True); selected=[]; seen=set()
        for _,u in scored:
            key=re.sub(r'\W+',' ',u['text'].lower())
            if key in seen or len(u['text'])<18: continue
            selected.append(u); seen.add(key)
            if len(selected)>=8: break
        themes=[w for w,_ in freq.most_common(8)]
        output.append(f"{source}\n{len(source_units)} extracted knowledge statements.\nRecurring terms: {', '.join(themes)}.\n\nMain content:\n"+'\n'.join('• '+u['text'] for u in selected))
    return '\n\n'+'\n\n'.join(output)
