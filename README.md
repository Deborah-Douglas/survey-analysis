# Reporting Under Pressure: Survey Dashboard

An interactive dashboard for the November 20, 2026 survey snapshot. It presents aggregate results from 421 eligible respondents: 298 who finished and 123 who submitted partial responses. Each question uses the available eligible answers. The dashboard has topic navigation, respondent-group comparisons, chart and table views, question wording, and a methods section. It uses HTML, CSS, and vanilla JavaScript. No build step, API key, or backend is needed.

## Upload to GitHub

1. Unzip the download. Open the extracted `reporting-under-pressure-github` folder.
2. Create or open your GitHub repository. Upload the **contents** of the extracted folder, not the ZIP itself. Keep `index.html`, `styles.css`, `app.js`, and `survey-data.js` together at the repository root. The `tools` folder is optional; it is not needed to run the dashboard.
3. Commit the files. You can keep this as a code repository without publishing a site.

## Publish with GitHub Pages (optional)

Once the files are on `main`, go to **Settings → Pages → Build and deployment**. Choose **Deploy from a branch**, select **`main`** and **`/(root)`**, then click **Save**. If your default branch has a different name, select that branch. GitHub documents the settings in [Configuring a publishing source for your GitHub Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

Check who can access the site before enabling Pages. The attached Perplexity preview and a GitHub Pages deployment are separate; the dashboard itself does not require a login. Anyone who can load the site can retrieve the bundled aggregate data.

## Preview or edit locally

Open `index.html` directly in a browser, or run the following from the project root and open `http://localhost:8000`:

```sh
python3 -m http.server 8000
```

| File | Purpose |
| --- | --- |
| `index.html` | Page structure, navigation, and snapshot heading |
| `styles.css` | Responsive styles and [Northwestern’s purple palette](https://www.northwestern.edu/brand/visual-identity/color-palettes/) |
| `app.js` | Group filters, comparisons, chart and table rendering, and methods |
| `survey-data.js` | Precomputed counts and denominators by question and group |
| `tools/build-survey-dashboard.py` | Optional, standard-library-only script to regenerate the aggregates from the original Qualtrics export |

The typeface is loaded from Fontshare when available; a system font is used as fallback. The dashboard data and interactions do not require internet access when running locally.

## Data and privacy

This package contains aggregate counts only. It does not include the original Qualtrics export, response IDs, contact details, or raw open-ended answers. A few written-response themes are summarized without direct quotes. Keep any survey export outside the repository; `.gitignore` excludes CSVs as an additional safeguard. These are descriptive results, not estimates for U.S. journalists overall.

The archive already contains `survey-data.js`. To reproduce this snapshot from your private copy of the original export, run:

```sh
python3 tools/build-survey-dashboard.py "/path/to/private/qualtrics-export.csv" survey-data.js
```

The script checks totals against the November 20, 2026 snapshot. For a new wave, review question mappings, cohort rules, and validation totals, then update the dated and sample-specific language in `index.html` and `app.js`. Review the regenerated aggregates before uploading.
