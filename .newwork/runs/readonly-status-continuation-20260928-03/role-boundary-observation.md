# Role boundary observation

Actual run 04 recorded successful lock tests, parent-context full tests (Memory35 and Loop), unchanged source hashes and empty tracked diff. Its implementer nevertheless spawned internal review agents and repeatedly waited/sent messages, although the outer Loop already schedules independent reviewer and verifier roles.

The current invocation's implementer process was identified by its exact run-04 output path and terminated with SIGTERM after over ten minutes in that role. The production Loop then wrote an ordinary FAIL summary: 746 seconds, planner 1, implementer 1, reviewer 0, verifier 0. No failed artifact or protocol check was changed.

Run 05 narrows invocation instructions: each role performs only its assigned responsibility, with no nested delegation because independent review is provided by the outer Loop. This changes no production code, model storage, retry engine or persistent configuration.

The observation supports investigating clearer role/evidence ownership and avoiding duplicate review. It does not establish a new harness contract, a general latency saving, or a Lesson decision. Long prompts alone did not prevent the overlap; a small explicit role boundary was needed in this experiment.
