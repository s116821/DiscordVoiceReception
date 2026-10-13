# Why
The temporary-server harness currently requires a participant consent allowlist and aborts on new arrivals. The operator wants ordinary channel membership to determine capture, including a one-person initial test.

# What Changes
- Remove configured participant IDs and membership-based aborts.
- Accept all received speakers in the configured temporary voice channels.
- Report one-person phase success separately from exercised multiple-speaker coverage.
- Preserve explicit live opt-in, temporary-only server identity, bounded capture and metadata-only output.

# Capabilities
## Modified Capabilities
- `live-qualification`: automatic participant discovery in disposable test channels.

# Impact
Qualification example, offline guard tests and setup documentation only; library runtime unchanged.
