doc_id: KB-120
# Frequent Call Drops — Diagnostics

## Overview
Use this runbook when calls connect but disconnect mid-conversation, or fail to connect at
the first attempt. Common causes are VoLTE misconfiguration, poor signal at a specific
location, or a handset software issue.

## Steps
1. Confirm whether drops happen everywhere or only at one location (home, office, lift).
2. Enable VoLTE / "HD Voice" under Settings > Mobile Network so calls use the 4G/5G core.
3. Toggle Airplane mode to force re-registration, then place a test call.
4. Turn on Wi-Fi Calling (VoWiFi) as a fallback where mobile signal is weak.
5. Update the handset software; carrier settings updates often fix call setup issues.
6. Test the SIM in another handset to rule out a device fault.

## Escalation
If drops cluster at one location and affect multiple customers, raise to NOC_L2 with the
location and approximate drop rate so the radio team can inspect the serving cell.
