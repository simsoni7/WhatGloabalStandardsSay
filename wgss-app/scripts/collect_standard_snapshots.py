"""Collect/verify pinned official bytes into a private staging cache.

Parsing remains staging-only: it never promotes a new release, mapping, or
provider policy automatically. A changed source hash stops the process.
"""
import argparse,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--workdir',type=Path,default=ROOT/'research/source-store/standards');parser.add_argument('--parse',action='store_true');args=parser.parse_args()
 work=args.workdir.resolve();work.mkdir(parents=True,exist_ok=True)
 manifest=work/'source-manifest.json'
 if not manifest.exists():shutil.copyfile(ROOT/'research/data-v10/inputs/standards-source-manifest.json',manifest)
 env=os.environ|{'WGSS_STANDARD_WORKDIR':str(work)};scripts=ROOT/'research/data-v10/reproduce/standards'
 subprocess.run([sys.executable,str(scripts/'fetch_pinned_sources.py')],env=env,check=True)
 if args.parse:
  subprocess.run([sys.executable,str(scripts/'build_catalogues.py')],env=env,check=True)
  subprocess.run([sys.executable,str(scripts/'validate_catalogues.py')],env=env,check=True)
 print('Source snapshots verified; outputs remain staged in '+str(work))
if __name__=='__main__':main()
