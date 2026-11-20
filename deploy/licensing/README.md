# Nextgen Remote licensing rollout

Portal 1.1.0 introduced customers, licenses and device activations. This first
release enforces product access only for Nextgen Remote. Components/Reports code
and their download entitlements are unchanged. Customer sign-in is password-based;
administrator sign-in still requires MFA. Public guides and previews stay public.

Administration: /admin/licenses. Register first name, last name, private/organization,
organization name where applicable, and email. Registration grants no license and
sends no email. Assign a product license, then use Users & invitations to send the
normal invitation. Manage edition, expiry, installation count, suspension and device
deactivation. Active-device allocation is serialized by locking the license row.

The one-time migrate-existing-access.sql grants the two existing enabled accounts
perpetual Remote licenses with three activations, preserving prior access. It uses
a migration marker and a unique legacy index; rerunning does not create more grants.
Do not rerun this as a recurring user provisioning rule.

License signing key: /etc/nextgensoftware/license-signing-key.pem, mode 0600,
owned by the portal service. This key is separate from the local update-manifest
signing key. Never copy either private key into sources or packages. Client code
pins assets/license-public-key.der. Back up keys privately and coordinate rotation
with a client update before changing the verification trust root.

Devices generate P-256 keys. A CSRF-protected owner action consumes a ten-minute
activation code. Lease refresh uses a hashed bearer token plus a single-use,
60-second challenge signed by the device key. Signed runtime permissions expire
within seven days and never after the license's end. The relay checks active device
entitlement every five minutes and cancels active tunnels when registration ends.
Offline revocation is bounded by the already issued lease; no claim of tamper-proof
local execution or hardware-backed device keys is made in this release.

Production state: /opt/nextgensoftware/current -> releases/1.1.1. Pre-change private
DB backup: /root/nextgensoftware-licensing-backup/database.dump. Previous portal
1.0.19 and previous relay release remain for rollback. New schema is additive.
The relay licensing switch is in nextgen-relay.service.d/licensing.conf.

Validation: tests/licensing-integration.py runs only against the explicitly named
local nextgen_license_test DB on port 55462; mail delivery must be disabled.
It deliberately clears synthetic fixtures in that database. tests/licensing-browser.py
uses a separate visible Chrome QA profile and local synthetic admin cookies.
Production tests used a separate temporary example.invalid account without email.

Portal 1.1.1 compacts the admin into Clients / Licenses / Devices tabs, filtered
25-row tables, collapsed creation forms and a separate license editor. Search
matches client names, email and organization across all three views.

## Version 1.2.0

Remote 0.4.2 signs host registration and update package requests with its
device key. Proofs bind the action to the room or package digest, expire within
a short clock-skew window, and have a database-enforced single-use nonce.
Bootstrap credentials present when this migration first runs can download the
0.4.2 package using the previous protocol. The relay requires proof immediately
upon deployment. Devices are ranked by approval time and ID, so reducing the
installation count keeps the oldest devices eligible without deleting activations.

The administrator sets the independent concurrent session limit on each license.
Existing licenses default to 16, the previous relay-wide capacity. A slot covers
a pending or active viewer, across all rooms on the production relay process.
New connections read current limits. Existing tunnels recheck within 60 seconds
and release their slots on termination. Multiple relay replicas would require
shared session accounting before scaling out.
