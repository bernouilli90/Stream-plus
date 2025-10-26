#!/usr/bin/env python3

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env

from models import RulesManager
from execute_rules import RuleExecutor
import json

# Get the rule
rm = RulesManager()
rule = rm.get_rule(3)
print(f'Executing rule: {rule.name}')
print(f'disable_profiles: {rule.disable_profiles}')

# Execute the rule
executor = RuleExecutor()
result = executor.execute_assignment_rules(rule_ids=[3], verbose=True)
print('Execution result:')
print(json.dumps(result, indent=2))