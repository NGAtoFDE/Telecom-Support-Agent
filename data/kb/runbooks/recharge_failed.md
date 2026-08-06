doc_id: KB-140
# Recharge Failed but Money Deducted — Runbook

## Overview
Use this runbook when a prepaid customer says a recharge failed but the amount was debited
from their bank or wallet. The typical error is `ERR-RCH-402` (payment captured, recharge
not applied). Most such cases auto-reconcile; the rest are routed to Billing Operations.

## Steps
1. Capture the recharge amount, date, time and the payment method used.
2. Ask for the payment reference or transaction id from the bank/wallet SMS.
3. Check the recharge status in the self-care app under "Recharge history".
4. If status is "Pending", advise that auto-reconciliation completes within 30 minutes.
5. If the amount is debited and not credited after the window, route to BILLING_OPS with
   the transaction id for a refund or manual recharge.

## Note
Do not ask for card numbers, CVV, UPI PIN or OTP. Only the transaction reference is needed.
