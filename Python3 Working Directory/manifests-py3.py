#!/usr/local/sal/Python.framework/Versions/3.8/bin/python3


import os
import pathlib
import plistlib
import sys

import sal
sys.path.append('/usr/local/munki')
import munkilib.updatecheck.manifestutils


def main():
    client_manifest_path = munkilib.updatecheck.manifestutils.get_primary_manifest()
    if client_manifest_path.exists():
        client_manifest = plistlib.loads(client_manifest_path.read_bytes())
    else:
        client_manifest = {}

    # Drop any blank entries and trim WS.
    manifests = [m.strip() for m in client_manifest.get("included_manifests", []) if m]
    if not manifests:
        manifests = ["NO INCLUDED MANIFESTS"]
    sal.add_plugin_results('Manifests', {"included_manifests": "+".join(manifests)})


if __name__ == "__main__":
    main()