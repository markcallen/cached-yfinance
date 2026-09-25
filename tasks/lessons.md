# Lessons

- A collector that writes timestamped snapshots must own a retention policy.
  Retention must be opt-in for the library, preserve the retrieval key layout,
  and remove only dates strictly older than the configured cutoff.
- A rerun of a release workflow starts from the original workflow SHA but can
  observe a tag created by its prior attempt. Detect tags whose release commit
  has that SHA as its parent before calculating a new SemVer; cover this with
  temporary Git repositories rather than only checking workflow text.
