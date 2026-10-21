"""Provider-owned account changes. No credential value is sent to the platform."""

import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import UTC, datetime
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from uuid import uuid4

from authentik.core.models import AuthenticatedSession, User
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.providers.oauth2.models import AccessToken, RefreshToken
from authentik.stages.email.models import EmailStage
from authentik.stages.email.stage import TemplateEmailMessage, send_mails
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import connection, transaction
from django.contrib.auth import logout
from django.http import JsonResponse, HttpResponseRedirect

PENDING = "monash_pending_email"
RECENT = "monash_account_recent"


class ChangeRejected(Exception):
    pass


def plan(request):
    return request.http_request.session.get(SESSION_KEY_PLAN)


def actor(request, restored=False):
    user = request.user
    if not user or not user.is_authenticated or not user.is_active:
        raise ChangeRejected()
    http_user = request.http_request.user
    if http_user.is_authenticated and http_user.pk != user.pk:
        raise ChangeRejected()
    if not restored and not http_user.is_authenticated:
        raise ChangeRejected()
    return user


def data(request, allowed):
    values = dict(request.context.get("prompt_data", {}))
    values.pop("component", None)
    if set(values) - set(allowed):
        raise ChangeRejected()
    return values


def mark_recent(request):
    try:
        user = actor(request)
        request.http_request.session[RECENT] = {
            "user": str(user.uuid),
            "at": time.time(),
        }
        return True
    except ChangeRejected:
        return False


def confirm_security(request):
    try:
        if data(request, {"confirm"}).get("confirm") is not True:
            return False
        return mark_recent(request)
    except ChangeRejected:
        return False


def recent(http):
    proof = http.session.get(RECENT, {})
    return (
        proof.get("user") == str(http.user.uuid)
        and 0 <= time.time() - proof.get("at", 0) <= 300
    )


def save_profile(request):
    try:
        user = actor(request)
        values = data(request, {"name"})
        name = values.get("name", "")
        if not isinstance(name, str) or len(name.strip()) > 120:
            raise ChangeRejected()
        with transaction.atomic():
            current = User.objects.select_for_update().get(pk=user.pk)
            current.name = name.strip()
            current.save(update_fields=["name"])
        return True
    except (ChangeRejected, ValidationError):
        return False


def lock_email(candidate):
    # Serialize candidate ownership across different user rows on PostgreSQL.
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", [candidate.lower()]
        )


def prepare_email_change(request):
    try:
        user = actor(request)
        values = data(request, {"candidate_email"})
        candidate = values.get("candidate_email", "").strip().lower()
        validate_email(candidate)
        if len(candidate) > 254 or candidate == user.email.lower():
            raise ChangeRejected()
        with transaction.atomic():
            current = User.objects.select_for_update().get(pk=user.pk)
            lock_email(candidate)
            if (
                User.objects.exclude(pk=user.pk)
                .filter(email__iexact=candidate)
                .exists()
            ):
                raise ChangeRejected()
            attempt = {
                "candidate": candidate,
                "nonce": secrets.token_urlsafe(32),
                "expires": time.time() + 1800,
                "event": str(uuid4()),
            }
            current.attributes = {**current.attributes, PENDING: attempt}
            current.save(update_fields=["attributes"])
            p = plan(request)
            if p is None:
                raise ChangeRejected()
            p.context.update({"email": candidate, "monash_email_attempt": attempt})
            # The mutable server-side FlowPlan is persisted by the flow executor.
        return True
    except (ChangeRejected, ValidationError, AttributeError):
        return False


def send_event(user, action, event_id):
    body = json.dumps(
        {
            "id": str(event_id),
            "issuer": os.environ["MONASH_EVENT_ISSUER"],
            "subject": str(user.uuid),
            "occurred_at": datetime.now(UTC).isoformat(),
            "action": action,
        },
        separators=(",", ":"),
    ).encode()
    signature = hmac.new(
        os.environ["IDENTITY_EVENT_SECRET"].encode(), body, hashlib.sha256
    ).hexdigest()
    try:
        with urlopen(
            Request(
                os.environ["MONASH_EVENT_ENDPOINT"],
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Monash-Signature": signature,
                },
            ),
            timeout=5,
        ) as response:
            return response.status == 204
    except Exception:
        return False


def revoke(user, action, event_id):
    AccessToken.objects.filter(user=user).update(revoked=True)
    RefreshToken.objects.filter(user=user).update(revoked=True)
    AuthenticatedSession.objects.filter(user=user).delete()
    if not send_event(user, action, event_id):
        raise ChangeRejected()


def notify_old_email(user, old):
    message = TemplateEmailMessage(
        subject="Your Monash Water email changed",
        template_name="email/monash_email_changed.html",
        to=[(user.name, old)],
        language="en-us",
        template_context={"user": user},
    )
    send_mails(EmailStage.objects.get(name="monash-account-email-verify"), message)


