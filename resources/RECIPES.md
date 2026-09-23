# Recipes (parked on the `recipes` branch, 2026-09-23)

A "Recipes" section for /resources: one goal, the tools in order, what you do at each step,
Jev's alternatives, a "see it in action" proof slot and a copyable first prompt. A task pill
that has a recipe shows "Start with a recipe: ..." above Jev's ranked tools.

Files:
- `resources/_preview_recipes.py`: the recipe data (RECIPES list) + styles + script; injects the
  section into a copy of index.html -> `resources/_preview-recipes.html` (red MOCKUP bar).
- Preview locally: `python -m http.server 8777` in the site folder, open
  http://localhost:8777/resources/_preview-recipes.html

Mockup recipes: long video -> Shorts; AI video from one photo (with a Kling first prompt);
faceless explainer (our real pipeline, tagged "how we make our videos"); meeting notes;
receipts to books; apps automated.

## Before going live
1. Real, credited X / YouTube posts for each "See it in action" slot (link out with the
   creator's handle; never rehost their media). Re-check links on each rebuild.
2. Re-verify every step line against the tool's current features.
3. Move the RECIPES data into resources.json (or recipes.json) and the markup into build.py,
   drop the mockup bar, keep the task -> recipe hint.
4. 2-3 more recipes for the most tapped tasks.
5. A launch video (brainrot or cookie-cutter): "how to turn one video into 10 Shorts" style,
   each recipe is its own short later.
