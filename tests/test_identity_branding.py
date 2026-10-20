from pathlib import Path


def test_branding_resources_are_shared_by_identity_server_and_worker():
    source = Path('infra/staging/identity/bootstrap.py').read_text()
    assert 'branding_title' in source and 'CitizenFlood' in source
    assert 'branding_custom_css' in source and 'branding_logo' in source
    css = Path('infra/staging/identity/branding.css').read_text()
    assert '--ak-color-primary' in css and '#146346' in css
    compose = Path('infra/staging/compose.yaml').read_text()
    assert './identity:/monash-brand:ro' in compose
    assert '<<: *identity' in compose


def test_branded_confirmation_and_recovery_templates_have_distinct_actions():
    root = Path('infra/staging/identity/templates/email')
    confirm = (root / 'monash_confirmation.html').read_text()
    recovery = (root / 'monash_recovery.html').read_text()
    assert 'Confirm account' in confirm and 'Reset password' not in confirm
    assert 'Reset password' in recovery and 'Confirm account' not in recovery
    for template in (confirm, recovery):
        assert '{{ url }}' in template and 'CitizenFlood' in template
        assert 'Monash Water' in template


def test_local_brand_matches_actual_identity_host_including_port():
    source = Path('infra/staging/identity/bootstrap.py').read_text()
    assert "domain='localhost:9100'" in source
    assert "'base': 'light'" in source
