doc_id: KB-101
# No Signal / No Service — First-Line Diagnostics

## Overview
Use this runbook when a customer reports no bars, "no service", or "emergency calls only"
on the handset. Confirm whether the problem is one device, one location, or the whole
circle before escalating. A single-device fault is resolved here; a suspected regional
outage is a P1 for the NOC.

## Steps
1. Ask the customer to toggle Airplane mode on for 10 seconds, then off, and wait 30s.
2. Restart the handset so it re-registers with the nearest tower.
3. Verify the SIM is seated correctly; reinsert the SIM and check for physical damage.
4. Confirm the network mode is set to "Auto (4G/5G)" and not locked to a single band.
5. Manually select the home network under Settings > Mobile Network > Network Operators.
6. Test the SIM in a second handset to isolate a device fault from a SIM fault.

## When to escalate
If two or more customers in the same circle report total loss of service within the same
hour, treat as a suspected outage (P1) and route to NOC_L2 with the circle name and time.
