# prints a tagged title line followed by one line per field, e.g.
#
#   [ERR]  Music load failed
#          [`path`:./resources/music/]
#          [`error`:No file found]
#
# usage: log.error('Music load failed', path=path, error=e)

def _emit(tag, title, fields):
    print(f'[{tag}]  {title}')

    for key, val in fields.items():
        print(f'       [`{key}`:{val}]')

def debug(title, **fields):
    _emit('DBG', title, fields)

def error(title, **fields):
    _emit('ERR', title, fields)
