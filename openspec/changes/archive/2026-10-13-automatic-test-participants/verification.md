# Verification

Offline Windows: 34 tests passed, one explicitly opted-in live test skipped. Ruff lint/format and ty passed; the actual configured release analyzer passed all 13 behavioral cases; source/wheel builds succeeded. Configuration loads without member IDs, new speaker999 is accepted without edits, foreign server/channel frames are rejected, solo versus multiple-speaker coverage is explicit. Existing source guards and secret-safe SDK logging remain tested.

No Discord login or live capture was run. New joins no longer abort the temporary test. Initial/move/reconnect phases still require observed nonzero signal; overlap, real DAVE epochs/rekey and OS reboot remain manual qualification gates. Single-person success does not claim multiple-speaker coverage. The operator requested removal of the test participant allowlist.

Same-PR archive supersession is tested against mismatched canonical specs, out-of-scope replacements, missing/self references and cycles; none can bypass the checker. The complete current PR base diff passes archive verification.
