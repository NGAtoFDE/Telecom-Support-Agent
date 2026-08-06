doc_id: KB-110
# Slow Data / No Internet — APN Reset

## Overview
Use this runbook when data is connected but pages do not load, or when the mobile data
icon shows but there is no internet. The most common cause is a wrong or corrupted APN
(Access Point Name) configuration on the device.

## Steps
1. Confirm mobile data is ON and the data limit or FUP has not been exhausted.
2. Toggle Airplane mode for 10 seconds to force a fresh data attach.
3. Go to Settings > Mobile Network > Access Point Names (APN).
4. Set the APN to the operator default value `internet` and clear any proxy or port.
5. Save the APN, select it, and reboot the handset.
6. Test by loading a lightweight page; if it works, the APN was the fault.

## Notes
For 5G handsets, ensure "5G Auto" is selected. If speeds are throttled after the FUP
limit, the fix is a data add-on pack, not an APN change — see the fair-usage policy.
