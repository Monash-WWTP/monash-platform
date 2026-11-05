"""Require a real OTP validation after first-time operator authenticator setup."""

VALIDATION_NEEDED = '''plan = request.context.get("flow_plan")
context = plan.context if plan else request.context
return not bool(context.get("auth_method_args", {}).get("mfa_devices"))'''


def provision():
    from django.db import transaction
    from authentik.flows.models import Flow, FlowStageBinding
    from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage
    from authentik.policies.expression.models import ExpressionPolicy
    from authentik.policies.models import PolicyBinding

    with transaction.atomic():
        flow = Flow.objects.get(slug='monash-operator-authentication')
        validation, _ = AuthenticatorValidateStage.objects.update_or_create(
            name='monash-operator-confirm-mfa',
            defaults={'not_configured_action': 'deny', 'device_classes': ['totp'],
                      'last_auth_threshold': 'seconds=0'},
        )
        policy, _ = ExpressionPolicy.objects.update_or_create(
            name='monash-operator-needs-mfa-validation',
            defaults={'expression': VALIDATION_NEEDED},
        )
        binding, _ = FlowStageBinding.objects.update_or_create(
            target=flow, order=40,
            defaults={'stage': validation, 'evaluate_on_plan': False,
                      're_evaluate_policies': True},
        )
        PolicyBinding.objects.update_or_create(target=binding, order=0,
                                               defaults={'policy': policy})
