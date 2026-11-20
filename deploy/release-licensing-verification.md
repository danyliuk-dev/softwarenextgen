# Nextgen Remote licensing release verification


Desktop source c439058, version 0.4.1; portal 1.1.1. This first stage enforces
licensing only for Nextgen Remote. Components and Report Engine binaries and
download entitlements are unchanged. Customers sign in by invitation/password;
administrators still require MFA. Existing enabled accounts received two total
perpetual legacy Remote licenses with three installations each.

- Rust tests: 38 passed, 3 native-session tests ignored. Dedicated signed-lease
  checks reject a wrong key, device, product, expiry, excessive lifetime and clock
  rollback. Installed Linux binary rejected a modified cached permission.
- Isolated PostgreSQL/HTTP tests passed administrator MFA/TOTP replay/recovery,
  customer password login, RBAC, CSRF, registration without access or email, signed
  device challenges, replay/wrong-key denial, suspension, device deactivation and
  concurrent approval at a one-device limit. No production invitations were sent.
- Linux, MacBook and existing Windows VM native builds activated through a
  temporary ordinary website account and independently validated real signed
  permissions. Suspending that license returned valid=false on all three; Linux
  real headless sharing and package/relay access were denied. Resuming restored
  access without reactivation. Offline fallback accepted the valid cached lease.
- Actual automatic upgrade 0.4.0 -> 0.4.1 passed on all three installed apps, using
  license-device credentials for private downloads. Helpers acknowledged GUI
  startup, installed binaries matched native candidates, and macOS deep/strict
  signature verification retained the original signing identity.
- Production relay independently rejects unlicensed host registration. An isolated
  licensed WebSocket tunnel preserved synthetic bytes; closing registration closed
  its active viewer tunnel. A regression also covers both relay URL variants.
  Relay binary SHA-256: 9f5b29c59270a7915762b40725949df398ba651143652c23b19ee8147c15a2a1.
- Signed immutable packages: remote/0.4.1/c439058-20261117/. Old unlicensed download
  revisions were hidden, with private artifacts retained. Portal/relay services
  are isolated; DME application services were not restarted.
- Visible foreground Linux Chrome checked client creation, license issuance,
  separate editing, suspension/limit/date persistence, search and mobile layout.
  Compact admin uses Clients/Licenses/Devices tabs, collapsed two-column creation
  forms, 25-row pages and a dedicated license editor.
- Temporary production QA user, license, activations and audit entries were
  removed. QA device tokens, private keys and cached leases were removed on all
  three systems. Installed apps were reopened for the owner's personal activation.
- Public checks passed 268 pages/assets, 83 guides and 4487 live links/fragments.
  Evidence and non-secret logs: dist/verification/licensing/.

Limits: local device keys use protected per-user files, not hardware binding.
Binary patching or copying all account-accessible credential files cannot be
claimed impossible. Offline grants last at most seven days; relay entitlement is
rechecked every five minutes. No new real desktop audio/input regression is claimed.
