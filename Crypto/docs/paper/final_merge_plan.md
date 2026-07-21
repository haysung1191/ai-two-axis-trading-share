# Final Merge Plan

This file defines how to collapse the current paper kit into one final manuscript.

## Source documents

- `abstract.md`
- `introduction.md`
- `method.md`
- `results_section.md`
- `discussion.md`
- `limitations.md`
- `conclusion.md`
- `related_work.md`

## Recommended final section order

1. Abstract
2. Introduction
3. System / Method
4. Related Work
5. Experimental Setup
6. Results
7. Discussion
8. Limitations
9. Conclusion

## Merge rules

- Remove duplicated framing between `introduction.md`, `method.md`, and `discussion.md`.
- Keep the "not a profitability claim" language, but do not repeat it excessively.
- Keep one strong thesis sentence and reuse it consistently:
  - the contribution is a governance-aware, reproducible strategy validation framework
- Convert raw snapshot wording into benchmark wording once clean runs are available.

## Final tone requirements

- systems-focused
- empirically disciplined
- conservative in claims
- explicit about scope

## Appendix candidates

- prompt template details
- strategy category definitions
- decision rule tables
- artifact schema summary
- additional rejection-reason plots
