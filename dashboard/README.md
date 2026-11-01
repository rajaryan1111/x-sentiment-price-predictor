# Dashboard

Every offline pipeline run writes a standalone `dashboard.html` alongside the
generated SVG, evaluation report, metrics, predictions, and one-page outlook. The
HTML embeds the SVG and styles inline, makes no network requests, and includes
sample counts, quote currency, forecast errors, strategy risk metrics, source
freshness, licensing, and explicit missing-sentiment messaging. It does not run a
server or claim that the sentiment model was empirically validated when no posts
were scored.

Open `dashboard.html` in a browser after running the documented pipeline. The
dashboard links to the sibling Markdown and JSON artifacts.
