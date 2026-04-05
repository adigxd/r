import subprocess
from datetime import datetime

dtm = datetime.now().strftime('%Y%m%d%H%M%S')
msg = f'prod: {dtm}'

subprocess.run(['git', 'add', '.'], check=True)
subprocess.run(['git', 'commit', '-am', msg], check=True)
subprocess.run(['git', 'push'], check=True)
