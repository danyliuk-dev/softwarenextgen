#!/usr/bin/env bash
set -euo pipefail
cd /tmp
printf '%s\n' '2119609c603715dcce025f4548c5918e159850b1be3f7a37242e313d6f21c61c  site.tar.gz' '9e0f53b72e8d027e4318e92f00618748c482363ea0dcaf4e7d4165f493a9232e  preview.tar.gz' | sha256sum -c -
[[ ! -e /opt/nextgensoftware/releases/1.0.16 ]]
[[ ! -e /opt/nextgen-component-preview/releases/0.74.0 ]]
mkdir /opt/nextgensoftware/releases/1.0.16 /opt/nextgen-component-preview/releases/0.74.0
tar --no-same-owner -xzf site.tar.gz -C /opt/nextgensoftware/releases/1.0.16
tar --no-same-owner -xzf preview.tar.gz -C /opt/nextgen-component-preview/releases/0.74.0
install -m 600 releases-variable074.json nextgen-releases-variable074.json
[[ -f /opt/nextgensoftware/releases/1.0.16/Nextgen.Web.dll ]]
[[ -f /opt/nextgen-component-preview/releases/0.74.0/wwwroot/_content/NextgenComponents.Blazor/variable-rows.js ]]
echo 'Staged website 1.0.16 and Components 0.74.0; active releases unchanged'
