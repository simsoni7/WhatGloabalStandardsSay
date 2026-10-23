import { redirect } from "next/navigation";
import { officialWorkspaceUrl } from "../lib/canonical-workspace.mjs";
export default async function Home({searchParams}: {searchParams?: Promise<Record<string,string|string[]|undefined>>}){
  const destination=new URL(officialWorkspaceUrl);
  for(const [key,value] of Object.entries(await searchParams||{})){
    for(const item of Array.isArray(value)?value:[value])if(item!==undefined)destination.searchParams.append(key,item);
  }
  redirect(destination.href);
}
