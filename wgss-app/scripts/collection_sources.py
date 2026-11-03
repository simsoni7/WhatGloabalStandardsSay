"""Additional pinned official language-pack source, with original keys and notices."""
import json,re
from collection_batch import fetch_bytes,digest,norm,now,pair_key,validate_pairs,atomic_json

MIFOS_LOCALES={'az':'az-AZ','cs':'cs-CS','de':'de-DE','es':'es-MX','fr':'fr-FR','it':'it-IT','ko':'ko-KO','lt':'lt-LT','lv':'lv-LV','ne':'ne-NE','pt':'pt-PT','sw':'sw-SW'}

def flatten(value, path=''):
    result={}
    if isinstance(value,dict):
        for key,child in value.items():result.update(flatten(child,path+'/'+key.replace('~','~0').replace('/','~1')))
    elif isinstance(value,str):result[path]=value
    return result

def mifos_pairs(english,target,language):
    en,other=flatten(english),flatten(target)
    rows=[]
    for key in en.keys() & other.keys():
        a,b=en[key],other[key]
        if not a.strip() or not b.strip() or norm(a)==norm(b) or len(a)>900 or len(b)>900:continue
        if not re.search(r'account|payment|loan|saving|deposit|withdraw|transfer|currency|balance|interest|charge|cash|invoice|ledger|repay',key+' '+a,re.I):continue
        # Preserve interpolation contracts, never turn dynamic values into invented examples.
        if sorted(re.findall(r'{{.*?}}',a))!=sorted(re.findall(r'{{.*?}}',b)):continue
        rows.append({'key':language+':'+key,'code':key,'language':language,'english':a,'target':b})
    return sorted(rows,key=lambda r:r['code'])

def research_mifos(languages,directory,model,existing,max_pairs):
    domains=['api.github.com','raw.githubusercontent.com']
    revision=json.loads(fetch_bytes('https://api.github.com/repos/openMF/web-app/commits/dev',domains))['sha']
    if not re.fullmatch('[0-9a-f]{40}',revision):raise ValueError('invalid_source_revision')
    base=f'https://raw.githubusercontent.com/openMF/web-app/{revision}/'
    license_raw=fetch_bytes(base+'LICENSE',domains)
    if b'Mozilla Public License Version 2.0' not in license_raw:raise ValueError('license_changed_requires_review')
    directory.mkdir(parents=True,exist_ok=True)
    (directory/'LICENSE.txt').write_bytes(license_raw)
    source_base=base+'src/assets/translations/'
    english_raw=fetch_bytes(source_base+'en-US.json',domains)
    korean_raw=fetch_bytes(source_base+'ko-KO.json',domains)
    (directory/'en-US.json').write_bytes(english_raw);(directory/'ko-KO.json').write_bytes(korean_raw)
    results=[]
    for language in languages:
        try:
            filename=MIFOS_LOCALES[language]+'.json';url=source_base+filename
            raw=fetch_bytes(url,domains);(directory/filename).write_bytes(raw)
            rows=[r for r in mifos_pairs(json.loads(english_raw),json.loads(raw),language) if pair_key(r) not in existing and 'excluded:'+revision+':'+pair_key(r) not in existing][:max_pairs]
            decisions=model.call('Independently screen exact aligned official Mifos financial UI strings. Keep only clear financial UI pairs, reject wrong meanings, software errors, ambiguous labels or untranslated text. Never rewrite originals. Return JSON {"rows":[{"key":"exact key","include":true,"risk":"none|alignment|unreadable|nonfinancial"}]} one decision per key. Rows: '+json.dumps(rows,ensure_ascii=False),max_tokens=6000) if rows else {'rows':[]}
            accepted=validate_pairs(decisions,rows)
            for row in accepted:row.update(sourceUrl=url,sourceSha256=digest(raw),englishSourceUrl=source_base+'en-US.json',englishSourceSha256=digest(english_raw),koreanSourceUrl=source_base+'ko-KO.json',koreanSourceSha256=digest(korean_raw),revision=revision,license='MPL-2.0',licenseUrl=base+'LICENSE',licenseSha256=digest(license_raw),sourceName='Mifos Web App · 금융업무 UI',sourceDatasetId='mifos_web_app',collectedAt=now(),automatedScreening=True,automaticallyPublished=False)
            results.append({'language':language,'observed':len(rows),'accepted':accepted,'revision':revision,'excludedKeys':['excluded:'+revision+':'+pair_key(r) for r in rows if r['key'] not in {a['key'] for a in accepted}]})
        except Exception as error:
            from collection_batch import safe_error
            results.append({'language':language,'observed':0,'accepted':[],'error':safe_error(error)})
    atomic_json(directory/'source-manifest.json',{'revision':revision,'licenseUrl':base+'LICENSE','licenseSha256':digest(license_raw),'languages':languages})
    return results
