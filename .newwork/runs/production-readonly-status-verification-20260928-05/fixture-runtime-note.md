# Disposable fixture runtime correction

The Git archive fixture contained the copied initialized ledger/projections but not its ignored `.newwork/.lock` runtime file. The reviewer status command therefore correctly returned `invalid_input` for this incomplete fixture; this is not a code assertion failure.

The main orchestrator supplied the existing zero-byte runtime lock by copying it from the real repo into the disposable fixture only, without overwriting a destination, changing modes/owners, editing any ledger/projection/source, or changing sandbox settings. The original repo lock was read, not modified. Initialized read-only status can now be checked against this complete fixture. All source hashes remain unchanged.
