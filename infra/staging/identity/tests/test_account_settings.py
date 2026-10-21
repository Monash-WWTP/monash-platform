"""Run with ak shell in the pinned image; touches only newly-created QA identities."""

import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from authentik.core.models import User
from django.test import RequestFactory

sys.path.insert(0, "/monash-brand")
import account_settings as settings


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username="qa-settings-" + uuid4().hex,
            email=uuid4().hex + "@example.test",
            name="QA",
            attributes={"monash_verified_email": "old@example.test"},
        )
        self.user.attributes["monash_verified_email"] = self.user.email
        self.user.save()
        self.http = RequestFactory().post(
            "/api/v3/flows/executor/monash-account-email/"
        )
        self.http.user = self.user
        from authentik.core.sessions import SessionStore

        self.http.session = SessionStore()
        self.plan = SimpleNamespace(
            context={
                "monash_reauthenticated": {
                    "user": str(self.user.uuid),
                    "at": __import__("time").time(),
                }
            }
        )
        self.http.session[settings.SESSION_KEY_PLAN] = self.plan
        self.request = SimpleNamespace(
            user=self.user, http_request=self.http, context={"prompt_data": {}}
        )

    def tearDown(self):
        self.user.delete()

    def test_shared_email_layout_renders_distinct_actions(self):
        from django.template.loader import render_to_string

        cases = {
            "monash_confirmation": "Confirm account",
            "monash_recovery": "Reset password",
            "monash_email_change": "Confirm email change",
            "monash_email_changed": None,
        }
        for template, action in cases.items():
            rendered = render_to_string(
                "email/" + template + ".html",
                {"url": "https://accounts.example.test/confirm?token=synthetic&test=1"},
            )
            self.assertIn("CitizenFlood logo", rendered)
            self.assertIn("max-width:560px", rendered)
            self.assertEqual(rendered.count('id="confirm"'), int(action is not None))
            if action:
                self.assertIn(action, rendered)
                self.assertIn("token=synthetic&amp;test=1", rendered)

    def test_expired_browser_session_goes_to_signin_without_trusting_return_input(self):
        from django.contrib.auth.models import AnonymousUser

        http = RequestFactory().get(
            "/if/flow/monash-account-profile/?next=https://evil.test"
        )
        http.user = AnonymousUser()
        http.session = {}
        response = settings.AccountSettingsGuard(
            lambda r: SimpleNamespace(status_code=200)
        )(http)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("evil.test", response["Location"])

    def test_stale_auth_cannot_be_made_recent_by_delayed_confirmation(self):
        self.plan.context["monash_reauthenticated"] = {
            "user": str(self.user.uuid),
            "at": 0,
        }
        self.request.context["prompt_data"] = {"confirm": True}
        self.assertFalse(settings.confirm_security(self.request))
        self.assertFalse(settings.sign_out_all(self.request))

    def test_invalid_native_setup_preserves_session_and_does_not_revoke(self):
        self.assertTrue(settings.mark_recent(self.request))
        self.http.path = "/api/v3/flows/executor/default-authenticator-totp-setup/"
        self.http.session["pending-qa"] = "retained"
        guard = settings.AccountSettingsGuard(
            lambda r: SimpleNamespace(status_code=200)
        )
        with (
            patch.object(settings, "native_setup", return_value=True),
            patch.object(settings, "send_event", return_value=True) as send,
        ):
            self.assertEqual(guard(self.http).status_code, 200)
            send.assert_not_called()
            self.assertEqual(self.http.session["pending-qa"], "retained")

    def test_native_mutation_rolls_back_when_revocation_delivery_fails(self):
        from authentik.stages.authenticator_totp.models import TOTPDevice

        self.assertTrue(settings.mark_recent(self.request))
        self.http.path = "/api/v3/authenticators/totp/"
        self.http.session["pending-qa"] = "retained"

        def create_device(http):
            TOTPDevice.objects.create(
                user=self.user, name="QA new authenticator", confirmed=True
            )
            http.session.pop("pending-qa", None)
            return SimpleNamespace(status_code=200)

        guard = settings.AccountSettingsGuard(create_device)
        with patch.object(settings, "send_event", return_value=False):
            self.assertEqual(guard(self.http).status_code, 503)
        self.assertFalse(TOTPDevice.objects.filter(user=self.user).exists())
        self.assertEqual(self.http.session["pending-qa"], "retained")
        self.assertTrue(self.http.user.is_authenticated)
        with patch.object(settings, "send_event", return_value=True):
            self.assertEqual(guard(self.http).status_code, 200)
        self.assertEqual(TOTPDevice.objects.filter(user=self.user).count(), 1)
        self.assertFalse(self.http.user.is_authenticated)

    def test_reauthentication_does_not_accept_api_tokens_and_marks_completion(self):
        from authentik.stages.password.models import PasswordStage
        from authentik.flows.models import FlowStageBinding

        self.assertNotIn(
            "authentik.core.auth.TokenBackend",
            PasswordStage.objects.get(name="monash-account-reauthenticate").backends,
        )
        bindings = list(
            FlowStageBinding.objects.filter(
                target__slug="monash-account-security"
            ).order_by("order")
        )
        self.assertEqual(
            bindings[2].stage.name, "monash-account-authentication-complete"
        )
        self.assertFalse(bindings[2].evaluate_on_plan)
        self.assertTrue(bindings[2].re_evaluate_policies)

    def test_authentication_checkpoint_is_automatic_and_does_not_renew_on_form(self):
        from authentik.flows.models import Flow
        from authentik.flows.planner import FlowPlanner

        planner = FlowPlanner(Flow.objects.get(slug="monash-account-profile"))
        planner.use_cache = False
        planned = planner.plan(self.http)
        planned.bindings = planned.bindings[2:]
        planned.markers = planned.markers[2:]
        stage = planned.next(self.http)
        self.assertEqual(stage.stage.name, "monash-account-profile")
        proof = dict(planned.context["monash_reauthenticated"])
        planned.next(self.http)
        self.assertEqual(planned.context["monash_reauthenticated"], proof)

    def test_profile_allowlist(self):
        self.request.context["prompt_data"] = {"name": "  Research volunteer  "}
        self.assertTrue(settings.save_profile(self.request))
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "Research volunteer")
        self.request.context["prompt_data"] = {
            "name": "Fake",
            "email": "attacker@example.test",
        }
        self.assertFalse(settings.save_profile(self.request))
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "Research volunteer")

    def prepare(self, email):
        self.request.context["prompt_data"] = {"candidate_email": email}
        self.assertTrue(settings.prepare_email_change(self.request))

    def test_email_stays_old_until_verified_and_latest_attempt_wins(self):
        old = self.user.email
        uid = self.user.uuid
        self.prepare(uuid4().hex + "@example.test")
        first = dict(self.plan.context)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, old)
        self.prepare(uuid4().hex + "@example.test")
        latest = dict(self.plan.context)
        self.plan.context = first
        self.request.context["prompt_data"] = {"confirm": True}
        with patch.object(settings, "send_event") as deliver:
            self.assertFalse(settings.complete_email_change(self.request))
            deliver.assert_not_called()
        self.plan.context = latest
        self.plan.context["is_restored"] = SimpleNamespace(user=self.user)
        with (
            patch.object(settings, "send_event", return_value=True),
            patch.object(settings, "notify_old_email"),
        ):
            self.assertTrue(settings.complete_email_change(self.request))
            self.http.user = self.user
            self.assertFalse(settings.complete_email_change(self.request))
        self.user.refresh_from_db()
        self.assertEqual(self.user.uuid, uid)
        self.assertEqual(self.user.email, latest["email"])
        self.assertEqual(self.user.attributes["monash_verified_email"], self.user.email)

    def test_failed_receiver_rolls_back_email(self):
        old = self.user.email
        self.prepare(uuid4().hex + "@example.test")
        self.plan.context["is_restored"] = SimpleNamespace(user=self.user)
        self.request.context["prompt_data"] = {"confirm": True}
        with patch.object(settings, "send_event", return_value=False):
            self.http.user = self.user
            self.assertFalse(settings.complete_email_change(self.request))
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, old)

    def test_expired_or_different_user_confirmation_is_rejected(self):
        self.prepare(uuid4().hex + "@example.test")
        self.plan.context["is_restored"] = SimpleNamespace(user=SimpleNamespace(pk=-1))
        self.request.context["prompt_data"] = {"confirm": True}
        self.assertFalse(settings.complete_email_change(self.request))
        self.plan.context["is_restored"] = SimpleNamespace(user=self.user)
        self.user.refresh_from_db()
        attempt = dict(self.user.attributes[settings.PENDING])
        attempt["expires"] = 0
        self.user.attributes[settings.PENDING] = attempt
        self.user.save()
        self.plan.context["monash_email_attempt"] = attempt
        self.assertFalse(settings.complete_email_change(self.request))

    def test_password_and_signout_fail_closed_and_preserve_identity(self):
        self.user.set_password("QA-original-password")
        self.user.save()
        uid = self.user.uuid
        self.request.context["prompt_data"] = {
            "new_password": "QA-new-password-long",
            "repeat_password": "QA-new-password-long",
        }
        with patch.object(settings, "send_event", return_value=False):
            self.assertFalse(settings.change_password(self.request))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("QA-original-password"))
        with patch.object(settings, "send_event", return_value=True) as send:
            self.assertTrue(settings.change_password(self.request))
            self.assertEqual(send.call_args.args[1], "credentials.changed")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("QA-new-password-long"))
        self.assertEqual(self.user.uuid, uid)
        self.http.user = self.user
        self.http.session[settings.SESSION_KEY_PLAN] = self.plan
        self.request.context["prompt_data"] = {"confirm": True}
        with patch.object(settings, "send_event", return_value=True) as send:
            self.assertTrue(settings.sign_out_all(self.request))
            self.assertEqual(send.call_args.args[1], "sessions.revoked")

    def test_flow_plan_binds_current_user_before_password(self):
        from authentik.flows.models import Flow
        from authentik.flows.planner import FlowPlanner

        for slug in [
            "monash-account-profile",
            "monash-account-email",
            "monash-account-password",
            "default-password-change",
            "monash-account-signout-all",
            "monash-account-security",
        ]:
            planner = FlowPlanner(Flow.objects.get(slug=slug))
            planner.use_cache = False
            planned = planner.plan(self.http)
            self.assertEqual(planned.context["pending_user"].pk, self.user.pk)

    def test_security_change_clears_current_provider_session(self):
        from authentik.core.models import AuthenticatedSession, Session
        from authentik.stages.user_login.middleware import BoundSessionMiddleware
        from django.http import HttpResponse

        self.http.session.save()
        AuthenticatedSession.objects.create(
            user=self.user,
            session=Session.objects.get(session_key=self.http.session.session_key),
        )
        self.http.session["authenticatedsession"] = AuthenticatedSession.objects.get(
            session_id=self.http.session.session_key
        )
        self.request.context["prompt_data"] = {"confirm": True}
        with patch.object(settings, "send_event", return_value=True):
            self.assertTrue(settings.sign_out_all(self.request))
        self.http.user_switching_token = None
        self.http.user_switching_token_needs_update = False
        response = BoundSessionMiddleware(lambda r: HttpResponse()).process_response(
            self.http, HttpResponse()
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AuthenticatedSession.objects.filter(user=self.user).exists())
        self.assertFalse(self.http.user.is_authenticated)

    def test_direct_api_sensitive_writes_require_fresh_same_user_auth(self):
        guard = settings.AccountSettingsGuard(
            lambda r: SimpleNamespace(status_code=200)
        )
        self.http.path = "/api/v3/authenticators/totp/1/"
        self.assertEqual(guard(self.http).status_code, 403)
        self.assertTrue(settings.mark_recent(self.request))
        with patch.object(settings, "send_event", return_value=True):
            self.assertEqual(guard(self.http).status_code, 200)
        self.http.path = "/api/v3/core/users/" + str(self.user.pk) + "/"
        self.assertEqual(guard(self.http).status_code, 403)


suite = unittest.defaultTestLoader.loadTestsFromTestCase(SettingsTests)
result = unittest.TextTestRunner(verbosity=2).run(suite)
if not result.wasSuccessful():
    raise SystemExit(1)
