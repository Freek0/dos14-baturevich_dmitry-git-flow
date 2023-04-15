import os

if os.environ.get('SHELL') == '/bin/bash':
    print('Greetings bash')
else:
    print(f'Hello {os.environ.get("SHELL")}')
