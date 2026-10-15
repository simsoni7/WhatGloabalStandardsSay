"""Stable document-order sections, including duplicated native HTML IDs."""
import collections,hashlib
from bs4 import BeautifulSoup,NavigableString

def blocks(path,book,root):
    soup=BeautifulSoup(path.read_text(),'html.parser')
    headings=[h for h in soup.select('h1,h2') if h.get('id')]
    counts=collections.Counter(h['id'] for h in headings);seen=collections.Counter();result=[]
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    for ordinal,h in enumerate(headings):
        seen[h['id']]+=1;parts=[h.get_text(' ',strip=True)]
        for following in h.next_elements:
            if getattr(following,'name',None) in ['h1','h2']:break
            if isinstance(following,NavigableString) and following.parent.name not in ['script','style'] and not any(parent is h for parent in following.parents):
                value=str(following).strip()
                if value:parts.append(value)
        text='\n'.join(parts)
        suffix=f':occurrence:{seen[h["id"]]}' if counts[h['id']]>1 else ''
        result.append(dict(section_id=f'NIST-63{book.upper()}:{h["id"]}{suffix}',native_html_id=h['id'],native_id_occurrence=seen[h['id']],
            heading_ordinal=ordinal,source_locator=f'identified h1/h2 heading[{ordinal}] with id={h["id"]}; occurrence={seen[h["id"]]}',
            heading=parts[0],text=text,source_url=f'https://pages.nist.gov/800-63-4/sp800-63{book}.html#{h["id"]}',
            raw_path=str(path.relative_to(root)),raw_sha256=sha,
            contains_requirement_words=any(word in text for word in ['SHALL','SHOULD']),
            normative_statement='explicit normative' if 'This section is normative' in text else 'explicit informative' if 'This section is informative' in text else 'inherits publication section context; review required'))
    assert len(result)==len({r['section_id'] for r in result})
    return result
