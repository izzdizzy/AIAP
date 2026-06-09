import groq
from groq import resources
print('resources attrs:')
print([n for n in dir(resources) if not n.startswith('_')])
# inspect chat or responses if present
for candidate in ['chat', 'responses', 'completions']:
    print('\nCandidate:', candidate)
    attr = getattr(resources, candidate, None)
    print(' - present:', attr is not None)
    if attr is not None:
        print(' - attrs:', [n for n in dir(attr) if not n.startswith('_')][:50])
