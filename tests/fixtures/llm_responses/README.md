# Canned LLM responses

Recorded provider outputs for deterministic replay in tests. The suite currently drives
everything through the in-process `FakeProvider` (deterministic by construction), so these
are placeholders for when a test needs to pin a *specific* real-provider payload.

Format: one JSON file per scenario, e.g. `classify_data_slow.json`:

```json
{"category": "DATA_SLOW", "priority": "P2", "confidence": 0.88, "entities": {"circle": "Pune"}}
```
