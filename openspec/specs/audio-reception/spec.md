# audio-reception Specification

## Purpose
Provide reusable attributed Discord voice audio to Python applications without owning consumer speech or analytics logic.

## Requirements

### Requirement: Attributed audio frames
The receiver SHALL deliver timestamped frames with server, channel, member, sequence and stream timing metadata. Consumers SHALL choose Opus or 48000 Hz stereo PCM. Unknown or stale speaker identities MUST be dropped.

#### Scenario: Speaker mapping changes
- **WHEN** an SSRC is rebound to a different member or a voice connection restarts
- **THEN** queued old audio and decoder state are discarded before new attributed delivery

### Requirement: Maintained encryption and fail-closed handling
The receiver MUST use maintained transport and SDK DAVE implementations. Audio without valid transport authentication or a ready DAVE session MUST be dropped, except known plaintext silence. The receiver MUST recover delivery after session readiness returns without exposing audio, keys or tokens in logs.

#### Scenario: Epoch transition
- **WHEN** a session temporarily cannot decrypt an incoming frame
- **THEN** that frame is discarded and later valid frames can be delivered

### Requirement: Bounded independent streams
The receiver SHALL bound ingress, stream count and reorder buffers. Loss, duplicate, malformed and out-of-order packets in one stream MUST NOT stop other streams. PCM loss concealment SHALL be bounded; Opus consumers MUST NOT receive fabricated encoded data.

#### Scenario: Slow consumer
- **WHEN** consumers cannot keep up with incoming packets
- **THEN** bounded queues drop excess audio and report drop counters instead of growing without limit

### Requirement: Owned lifecycle and observable health
Start, stop, disconnect and cancellation SHALL release socket listeners, receiver tasks and sink resources. Each sink MUST close exactly once per listening session. Health SHALL distinguish capture readiness, actual frame activity and degraded delivery.

#### Scenario: Cancel listening
- **WHEN** a listener is cancelled while a sink is processing
- **THEN** the receiver task terminates and every sink closes once
