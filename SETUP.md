# Professional GitHub profile (terminal style)

Same idea as the profile you sent me, but it runs on your own data.

Every asset is generated from the GitHub API, then refreshed by a scheduled
GitHub Action, so the profile stays current without you touching it.

## What's inside

```
README.md                     the profile page itself
assets/contrib-heatmap.svg    contribution graph (53 weeks, animated)
assets/stats.svg              streak / repo / language card
assets/ascii-portrait.svg     your photo as ASCII art
scripts/gh.py                 GitHub API client (REST + contributions page)
scripts/build.py              builds every asset, then rewrites the featured repos table
scripts/make_heatmap_svg.py   contribution graph renderer
scripts/render_stats_svg.py   stats card renderer
scripts/make_ascii_svg.py     photo -> ASCII SVG
.github/workflows/update-profile-art.yml   daily refresh
```

## Setup (10 minutes)

1. Create a repository whose name is **exactly your GitHub username**
   (e.g. `github.com/new` -> `your-login/your-login`). Public, no template.
   GitHub shows a green "you found a secret" note: that repo's `README.md`
   becomes your profile page.

2. Drop these files into it and push:

   ```bash
   git init && git add . && git commit -m "feat: terminal-style profile"
   git branch -M main
   git remote add origin https://github.com/<your-login>/<your-login>.git
   git push -u origin main
   ```

3. Make your portrait:

   ```bash
   pip install -r requirements.txt
   python scripts/make_ascii_svg.py photo.jpg assets/ascii-portrait.svg --width 56
   ```

   A head-and-shoulders photo, plain background, face centred works best.
   `--width 44` for a chunkier look, `--width 64` for more detail. Bump
   `--contrast 1.6` if the result looks washed out.

4. Build the data assets:

   ```bash
   python scripts/build.py --user <your-login>
   ```

   That writes the graph, the stats card and the featured-repos table.
   With no token you get 60 requests/hour, which is plenty for one run.
   For a higher limit: `export GITHUB_TOKEN=ghp_...`

5. Edit the personal bits in `README.md`: `whoami --verbose` block, the three
   badges at the bottom (portfolio, LinkedIn, email). Everything between
   `<!-- featured:start -->` and `<!-- featured:end -->` is overwritten on
   every build, so don't hand-edit inside those markers.

6. Turn on the daily refresh. The workflow uses the repo's own
   `GITHUB_TOKEN`, so there is nothing to configure. Once pushed, open
   **Actions -> Update profile art -> Run workflow** to test it. After that
   it runs itself every morning at 04:17 UTC.

## Notes

- The contribution graph is read from the public
  `github.com/users/<login>/contributions` page, so private contributions only
  appear if you enable "Include private contributions on my profile" in your
  GitHub settings.
- The stats card counts only your own non-forked repos.
- Colours live in `PALETTE` in `scripts/make_heatmap_svg.py` if you want a
  different accent than GitHub green.

## The three panes

| Asset | Script | What it is |
| :--- | :--- | :--- |
| `assets/contrib-heatmap.svg` | `scripts/make_heatmap_svg.py` | Day-by-day contribution grid, animated column by column |
| `assets/portrait.svg` | `scripts/make_ascii_svg.py` + `scripts/cards.py` | Your profile picture as ASCII, cropped on the face |
| `assets/stats.svg` | `scripts/cards.py` | Six stat boxes plus a contributions-per-month chart |

All three share one terminal-window frame (`cards.chrome`) so they read as panes of
the same terminal. Rebuild everything with:

```bash
python scripts/build.py --user <your-login>
```

### Swapping in a better photo

The portrait is only as good as the picture. Drop a head-and-shoulders shot in and
rebuild:

```bash
python scripts/make_ascii_svg.py my-photo.jpg assets/portrait.svg --width 60
```

`make_ascii_svg.py` finds the face with OpenCV (cascade model in `scripts/model/`)
and centres the crop on it, so you do not have to pre-crop anything. Commit the new
`assets/portrait.svg` and the daily job will leave it alone.
