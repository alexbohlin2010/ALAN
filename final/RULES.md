# RULES

Every AI agent (Claude Code or otherwise) reads this file at the start of every session that touches `final/`, and follows it for the whole session. If a request conflicts with these rules, the agent stops and asks. It does not quietly pick one side.

This file is kept in git. Only a human changes it, and the reason for each change goes in the commit message.

## Ethos

The humans are the pilots. The AI is an instrument: fast at finding data, prototyping, transforming and engineering, but it does not shape the narrative, choose the architecture, or fill gaps with plausible-looking guesses. When in doubt, the agent does less and asks more. We would rather have an honest empty cell than a confident wrong one, and a simple system we understand rather than a clever one we don't.

## 1. Human control

1. Humans decide the story, the design and the architecture. The agent may propose options, kept short, with trade-offs stated, and then waits for a decision.
2. The agent does not add narrative framing, interpretive claims or conclusions to the visualization, captions or docs unless asked to.
3. The agent prefers the simplest solution that works. Before adding a new dependency, framework, build step, abstraction or file layout, it asks first.
4. One narrowly scoped task at a time. The agent does not expand scope on its own. It notes anything else it spots in the log as a suggestion.
5. The agent never commits, pushes, merges or deletes unless a human asks for that specific action.

## 2. Data integrity

1. **Raw data is never edited without a request.** Raw files live in `final/data/raw/` (and any file a human marks as raw). Agents read them and never overwrite, reformat, re-save, rename or delete them. All transformations write new files somewhere else.
2. **No guessing.** If no source can be found for a value, the cell stays empty and the gap is reported. An estimate is made only when a human asks for one *and* it follows an established, cited method.
3. **Every value is labelled** with one of:

   | Label | Meaning | Required alongside |
   |---|---|---|
   | `measured` | Directly observed by an instrument or survey (satellite radiance, a spectrometer reading, a field count) | source dataset + link |
   | `documented` | Stated by an authoritative source (city report, utility, published paper) | source link or citation |
   | `inferred` | Derived by stated, deterministic logic from measured or documented values | the rule used + its inputs |
   | `estimated` | Produced by an established methodology when a human asked for an estimate | method citation + note of who requested it |

   Empty cells carry no label, just a note saying what was searched.
4. Every transformation is a script in the repo, not a one-off chat edit, so it can be rerun from raw data and reviewed.
5. Units, coordinate systems, date ranges and filters are written down next to the data they apply to, never just assumed.

## 3. Audit

1. **Cross-agent check:** any manipulated dataset is compared against its original by a *separate* agent session with fresh context (ideally a different model). That agent looks for broken invariants (row counts, totals, ranges, units, duplicates, unexpected changes) and anything concerning, then writes up what it found.
2. **Human spot check:** the agent picks N random rows (recording the random seed) and lists them with their sources. A **human** re-checks them against the original by hand, and the match rate is recorded. Agents never carry out or report the human check themselves.
3. Audit results are written to `final/audits/` and linked from the log.

## 4. Logging

1. **Every AI step is logged** in `final/AI_LOG.md`: date, tool, exact model ID, the human's exact prompt (verbatim), what the agent did, and which files it created or changed.
2. The agent appends to the log. It never rewrites or deletes earlier entries.
3. If an AI step produced or changed data values, the log entry also gives the labels used and any cells left empty.

## 5. Bias mitigation: context refresh

1. Agents do not run long sessions or compress their context to keep going. Once a narrowly scoped task is done, or when context use reaches about **30%**, the agent writes a handoff file to `final/handoffs/YYYY-MM-DD_<topic>.md` (what was done, decisions made *by humans*, open questions, next steps) and the human starts a fresh session from it.
2. A handoff records facts and decisions, not the agent's own opinions or preferred direction, so the next session isn't steered by the last one.
3. A fresh session reads this file and the latest handoff before doing anything else.

## 6. Scope of use

| Phase | AI is used for | AI is not used for |
|---|---|---|
| Research & data collection | Finding datasets, sources and constraints; locating data for an idea the humans have already formed | Generating the narrative or ideas |
| Prototyping | Quick approximations of the final look and function | Locking in final design decisions |
| Data transformation | Scripted, labelled, audited transformations (sections 2 to 4) | Filling gaps, silent cleaning |
| Final software & rendering | Identifying rendering options; building to *our* architecture and design | Choosing or growing the architecture on its own |
