"""Grant an approved invitation to a registered native account, by UUID, with audit."""

import argparse
from app.db.session import SessionLocal
from app.identity.administration import set_capabilities

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--account-id", required=True)
p.add_argument("--capability", action="append", default=[])
p.add_argument("--administrator", required=True)
p.add_argument("--reason", required=True)
a = p.parse_args()
with SessionLocal() as db:
    set_capabilities(db, a.account_id, a.capability, a.administrator, a.reason)
print(
    "Capabilities updated and browser sessions revoked; operator sign-in still requires MFA."
)
