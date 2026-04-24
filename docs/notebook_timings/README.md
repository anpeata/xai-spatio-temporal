# Notebook Timing Logs

Use this folder to keep notebook execution timing logs for future reference.

Recommended format:
- One file per notebook run, using the notebook name and a timestamp in the filename.
- Prefer CSV or Markdown tables with one row per executed cell.
- Capture at least: notebook name, cell number, start time, end time, duration seconds, and success or error state.

Suggested workflow:
- Run notebooks with timing enabled when possible.
- Save the resulting timing log here after a successful execution.
- Keep the log close to the notebook run so later comparisons can track performance regressions.