"""Enumerate omitted standard material without treating concepts as work counts."""
import collections,hashlib,json,tarfile,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from run_mece_closure import ROOT,read,write

RUN=ROOT/'research/source-store/mece-closure-v22-20261011'
STORE=ROOT/'research/source-store/standards'
XMI='{http://www.omg.org/XMI}';XSI='{http://www.w3.org/2001/XMLSchema-instance}'
RDF='{http://www.w3.org/1999/02/22-rdf-syntax-ns#}';OWL='{http://www.w3.org/2002/07/owl#}'

def prepare():
    out=RUN/'standard-scope-census.json';assert not out.exists(), 'Frozen scope already exists'
    iso=[];messages=[];tags=collections.Counter();types=collections.Counter()
    with zipfile.ZipFile(STORE/'raw/iso.zip') as z:
        for _,e in ET.iterparse(z.open(z.namelist()[0]),events=['end']):
            tag=e.tag.split('}')[-1];kind=e.get(XSI+'type','').split(':')[-1];tags[tag]+=1;types[kind]+=1
            if kind in ['BusinessArea','MessageSet']:
                iso.append(dict(id=e.get(XMI+'id'),kind=kind,name=e.get('name'),definition=e.get('definition'),
                    registration_status=e.get('registrationStatus'),business_area=e.get('businessArea'),
                    message_definition_ids=e.get('messageDefinition','').split(),
                    locator=f'//*[@xmi:id="{e.get(XMI+"id")}"]'))
            if tag=='messageDefinition':
                messages.append(dict(id=e.get(XMI+'id'),name=e.get('name'),definition=e.get('definition'),business_area=e.get('businessArea')))
            e.clear()
    write(RUN/'iso-catalogue-scope.json',dict(version='20260904',catalogue_items=iso,message_definitions=messages,
        source_zip_sha256=hashlib.sha256((STORE/'raw/iso.zip').read_bytes()).hexdigest(),
        source_scope='Actual serialized catalogue items, not assumed metamodel instances',
        business_process_instances=types['BusinessProcess'],business_transaction_instances=types['BusinessTransaction'],
        limitation='No serialized BusinessProcess/BusinessTransaction instances found; BusinessArea/MessageSet/MessageDefinition are not atomic financial work. Message flow/report documents remain separate evidence.'))
    old=read(STORE/'fibo-catalogue.json');included={m['path'] for m in old['module_manifest']};modules=[];terms=[];failed=[]
    with tarfile.open(STORE/'raw/fibo.tar.gz') as tar:
        for member in tar.getmembers():
            if not member.isfile() or not member.name.endswith('.rdf'):continue
            path=member.name.split('/',1)[1]
            if path in included:continue
            raw=tar.extractfile(member).read()
            try: root=ET.fromstring(raw)
            except ET.ParseError:
                failed.append(path);continue
            ont=root.find(OWL+'Ontology')
            if ont is None:continue
            maturity=next((x.get(RDF+'resource','').rsplit('/',1)[-1] for x in ont if x.tag.endswith('hasMaturityLevel')),None)
            records=[]
            for e in root:
                if e.tag not in [OWL+'Class',OWL+'ObjectProperty',OWL+'DatatypeProperty',OWL+'AnnotationProperty','{http://www.w3.org/2000/01/rdf-schema#}Class']:continue
                iri=e.get(RDF+'about')
                if not iri:continue
                records.append(dict(id=iri,kind=e.tag.split('}')[-1],name=next((x.text for x in e if x.tag.endswith('label')),None),
                    definition=next((x.text for x in e if x.tag.endswith('definition')),None),
                    module=path,module_maturity=maturity,
                    anonymous_constraints_present=any(not x.get(RDF+'resource') and len(x)>0 for x in e),
                    source_xml=ET.tostring(e,encoding='unicode')))
            modules.append(dict(path=path,domain=path.split('/')[0],maturity=maturity,named_schema_terms=len(records),sha256=hashlib.sha256(raw).hexdigest(),
                imports=[x.get(RDF+'resource') for x in ont if x.tag==OWL+'imports'],
                ontology_iri=ont.get(RDF+'about')))
            terms.extend(records)
    write(RUN/'fibo-omitted-scope.json',dict(version='master_2026Q2',commit='f59157fe156e3d91b1c045222d0a7dc06b7d78a2',modules=modules,terms=terms,parse_failures=failed,
        source_tar_sha256=hashlib.sha256((STORE/'raw/fibo.tar.gz').read_bytes()).hexdigest(),
        imported_as_active_concepts=False,limitations=['Maturity is the declaring ontology level; term overrides require assessment.',
        'Draft/Informative/EXMP/metadata modules are contextual, not automatically financial work or excluded finance.',
        'External imports still require provenance and scope assessment. Anonymous XML retained, not inferred as new work.']))
    # Heading-bounded blocks preserve every paragraph of the full publications.
    from bs4 import BeautifulSoup
    blocks=[]
    for book in ['a','b','c']:
        path=STORE/f'raw/nist-sp800-63{book}.html';soup=BeautifulSoup(path.read_text(),'html.parser')
        for h in soup.select('h1,h2'):
            if not h.get('id'):continue
            text=[h.get_text(' ',strip=True)]
            from bs4 import NavigableString
            for following in h.next_elements:
                if getattr(following,'name',None) in ['h1','h2']:break
                if isinstance(following,NavigableString) and following.parent.name not in ['script','style'] and following.parent is not h:
                    value=str(following).strip()
                    if value:text.append(value)
            joined='\n'.join(text)
            blocks.append(dict(section_id=f'NIST-63{book.upper()}:{h["id"]}',heading=text[0],text=joined,
                source_url=f'https://pages.nist.gov/800-63-4/sp800-63{book}.html#{h["id"]}',
                raw_path=str(path.relative_to(ROOT)),raw_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                contains_requirement_words=any(word in joined for word in [' SHALL ',' SHALL NOT ',' SHOULD ']),
                normative_statement='explicit normative' if 'This section is normative' in joined else 'explicit informative' if 'This section is informative' in joined else 'inherits publication section context; review required'))
    write(RUN/'nist-full-section-scope.json',dict(version='SP800-63A/B/C-4 final',blocks=blocks,scope='All identified h1/h2 heading blocks in three frozen full official HTML publications',
        limitation='Normativity and independently completed result require review; headings/SHALL clauses are not work counts.'))
    report=dict(version='WGSS-v22-standard-material-census',iso_business_areas=sum(r['kind']=='BusinessArea' for r in iso),
        iso_message_sets=sum(r['kind']=='MessageSet' for r in iso),iso_message_definitions=len(messages),
        iso_business_process_instances=types['BusinessProcess'],iso_business_transaction_instances=types['BusinessTransaction'],
        fibo_nonimported_modules=len(modules),fibo_nonimported_named_schema_terms=len(terms),
        fibo_module_domains=dict(collections.Counter(m['domain'] for m in modules)),
        fibo_module_maturities=dict(collections.Counter(str(m['maturity']) for m in modules)),fibo_parse_failures=len(failed),
        nist_heading_blocks=len(blocks),nist_requirement_containing_blocks=sum(b['contains_requirement_words'] for b in blocks),
        mapping_review_complete=False,global_mece_approved=False,automatic_adoption=False)
    write(out,report);print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':prepare()
