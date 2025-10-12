#!/usr/bin/env python3
import jinja2

# Test template rendering
template_str = '''
<script>
    const allChannelGroups = {{ channel_groups|tojson|safe }};
</script>
'''

try:
    env = jinja2.Environment()
    template = env.from_string(template_str)
    result = template.render(channel_groups=[{'id': 1, 'name': 'Test'}])
    print('Template rendered successfully:')
    print(result)
except Exception as e:
    print(f'Template error: {e}')