def complete_email_change(request):
    try:
        user = actor(request, restored=True)
        values = data(request, {"confirm"})
        if values.get("confirm") is not True:
            raise ChangeRejected()
        p = plan(request)
        proof = p.context.get("is_restored")
        attempt = p.context.get("monash_email_attempt", {})
        if not proof or proof.user.pk != user.pk:
            raise ChangeRejected()
        with transaction.atomic():
            current = User.objects.select_for_update().get(pk=user.pk)
            pending = current.attributes.get(PENDING)
            if not pending or pending != attempt or pending["expires"] < time.time():
                raise ChangeRejected()
            lock_email(pending["candidate"])
            if (
                User.objects.exclude(pk=user.pk)
                .filter(email__iexact=pending["candidate"])
                .exists()
            ):
                raise ChangeRejected()
            old = current.email
            current.email = pending["candidate"]
            attrs = dict(current.attributes)
            attrs.pop(PENDING, None)
            attrs["monash_verified_email"] = current.email
            current.attributes = attrs
            current.save(update_fields=["email", "attributes"])
            revoke(current, "account.email_changed", pending["event"])
        logout(request.http_request)
        try:
            notify_old_email(current, old)
        except Exception:
            # Non-secret operational evidence; ownership stays at the verified address.
            import logging

            logging.getLogger(__name__).warning(
                "Previous-address notification failed",
                extra={"user_id": str(current.uuid)},
            )
        return True
    except (ChangeRejected, ValidationError, AttributeError, KeyError):
        return False


def change_password(request):
    try:
        user = actor(request)
        values = data(request, {"new_password", "repeat_password"})
        password = values.get("new_password", "")
        if (
            not isinstance(password, str)
            or len(password) < 12
            or password != values.get("repeat_password")
        ):
            raise ChangeRejected()
        with transaction.atomic():
            current = User.objects.select_for_update().get(pk=user.pk)
            current.set_password(password, request=request.http_request)
            current.save()
            revoke(current, "credentials.changed", uuid4())
        logout(request.http_request)
        return True
    except (ChangeRejected, ValidationError):
        return False


def sign_out_all(request):
    try:
        user = actor(request)
        if data(request, {"confirm"}).get("confirm") is not True:
            raise ChangeRejected()
        with transaction.atomic():
            current = User.objects.select_for_update().get(pk=user.pk)
            revoke(current, "sessions.revoked", uuid4())
        logout(request.http_request)
        return True
    except ChangeRejected:
        return False


def native_setup(http):
    if not http.path.startswith("/api/v3/flows/executor/"):
        return False
    from authentik.flows.models import FlowStageBinding

    slug = http.path.removeprefix("/api/v3/flows/executor/").split("/")[0]
    relations = [
        "authenticatorduostage",
        "authenticatoremailstage",
        "authenticatorsmsstage",
        "authenticatorstaticstage",
        "authenticatortotpstage",
        "authenticatorwebauthnstage",
    ]
    return any(
        any(hasattr(binding.stage, relation) for relation in relations)
        for binding in FlowStageBinding.objects.filter(
            target__slug=slug
        ).select_related("stage")
    )


class AccountSettingsGuard:
    """Protect native user edits and authenticator APIs as well as branded flows."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, http):
        user = getattr(http, "user", None)
        account_pages = {
            "monash-account-profile",
            "monash-account-email",
            "monash-account-password",
            "monash-account-security",
            "monash-account-signout-all",
            "default-user-settings-flow",
            "default-password-change",
        }
        if (
            http.method == "GET"
            and http.path.startswith("/if/flow/")
            and http.path.split("/")[3] in account_pages
            and not (user and user.is_authenticated)
            and "flow_token" not in http.GET
        ):
            return HttpResponseRedirect(
                "/if/flow/default-authentication-flow/?"
                + urlencode({"next": http.path})
            )
        setup = native_setup(http)
        guarded = setup or http.path.startswith(
            (
                "/api/v3/core/users/",
                "/api/v3/core/tokens/",
                "/api/v3/authenticators/",
                "/api/v3/core/authenticated_sessions/",
            )
        )
        if (
            guarded
            and http.method not in {"GET", "HEAD", "OPTIONS"}
            and not (user and user.is_authenticated and user.is_superuser)
        ):
            if not user or not user.is_authenticated:
                return JsonResponse(
                    {"detail": "Use an authenticated account settings flow."},
                    status=403,
                )
            path = http.path
            if path.startswith(("/api/v3/core/users/", "/api/v3/core/tokens/")):
                return JsonResponse(
                    {"detail": "Use the verified Monash Water account flow."},
                    status=403,
                )
            sensitive = setup or path.startswith(
                ("/api/v3/authenticators/", "/api/v3/core/authenticated_sessions/")
            )
            if sensitive and not recent(http):
                return JsonResponse(
                    {"detail": "Open Security and verify your account again."},
                    status=403,
                )
            if setup or path.startswith("/api/v3/authenticators/"):
                try:
                    with transaction.atomic():
                        current = User.objects.select_for_update().get(pk=user.pk)
                        revoke(current, "credentials.changed", uuid4())
                except ChangeRejected:
                    return JsonResponse(
                        {
                            "detail": "Session revocation unavailable. No security change was made."
                        },
                        status=503,
                    )
        response = self.get_response(http)
        if (
            guarded
            and http.method not in {"GET", "HEAD", "OPTIONS"}
            and user
            and user.is_authenticated
            and not user.is_superuser
            and (setup or http.path.startswith("/api/v3/authenticators/"))
            and recent(http)
        ):
            # Clear the deleted current Django session before SessionMiddleware saves it.
            logout(http)
        return response
