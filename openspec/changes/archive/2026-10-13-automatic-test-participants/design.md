# Design
Settings retain the token, server, two channels and phase duration. No member-ID list is read. The sink checks source server and channel and discovers speaker IDs from frames. New channel occupants do not abort capture. Moving the bot outside the configured channels still aborts. Each phase passes when capture is ready and at least one speaker produces nonzero PCM; a separate multi-speaker field requires two speakers in every phase and remains false for solo tests. This is bounded receiver acceptance, not the long-running application's coordinator; reconnect/rekey/OS and overlap manual gates remain explicit.

Audio remains transient. The metadata output has only IDs/counts/readiness; no voice or credentials. No real server testing is introduced.
