"""Registration mail must confirm an account, never instruct a password reset."""
import ast
from pathlib import Path


def test_registration_and_recovery_have_distinct_email_templates():
    tree = ast.parse(Path('infra/staging/identity/bootstrap.py').read_text())
    stages = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'update_or_create':
            keywords = {k.arg: k.value for k in node.keywords}
            if 'name' in keywords and isinstance(keywords['name'], ast.Constant):
                name = keywords['name'].value
                if name in ('monash-enrollment-verify-email', 'monash-recovery-email'):
                    stages[name] = ast.literal_eval(keywords['defaults'])
    assert stages['monash-enrollment-verify-email']['template'] == 'email/monash_confirmation.html'
    assert stages['monash-recovery-email']['template'] == 'email/monash_recovery.html'
    assert stages['monash-enrollment-verify-email']['activate_user_on_success'] is True
    assert stages['monash-recovery-email']['activate_user_on_success'] is False
