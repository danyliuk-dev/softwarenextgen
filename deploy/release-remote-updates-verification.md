# Nextgen Remote automatic updates — 2026-11-17


Release 0.3.3 binaries were built locally from 11f13f6 on Linux, MacBook, and
in the existing Windows 11 VM. The private installer channel is served by portal
1.0.19; immutable bucket prefix: remote/0.3.3/11f13f6-20261117/.

- Rust suite: 37 passed, 3 ignored. Unix installer integration: 3 passed,
  including failed-start rollback, argument preservation, and unsafe archive rejection.
- Native Windows isolated rollback restored original executable bytes and quoted
  arguments after the new executable exited before startup acknowledgement.
- Real startup upgrades reached 0.3.3 on all three installed applications. Each
  helper logged successful new-app startup; installed executables matched their
  native release candidates. macOS deep/strict codesign validation passed using
  the existing signing identity. Linux retained both central-server arguments.
- An initial macOS candidate safely rejected an invalid codesign requirement
  invocation. The inline requirement syntax was corrected; 0.3.1 was withdrawn.
  Corrected macOS automatic upgrades 0.3.1 -> 0.3.2 -> 0.3.3 then passed.
- Fixed the startup timer being restarted by frequent UI state changes. Production
  nginx recorded six 0.3.3 API requests across the three app starts, unchanged on
  a subsequent check after more than 30 seconds; authorized idle apps do not loop.
- Real password/TOTP enrollment and device approval tests covered CSRF, single-use
  codes, pending/anonymous denial, authorized byte ranges, revocation, and disabled
  accounts. Temporary MFA account, invitations, device grants and audit entries
  were removed; no emails were sent. QA credentials were removed from all devices.
- Public-access regression passed 268 pages/assets and 83 manuals. Installer and
  account routes still require login. Live documentation link validation passed
  83 guides / 4486 links. Public packages were not enabled.
- Release manifests are signed with a local private key; clients pin its public
  key and verify signature, expiry, platform, byte count and SHA-256 before install.
  Installation waits while remote sessions are active and rolls back on failed start.
- Personal MFA authorization is intentionally left to the user on each computer:
  Help -> Updates -> Authorize this computer. Test credentials are not retained.
  This verifies updater behavior, not a new remote input/audio regression run.

Live stable manifest exactly matched the local signed 0.3.3 release. All three
package API endpoints returned 401 without device credentials. Portal 1.0.19
remains deployed; only the portal service was restarted during publication.
