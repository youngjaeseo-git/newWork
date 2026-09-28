# Actual-model run 03 protocol failure

Run 03 executed planner, implementer and reviewer using actual model calls. Implementer ran all four lock tests and the injected-parent-environment Loop/Memory35 suite successfully, without source changes. Reviewer checked the source and attempted tests; temporary-directory creation was denied in its read-only sandbox. Its final artifact expressed PASS, but bytes ended with `VERDICT: PASS\n\n`.

Production Loop correctly rejected the artifact because the actual final line was empty. Summary: 709 seconds, planner 1, implementer 1, reviewer 1, verifier 0, Final FAIL, invalid reviewer verdict. No result was emitted. The artifact and verdict parser were not modified.

Run 04 is a new actual execution with a clearer final-line prompt and focused, capability-aware review instructions. It does not reuse the failed run ID or reinterpret run 03 as PASS.
