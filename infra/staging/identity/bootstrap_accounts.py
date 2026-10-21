"""Provision only the reviewed account flows in the pinned provider."""

import os
from urllib.parse import urlparse

from authentik.brands.models import Brand
from authentik.flows.models import Flow, FlowStageBinding
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage
from authentik.stages.email.models import EmailStage
from authentik.stages.password.models import PasswordStage
from authentik.stages.dummy.models import DummyStage
from authentik.stages.prompt.models import Prompt, PromptStage
from authentik.stages.redirect.models import RedirectStage
from django.db import transaction


def provision():
    origin = os.environ["MONASH_ACCOUNT_RETURN_ORIGIN"].rstrip("/")
    uri = urlparse(origin)
    if (
        uri.username
        or uri.password
        or uri.query
        or uri.fragment
        or uri.path not in ("", "/")
        or not uri.hostname
        or not (
            uri.scheme == "https"
            or uri.scheme == "http"
            and uri.hostname in {"localhost", "127.0.0.1"}
        )
    ):
        raise ValueError("Approved HTTPS account return origin required")

    def prompt(key, label, kind, required=True, identity=None):
        return Prompt.objects.update_or_create(
            name="monash-account-" + (identity or key),
            defaults={
                "field_key": key,
                "label": label,
                "type": kind,
                "required": required,
                "order": 0,
                "placeholder": "",
                "initial_value": "",
            },
        )[0]

    def policy(name, fn):
        return ExpressionPolicy.objects.update_or_create(
            name="monash-account-" + name,
            defaults={
                "expression": f"import sys\nsys.path.insert(0, '/monash-brand')\nimport account_settings\nresult = account_settings.{fn}(request)\nif not result:\n    ak_message('Could not complete this change. Check the details or sign in again and retry.')\nreturn result"
            },
        )[0]

    def form(name, fields, fn):
        stage = PromptStage.objects.get_or_create(name="monash-account-" + name)[0]
        stage.fields.set(fields)
        stage.validation_policies.set([policy(name, fn)])
        return stage

    def flow(slug, title, stages):
        f = Flow.objects.update_or_create(
            slug=slug,
            defaults={
                "name": title,
                "title": title,
                "designation": "stage_configuration",
                "authentication": "require_authenticated",
            },
        )[0]
        FlowStageBinding.objects.filter(target=f).delete()
        marker = DummyStage.objects.get_or_create(
            name="monash-account-authentication-complete"
        )[0]
        stages = [*stages[:2], marker, *stages[2:]]
        for i, stage in enumerate(stages):
            binding = FlowStageBinding.objects.create(
                target=f, stage=stage, order=i * 10, evaluate_on_plan=(i == 0)
            )
            if stage == marker:
                binding.re_evaluate_policies = True
                binding.save()
                completed = ExpressionPolicy.objects.update_or_create(
                    name="monash-account-authentication-complete",
                    defaults={
                        "expression": "import time\nrequest.context['flow_plan'].context['monash_reauthenticated'] = {'user': str(request.user.uuid), 'at': time.time()}\nreturn False"
                    },
                )[0]
                PolicyBinding.objects.create(target=binding, policy=completed, order=0)
            if i == 0:
                initialize = ExpressionPolicy.objects.update_or_create(
                    name="monash-account-bind-current-user",
                    defaults={
                        "expression": "request.context['flow_plan'].context['pending_user'] = request.user\nreturn request.user.is_authenticated"
                    },
                )[0]
                PolicyBinding.objects.create(target=binding, policy=initialize, order=0)

        return f

    with transaction.atomic():
        base = PasswordStage.objects.get(name="default-authentication-password")
        password = PasswordStage.objects.update_or_create(
            name="monash-account-reauthenticate",
            defaults={
                "backends": [
                    backend
                    for backend in base.backends
                    if backend != "authentik.core.auth.TokenBackend"
                ],
                "failed_attempts_before_cancel": 5,
                "allow_show_password": False,
            },
        )[0]
        mfa = AuthenticatorValidateStage.objects.update_or_create(
            name="monash-account-current-factor",
            defaults={
                "not_configured_action": "skip",
                "device_classes": ["totp", "webauthn", "static", "duo", "sms", "email"],
                "last_auth_threshold": "seconds=0",
            },
        )[0]
        done = RedirectStage.objects.update_or_create(
            name="monash-account-return",
            defaults={
                "mode": "static",
                "target_static": origin + "/account",
                "keep_context": False,
            },
        )[0]
        profile = form(
            "profile",
            [prompt("name", "Display name (optional)", "text", False)],
            "save_profile",
        )
        f = flow(
            "monash-account-profile", "Edit profile", [password, mfa, profile, done]
        )
        # The stock profile route is also restricted; no unverified email editor remains.
        flow(
            "default-user-settings-flow", "Edit profile", [password, mfa, profile, done]
        )
        Brand.objects.filter(domain="localhost:9100").update(flow_user_settings=f)
        prepare = form(
            "email-candidate",
            [prompt("candidate_email", "New email", "email")],
            "prepare_email_change",
        )
        verify = EmailStage.objects.update_or_create(
            name="monash-account-email-verify",
            defaults={
                "use_global_settings": True,
                "activate_user_on_success": False,
                "token_expiry": "minutes=30",
                "subject": "Confirm your new Monash Water email",
                "template": "email/monash_email_change.html",
            },
        )[0]
        finish = form(
            "email-finish",
            [
                prompt(
                    "confirm",
                    "Confirm email change",
                    "checkbox",
                    identity="email-confirm",
                )
            ],
            "complete_email_change",
        )
        flow(
            "monash-account-email",
            "Change email",
            [password, mfa, prepare, verify, finish, done],
        )
        first = prompt(
            "new_password", "New password (at least 12 characters)", "password"
        )
        second = prompt("repeat_password", "Repeat new password", "password")
        second.order = 1
        second.save()
        change = form("password", [first, second], "change_password")
        flow(
            "monash-account-password", "Change password", [password, mfa, change, done]
        )
        flow(
            "default-password-change", "Change password", [password, mfa, change, done]
        )
        confirm = form(
            "signout-all",
            [
                prompt(
                    "confirm",
                    "Sign out all devices",
                    "checkbox",
                    identity="signout-confirm",
                )
            ],
            "sign_out_all",
        )
        flow(
            "monash-account-signout-all",
            "Sign out all devices",
            [password, mfa, confirm, done],
        )
        security = form(
            "security",
            [
                prompt(
                    "confirm",
                    "Continue to security settings",
                    "checkbox",
                    identity="security-confirm",
                )
            ],
            "confirm_security",
        )
        portal = RedirectStage.objects.update_or_create(
            name="monash-account-security-return",
            defaults={
                "mode": "static",
                "target_static": "/if/user/#/settings;%7B%22page%22%3A%22page-credentials%22%7D",
                "keep_context": False,
            },
        )[0]
        flow(
            "monash-account-security",
            "Verify account",
            [password, mfa, security, portal],
        )
