doc_id: KB-190
# Device APN and Hotspot Configuration — Runbook

## Overview
Use this runbook when data works on the phone but the hotspot/tethering does not, or when a
customer needs the correct APN configured manually after a factory reset or new device.

## Steps
1. Confirm mobile data works in the browser first; if not, follow the APN reset runbook.
2. Go to Settings > Mobile Network > Access Point Names and confirm the default APN
   `internet` is present and selected.
3. To share data, enable Mobile Hotspot under Settings > Connections and set a WPA2
   password.
4. Connect the second device to the hotspot SSID and test a page load.
5. If tethering is blocked, confirm the plan permits hotspot use and no data cap is hit.

## Note
Some prepaid plans meter hotspot data against the same quota as on-device data. Exhausting
the quota throttles both together.
