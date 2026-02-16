# Tools Dashboard

Interactive Panel dashboard for exploring Baserow tools data.

## Quick Start

Run the 'tool_dashboard.py' file and it will generate a HTML file.
We should be able to use the file in Quarto and i can set this .py file to run automatically like weekly, monthly etc. depending on the data update frequency.

```bash
cd dashboard
python tools_dashboard.py
```

## For Quarto Integration (Later)

```markdown
---
title: "Tools Dashboard"
---

<iframe src="dashboard.html" width="100%" height="1200px" style="border:none;"></iframe>
```
