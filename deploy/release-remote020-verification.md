# Nextgen Remote portal publication — 2026-11-17

Portal release 1.0.18 is active at https://softwarenextgen.com.
Product: https://softwarenextgen.com/products/remote

- Home product card, overview, four public guides, and a dedicated illustration added.
- Three private portable packages published in the existing dedicated installer bucket under remote/0.2.0/portal-20261117/.
- Offline manuals added; all original binary/archive members verified unchanged. macOS documentation is outside the signed app bundle.
- Production checks: 268 public pages/assets, 83 manuals, 4486 documentation links/fragments passed; anonymous installer access requires login.
- Temporary ordinary-user fixture completed invitation and TOTP enrollment; all three authenticated downloads passed full size/SHA256 and Range checks. Fixture removed and no emails sent.
- MacBook Chrome DOM/computed geometry: product page images loaded, guides and sign-in links present, homepage card present, no horizontal overflow. Extra hero label removed after detecting overlap.
- Production health reports 1.0.18. Remote relay health remains healthy.
- Rollback: /opt/nextgensoftware/releases/1.0.17 retained; release table/constraint backup at /root/nextgensoftware-remote020-backup on the VM.

The packages contain the previously validated 11e3680 application binaries plus manuals. The subsequent menu placement change in NextgenRemote 7035170 is not included in these immutable packages.
