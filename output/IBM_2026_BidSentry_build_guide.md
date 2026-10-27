# Pitch deck build

The delivered pitch assets are separate from the local audit app. The editable PowerPoint source is generated with the Codex bundled `@oai/artifact-tool`; the PDF helper assembles the ten 16:9 slide renders into a landscape PDF.

From the repository root, choose a new stem for each build so existing deliverables are preserved:

```powershell
$env:BIDSENTRY_ROOT = (Get-Location).Path
$env:BIDSENTRY_DECK_STEM = "IBM_2026_BidSentry_next"
& "C:\Users\Lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe" output\IBM_2026_BidSentry.mjs
& "C:\Users\Lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" output\IBM_2026_BidSentry_pdf.py --stem IBM_2026_BidSentry_next
```

The deck generator reads the current UI screenshots from `output/`, writes slide renders under `.codex-build/presentation/renders/`, and stores the speaker script in `output/<stem>_content.md`. The PDF helper expects those renders to exist. `BIDSENTRY_DECK_STEM` should be a fresh name; the presentation finalizer intentionally does not overwrite a prior PPTX.
