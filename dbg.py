_TAG_DBG = 0x000

_TAG_ERR = 0x100

_TAG_CFG = 0x200

_TAG_THD = 0x300

def __DBG(TAG_KEY: int, KEY_ARR: list[str], VAL_ARR: list):
    TAG_MAP = {
        0x000: "DBG",
        0x100: "ERR",
        0x200: "CFG",
        0x300: "THD"
    }
    
    ########
    
    KEY_ARR_LEN = len(KEY_ARR)
    
    VAL_ARR_LEN = len(VAL_ARR)
    
    ########
    
    if KEY_ARR_LEN != VAL_ARR_LEN:
        print(f'debug.py : error : length of keys array ({KEY_ARR_LEN}) must match length of values array ({VAL_ARR_LEN})')
        
        return
    
    if KEY_ARR_LEN == 0:
        print(f'debug.py : error : length of arrays must be greater than 0')
        
        return
    
    if TAG_KEY not in TAG_MAP:
        print(f'debug.py : error : passed tag key ({TAG_KEY}) is not associated with a valid tag according to current tag map')
        
        return
    
    ########
    
    TAG = TAG_MAP[TAG_KEY]
    
    print(f'[{TAG}]  [`{KEY_ARR[0]}`:{VAL_ARR[0]}]')
    
    for KEY, VAL in zip(KEY_ARR[1:], VAL_ARR[1:]):
        print(f'       [`{KEY}`:{VAL}]')