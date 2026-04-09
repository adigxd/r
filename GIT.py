import argparse
import subprocess
from datetime import datetime

psr = argparse.ArgumentParser(description='Stage, commit, and push changes to the remote repository.')
psr.add_argument('-t', '--typ', default='prod', help='commit type prefix (default: prod)')
psr.add_argument('-m', '--msg', default=None, help='commit message body (default: current timestamp)')
arg = psr.parse_args()

bdy = arg.msg if arg.msg else datetime.now().strftime('%Y%m%d%H%M%S')
msg = f'{arg.typ}: {bdy}'

subprocess.run(['git', 'add', '.'], check=True)
subprocess.run(['git', 'commit', '-am', msg], check=True)
subprocess.run(['git', 'push'], check=True)
