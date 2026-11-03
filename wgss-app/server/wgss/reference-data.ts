import original from './reference-index.json';
import extraLanguages from './research-languages.json';
export default {...original,languages:[...original.languages,...extraLanguages.filter(x=>!original.languages.some(y=>y.id===x.id))]};
