import os

# ./
import dbg

from dotenv import load_dotenv
load_dotenv()

# kin.py
_ACC_D             = float(os.getenv('ACC_D'))
_JMP_MAG           = float(os.getenv('JMP_MAG'))

# kin.py / debug
_DBG_KIN           = int(os.getenv('DBG_KIN'))