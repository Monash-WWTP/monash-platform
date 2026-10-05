"""Idempotent local authentik provisioning. Run inside the pinned identity image."""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authentik.root.settings")
import django

django.setup()
from django.db import transaction
from authentik.core.models import Application, Group
from authentik.crypto.models import CertificateKeyPair
from authentik.providers.oauth2.models import OAuth2Provider, ScopeMapping
from authentik.flows.models import Flow, FlowStageBinding
from authentik.stages.prompt.models import PromptStage, Prompt
from authentik.stages.identification.models import IdentificationStage
from authentik.stages.redirect.models import RedirectStage
from authentik.stages.email.models import EmailStage
from authentik.stages.user_write.models import UserWriteStage
from authentik.stages.user_login.models import UserLoginStage
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage
from authentik.stages.authenticator_totp.models import AuthenticatorTOTPStage
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding

with transaction.atomic():
    flow, _ = Flow.objects.update_or_create(
        slug="monash-citizen-enrollment",
        defaults={
            "name": "Create your Monash Water account",
            "title": "Create your account",
            "designation": "enrollment",
            "authentication": "require_unauthenticated",
        },
    )
    fields = []
    for index, (key, label, kind) in enumerate(
        [
            ("username", "Username", "username"),
            ("email", "Email", "email"),
            ("password", "Password (at least 12 characters)", "password"),
            ("password_repeat", "Repeat password", "password"),
        ]
    ):
        prompt, _ = Prompt.objects.update_or_create(
            name="monash-" + key,
            defaults={
                "field_key": key,
                "label": label,
                "type": kind,
                "required": True,
                "order": index,
                "placeholder": "",
                "initial_value": "",
            },
        )
        fields.append(prompt)
    policy, _ = ExpressionPolicy.objects.update_or_create(
        name="monash-registration-validation",
        defaults={
            "expression": """data = request.context.get("prompt_data", {})
password = data.get("password", "")
return len(password) >= 12 and password == data.get("password_repeat") and bool(data.get("email"))"""
        },
    )
    prompt_stage, _ = PromptStage.objects.get_or_create(name="monash-enrollment-prompt")
    prompt_stage.fields.set(fields)
    prompt_stage.validation_policies.set([policy])
    write, _ = UserWriteStage.objects.update_or_create(
        name="monash-enrollment-create-inactive",
        defaults={
            "create_users_as_inactive": True,
            "user_creation_mode": "always_create",
        },
    )
    email, _ = EmailStage.objects.update_or_create(
        name="monash-enrollment-verify-email",
        defaults={
            "use_global_settings": True,
            "activate_user_on_success": True,
            "token_expiry": "minutes=30",
            "subject": "Verify your Monash Water account",
        },
    )
    login, _ = UserLoginStage.objects.get_or_create(name="monash-enrollment-login")
    verified, _ = ExpressionPolicy.objects.update_or_create(
        name="monash-mark-verified-email",
        defaults={
            "expression": """user = request.context.get("pending_user")
if not user or not user.is_active:
    return False
user.attributes["monash_verified_email"] = user.email
user.save(update_fields=["attributes"])
return True"""
        },
    )
    for order, stage in enumerate([prompt_stage, write, email, login]):
        binding, _ = FlowStageBinding.objects.update_or_create(
            target=flow, order=order * 10, defaults={"stage": stage}
        )
        if stage == login:
            PolicyBinding.objects.update_or_create(
                target=binding, order=0, defaults={"policy": verified}
            )
    recovery, _ = Flow.objects.update_or_create(
        slug="monash-account-recovery",
        defaults={
            "name": "Recover your Monash Water account",
            "title": "Reset your password",
            "designation": "recovery",
        },
    )
    recovery_identify, _ = IdentificationStage.objects.update_or_create(
        name="monash-recovery-identify",
        defaults={
            "user_fields": ["email"],
            "show_matched_user": False,
            "pretend_user_exists": True,
        },
    )
    recovery_email, _ = EmailStage.objects.update_or_create(
        name="monash-recovery-email",
        defaults={
            "use_global_settings": True,
            "activate_user_on_success": False,
            "token_expiry": "minutes=30",
            "subject": "Reset your Monash Water password",
        },
    )
    recovery_prompt, _ = PromptStage.objects.get_or_create(
        name="monash-recovery-password"
    )
    recovery_prompt.fields.set(
        Prompt.objects.filter(name__in=["monash-password", "monash-password_repeat"])
    )
    recovery_validation, _ = ExpressionPolicy.objects.update_or_create(
        name="monash-recovery-password-validation",
        defaults={
            "expression": """data = request.context.get("prompt_data", {})
return len(data.get("password", "")) >= 12 and data.get("password") == data.get("password_repeat")"""
        },
    )
    recovery_prompt.validation_policies.set([recovery_validation])
    recovery_write, _ = UserWriteStage.objects.update_or_create(
        name="monash-recovery-write", defaults={"user_creation_mode": "never_create"}
    )
    recovery_redirect, _ = RedirectStage.objects.update_or_create(
        name="monash-recovery-return",
        defaults={
            "mode": "static",
            "target_static": "http://localhost:8180/login",
            "keep_context": False,
        },
    )
    revoke, _ = ExpressionPolicy.objects.update_or_create(
        name="monash-recovery-revoke",
        defaults={
            "expression": """import os, json, hmac, hashlib, uuid
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from authentik.providers.oauth2.models import AccessToken, RefreshToken
from authentik.core.models import AuthenticatedSession
user = request.context.get("pending_user")
if not user or not user.is_active:
    return False
AccessToken.objects.filter(user=user).update(revoked=True)
RefreshToken.objects.filter(user=user).update(revoked=True)
AuthenticatedSession.objects.filter(user=user).delete()
body=json.dumps({"id":str(uuid.uuid5(uuid.NAMESPACE_URL,str(user.uuid)+str(user.password_change_date))),
    "issuer":os.environ["MONASH_EVENT_ISSUER"],"subject":str(user.uuid),
    "occurred_at":datetime.now(timezone.utc).isoformat(),"action":"credentials.reset"},separators=(",",":")).encode()
signature=hmac.new(os.environ["IDENTITY_EVENT_SECRET"].encode(),body,hashlib.sha256).hexdigest()
try:
    with urlopen(Request(os.environ["MONASH_EVENT_ENDPOINT"],data=body,headers={"Content-Type":"application/json","X-Monash-Signature":signature}),timeout=5) as response:
        return response.status == 204
except Exception:
    return False"""
        },
    )
    for order, stage in enumerate(
        [
            recovery_identify,
            recovery_email,
            recovery_prompt,
            recovery_write,
            recovery_redirect,
        ]
    ):
        binding, _ = FlowStageBinding.objects.update_or_create(
            target=recovery, order=order * 10, defaults={"stage": stage}
        )
        if stage == recovery_redirect:
            PolicyBinding.objects.update_or_create(
                target=binding, order=0, defaults={"policy": revoke}
            )
    IdentificationStage.objects.filter(
        name="default-authentication-identification"
    ).update(enrollment_flow=flow, recovery_flow=recovery)
    mapping, _ = ScopeMapping.objects.update_or_create(
        name="Monash verified email",
        defaults={
            "scope_name": "email",
            "expression": """return {"email": request.user.email, "email_verified": bool(request.user.is_active and request.user.email and request.user.attributes.get("monash_verified_email") == request.user.email)}""",
        },
    )
    key = CertificateKeyPair.objects.get(name="authentik Self-signed Certificate")
    authorization = Flow.objects.get(
        slug="default-provider-authorization-implicit-consent"
    )
    invalidation = Flow.objects.get(slug="default-provider-invalidation-flow")
    authentication = Flow.objects.get(slug="default-authentication-flow")
    operator_flow, _ = Flow.objects.update_or_create(
        slug="monash-operator-authentication",
        defaults={
            "name": "Operator sign-in with MFA",
            "title": "Operator sign-in",
            "designation": "authentication",
        },
    )
    operator_mfa, _ = AuthenticatorValidateStage.objects.update_or_create(
        name="monash-operator-mfa",
        defaults={
            "not_configured_action": "configure",
            "device_classes": ["totp"],
            "last_auth_threshold": "seconds=0",
        },
    )
    operator_mfa.configuration_stages.set(
        AuthenticatorTOTPStage.objects.filter(name="default-authenticator-totp-setup")
    )
    for binding in FlowStageBinding.objects.filter(target=authentication).order_by(
        "order"
    ):
        stage = (
            operator_mfa
            if binding.stage_id
            in set(AuthenticatorValidateStage.objects.values_list("pk", flat=True))
            else binding.stage
        )
        FlowStageBinding.objects.update_or_create(
            target=operator_flow, order=binding.order, defaults={"stage": stage}
        )
    for slug, client, kind, redirect in [
        (
            "monash-web",
            "monash-web",
            "confidential",
            "http://localhost:8180/api/v1/auth/callback",
        ),
        (
            "monash-operator",
            "monash-operator",
            "confidential",
            "http://localhost:8180/api/v1/auth/callback",
        ),
        (
            "citizen-mobile",
            "citizen-mobile",
            "public",
            "au.edu.monash.citizenflood:/oauthredirect",
        ),
    ]:
        provider, _ = OAuth2Provider.objects.update_or_create(
            name=slug,
            defaults={
                "client_id": client,
                "client_type": kind,
                "client_secret": os.environ.get("MONASH_WEB_SECRET", "")
                if kind == "confidential"
                else "",
                "authentication_flow": operator_flow
                if slug == "monash-operator"
                else authentication,
                "authorization_flow": authorization,
                "invalidation_flow": invalidation,
                "_redirect_uris": [{"matching_mode": "strict", "url": redirect}],
                "issuer_mode": "global",
                "sub_mode": "user_uuid",
                "signing_key": key,
                "grant_types": ["authorization_code", "refresh_token"],
                "access_token_validity": "minutes=10",
                "refresh_token_validity": "days=7",
                "include_claims_in_id_token": True,
            },
        )
        provider.property_mappings.set(
            [
                mapping,
                *ScopeMapping.objects.filter(
                    scope_name__in=["openid", "profile", "offline_access"]
                ),
            ]
        )
        Application.objects.update_or_create(
            slug=slug, defaults={"name": "Monash Water " + slug, "provider": provider}
        )
print(
    "Monash OIDC providers and verified registration configured; no operational reports created."
)
