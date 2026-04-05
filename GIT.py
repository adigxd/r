import argparse
import subprocess
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--typ', default='prod')
parser.add_argument('-m', '--msg', default=None)
args = parser.parse_args()

body = args.msg if args.msg else datetime.now().strftime('%Y%m%d%H%M%S')
msg = f'{args.typ}: {body}'

subprocess.run(['git', 'add', '.'], check=True)
subprocess.run(['git', 'commit', '-am', msg], check=True)
subprocess.run(['git', 'push'], check=True)
