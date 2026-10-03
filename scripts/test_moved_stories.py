#!/usr/bin/env python3
"""Moved stories (stories.json movedTo) 301 to the apex before any 200 rewrite."""
import json, pathlib, subprocess, sys
REPO = pathlib.Path(__file__).resolve().parent.parent
stories = json.loads((REPO / "src/data/stories.json").read_text())
moved = {s["slug"]: s["movedTo"] for s in stories if s.get("movedTo")}
assert len(moved) == 12, f"expected 12 moved stories, got {len(moved)}"
out = subprocess.run([sys.executable, str(REPO / "scripts/build-redirects.py"), "--stdout"], capture_output=True, text=True, check=True).stdout
lines = [l for l in out.splitlines() if l and not l.startswith("#")]
first200 = next(i for i, l in enumerate(lines) if l.endswith(" 200"))
for slug, target in moved.items():
    for src in (f"/stories/{slug}/", f"/stories/{slug}"):
        rule = f"{src} {target} 301"
        assert rule in lines, f"missing: {rule}"
        assert lines.index(rule) < first200, f"after the 200 block: {rule}"
    assert f"/stories/{slug}/ /stories/{slug}/ 200" not in lines, f"still rewritten: {slug}"
print(f"ok: {len(moved)} moved stories redirect to the apex")

# The deploy uploads dist/ only (deploy-cf-pages.yml: `pages deploy dist/`), so the
# generated _redirects must be copied into dist by the build.
dist = REPO / "dist"
if dist.exists():
    shipped = dist / "_redirects"
    assert shipped.exists(), "dist/_redirects missing — the build doesn't ship the redirect rules"
    assert shipped.read_text() == (REPO / "_redirects").read_text(), "dist/_redirects differs from the generated _redirects"
    print("ok: dist/_redirects matches the generated file")
