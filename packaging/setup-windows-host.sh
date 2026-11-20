#!/usr/bin/env bash
# One-time host prerequisites; run from the Linux iMac account.
set -euo pipefail
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt-get install -y wine64 wine32:i386 qemu-kvm libvirt-daemon-system libvirt-clients ovmf swtpm swtpm-tools virt-manager xorriso
"$(dirname -- "${BASH_SOURCE[0]}")/toolbin/wine" --version
virsh -c qemu:///system list --all
