# Lessons

- A collector that writes timestamped snapshots must own a retention policy.
  Retention must be opt-in for the library, preserve the retrieval key layout,
  and remove only dates strictly older than the configured cutoff.
