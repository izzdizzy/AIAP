import groq
import os
print('groq module attrs:')
print([n for n in dir(groq) if not n.startswith('_')])
print('\nGROQ_API_KEY present:', bool(os.environ.get('GROQ_API_KEY')))
from groq import Groq
key = os.environ.get('GROQ_API_KEY')
try:
    client = Groq(api_key=key)
    print('\nClient type:', type(client))
    print('\nClient attrs:')
    print([n for n in dir(client) if not n.startswith('_')])
except Exception as e:
    print('Error creating Groq client:', e)
