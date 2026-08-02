#!/usr/bin/env python3
"""Decide whether a paper's text layer can be trusted, and route to the page image when it can't.

    tools/extraction_integrity.py sweep              # classify the whole shelf
    tools/extraction_integrity.py check <stem>       # one paper: verdict + what to do
    tools/extraction_integrity.py page <stem> 20 44  # render those pages, 3-channel diff

This is the INSTRUMENT behind the maths half of `research_depth_gate`. The gate reads
the index this writes; with no index that half is silently inert.

    --shelf DIR    holds `pdfs/` and `text/`.  default: $NULLIUS_SHELF, else ./papers, else .
    --out FILE     the index the gate consults. default: <repo>/.nullius/extraction_integrity.json
    --report FILE  human-readable sweep. default: <shelf>/EXTRACTION-INTEGRITY.md

Requires `pdfinfo`, `pdffonts`, `pdftotext` (poppler) on PATH; `page` also wants
`pdftoppm` and optionally `tesseract`. No Python dependencies.

Why this exists, and why it does not try to "fix" extraction
------------------------------------------------------------
Rychlik (1994): the extraction rendered equation (3) as `R(t) = T(nF(t))`; the printed
page reads `R(t) = T((n/m)F(t))`. The denominator was gone with no mangling to warn
anyone — clean, plausible, wrong by 901x at the operating point it was read for.

The obvious control does not work. `pdftotext -layout`, `-raw`, and per-page all read the
SAME embedded text layer, so they agree with each other AND with the error.

The less obvious control is only half a control. Measured on Esseen (1945) p.20, whose
page image plainly shows `G(z) = (1/2pi) * int e^{-izt} f(t) dt` and `f(t) = 0 for t <= 0`:

    embedded layer   G(z) = -~z ... e-'~t e~ltl f(t) dt      1/2pi GONE;  `t ~ o`
    tesseract@300dpi Gl) = femennsyat                        equation destroyed; `t < 0`
    page image       correct                                 correct, and `<=` not `<`

Tesseract is genuinely independent of the text layer, and it caught the prose-level
inequality that the layer mangled — but it did not recover the displayed equation, and it
still got strictness wrong (`<` for `<=`).

**And this is NOT only a scan problem — that was the wrong diagnosis.** Patton (2013),
born-digital LaTeX, page 20. The page reads `U_it = F_i(eps_it)`, `C(gamma*)`,
`delta_t(gamma*)`. The embedded layer emits:

    Fi ("it )        eps -> "
    C ( )            gamma* DELETED, leaving syntactically valid empty parens
    C ( ( ))         delta_t(gamma*) -> nothing at all
    where t is the parameter of the copula        delta_t -> `t`
    i = 1; 2; :::; n                              commas -> semicolons

`delta_t` becoming `t` is the worst case in the whole family: not garbage, but a *different
variable that also exists in the paper*. pdftotext reads CMMI/CMSY glyphs through the font's
builtin TeX encoding and drops or transliterates what it cannot map. Every LaTeX paper on a
shelf is exposed; the scans were the visible half.

So the conclusion this tool encodes: **there is no text pipeline that recovers displayed
mathematics. The page image is the only authority.** The job here is triage and routing —
tell you which papers are in that class, and put the image in front of a reader for the
passages that matter. Agreement between text channels is NOT evidence; it is the failure mode.

Limits, stated so they are not rediscovered:
  - A zero Greek count is *necessary, not sufficient*. Rychlik's lost denominator carried no
    Greek at all. A clean sweep here does not license trusting an equation.
  - **Tesseract here is `eng`-only and physically cannot emit a Greek glyph**, so "tesseract
    also found no Greek" is an invariance that cannot fail. It was briefly used as a control
    and was worthless; seven papers were scored false-positive before the page image showed
    the Greek was there. Use it for prose/relations, never for symbol recovery.
  - For a scan, tesseract and the embedded layer are both OCR. Their disagreement is
    informative; their agreement is not.
  - This tool never rewrites a .txt. A silently-repaired extraction is worse than a flagged one.
"""
from __future__ import annotations

import collections
import glob
import json
import os
import re
import subprocess
import sys

try:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gates"))
    from _config import governing_root
except Exception:                                # standalone use is fine
    def governing_root(_path):
        return None

GREEK = re.compile(r"[Ͱ-Ͽἀ-῿]")
# A single capital, a space, then a capitalised run: `L EADBETTER`, `T HEOREM`.
# This is how pdftotext renders LaTeX small caps, and NOTHING here is lost -- every
# character survives in the right order with one space inserted -- so the file scores
# CLEAN while a hand-written grep for `Leadbetter` returns a false zero. Scored on its
# own axis rather than folded into `cls`, because `cls` is about MATHS safety and this
# is about NAME retrievability; a document can be perfect on one and hostile on the other.
CAPSPLIT = re.compile(r"\b[A-Z] [A-Z]{3,}[A-Za-z]*")
LIGATURE = re.compile(r"[ﬀ-ﬆ]")
RELATION = re.compile(r"[≤≥≠≈∼<>]")
SCAN_MARK = (".tif", ".tiff", "pdfgenerator", "abbyy", "scansoft", "acrobat capture",
             "capture plug-in", "tesseract", "scanner", "kofax", "finereader",
             "luradocument", "digipath", "page2pdf")

# Fonts that carry mathematics. Their presence means the paper HAS symbols, so a zero Greek
# count in the extraction is loss rather than absence. This is the discriminating control and
# it can come out wrong: a paper with these fonts whose .txt does contain Greek does not fire.
MATH_FONT = re.compile(r"CMMI|CMSY|CMEX|MSAM|MSBM|rsfs|eufm|stmary|MathematicalPi|"
                       r"Symbol|LMMath|txsy|txmi|NimbusRomNo9L-.*Ital|XYATIP|wasy", re.I)

# Papers whose maths is genuinely Greek-free; a zero count here is not evidence of loss.
GREEK_EXEMPT_HINT = ("syllabus", "toc", "frontmatter", "readme")

ORDER = ["NOT-A-PDF", "IMAGE-ONLY", "SCAN-OCR", "GLYPH-LOSS", "GLYPH-THIN", "GLYPH-RISK", "CLEAN"]
UNSAFE_CLASSES = ("NOT-A-PDF", "IMAGE-ONLY", "SCAN-OCR", "GLYPH-LOSS", "GLYPH-THIN")

PDFS = TEXT = IMGS = REPORT = STATE = ""        # set by configure()


def configure(argv: list) -> list:
    """Resolve the shelf layout. Returns argv with the recognised flags removed."""
    global PDFS, TEXT, IMGS, REPORT, STATE

    def take(flag, default=None):
        if flag in argv:
            i = argv.index(flag)
            val = argv[i + 1] if i + 1 < len(argv) else default
            del argv[i:i + 2]
            return val
        return default

    shelf = take("--shelf") or os.environ.get("NULLIUS_SHELF")
    if not shelf:
        shelf = "papers" if os.path.isdir("papers") else "."
    shelf = os.path.abspath(shelf)

    # A shelf may keep PDFs in `pdfs/` beside `text/`, or simply hold them directly.
    PDFS = os.path.join(shelf, "pdfs") if os.path.isdir(os.path.join(shelf, "pdfs")) else shelf
    TEXT = os.path.join(shelf, "text")
    IMGS = os.path.join(shelf, "pageimages")
    REPORT = take("--report") or os.path.join(shelf, "EXTRACTION-INTEGRITY.md")

    out = take("--out")
    if not out:
        root = governing_root(os.path.join(shelf, "x"))
        if root:
            os.makedirs(os.path.join(root, ".nullius"), exist_ok=True)
            out = os.path.join(root, ".nullius", "extraction_integrity.json")
        else:
            out = os.path.join(shelf, "extraction_integrity.json")
    STATE = out
    return argv


def sh(cmd, timeout=90):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return ""


def paired_text(pdf_base: str):
    """The .txt extraction for a pdf, matched loosely — stems drift (`foo.pdf` -> `foo.OCR.txt`)."""
    stem = pdf_base[:-4]
    exact = os.path.join(TEXT, stem + ".txt")
    if os.path.exists(exact):
        return exact
    # `arxiv-2605.07358.pdf` pairs with `2605.07358.txt`; strip the prefix before matching.
    bare = re.sub(r"^arxiv-", "", stem)
    for cand in (stem, bare):
        for t in glob.glob(os.path.join(TEXT, "*.txt")):
            tb = os.path.basename(t)[:-4]
            if tb.startswith(cand) or cand.startswith(tb):
                return t
    return None


def classify(pdf_path: str) -> dict:
    base = os.path.basename(pdf_path)
    with open(pdf_path, "rb") as fh:
        magic = fh.read(5)
    if magic != b"%PDF-":
        return dict(pdf=base, cls="NOT-A-PDF", maths_unsafe=True, pages=0,
                    note="file is not a PDF (block page / stub); the artifact is not the paper")

    info = sh(["pdfinfo", pdf_path])
    fonts = sh(["pdffonts", pdf_path])
    layer = sh(["pdftotext", pdf_path, "-"], timeout=180)

    pages = int((re.search(r"^Pages:\s+(\d+)", info, re.M) or [0, "0"])[1])
    creator = (re.search(r"^Creator:\s*(.*)$", info, re.M) or [None, ""])[1].strip()
    producer = (re.search(r"^Producer:\s*(.*)$", info, re.M) or [None, ""])[1].strip()
    blob = (creator + " " + producer).lower().replace("\x00", "")
    rows = [l for l in fonts.splitlines()[2:] if l.strip()]
    n_type3 = sum(1 for l in rows if re.search(r"\bType 3\b", l))
    n_math = sum(1 for l in rows if MATH_FONT.search(l))
    cpp = len(layer) / max(pages, 1)

    tpath = paired_text(base)
    txt = open(tpath, errors="ignore").read() if tpath else layer
    greek = len(GREEK.findall(txt))
    lig = len(LIGATURE.findall(txt))
    repl = txt.count("�")
    exempt = any(h in base.lower() for h in GREEK_EXEMPT_HINT)
    # How mathematical is the paper, independent of whether symbols survived. A survey with
    # zero Greek is unremarkable; a paper at eq_density 6 with zero Greek has lost something.
    eqd = round(1000 * txt.count("=") / max(len(txt), 1), 2)

    # Name-scan hazard. Two populations land in this screen and only one is the defect:
    # systematic \textsc (one arXiv paper: 385 splits, `P ROOF` x28, `L EMMA` x17, plus
    # author names) genuinely breaks name/keyword greps, while OCR noise (Kish 1965: 22
    # splits, all table headers like `A TAXONOMY`) contains no surnames and threatens
    # nothing. No reliable automatic discriminator was found, so the top tokens are carried
    # into the report and a reader tells them apart at a glance -- consistent with this
    # tool's rule that it triages and routes rather than repairing.
    csplits = CAPSPLIT.findall(txt)
    cs_top = [w for w, _ in collections.Counter(csplits).most_common(6)]

    if cpp < 200:
        cls, note = "IMAGE-ONLY", "no usable text layer; every character must come from the image"
    elif any(k in blob for k in SCAN_MARK):
        cls, note = "SCAN-OCR", f"text layer is OCR (creator={creator[:30]!r}); maths not trustworthy"
    elif n_math and greek == 0 and len(txt) > 8000 and not exempt:
        cls, note = "GLYPH-LOSS", (f"{n_math} maths fonts embedded but ZERO Greek extracted — "
                                   "symbols were deleted or transliterated (Patton-2013 mode)")
    elif n_math and greek < len(txt) / 20000:
        cls, note = "GLYPH-THIN", (f"{n_math} maths fonts but only {greek} Greek glyphs in "
                                   f"{len(txt)} chars; partial symbol loss likely")
    elif repl or n_type3 > 20:
        cls, note = "GLYPH-RISK", f"{repl} U+FFFD, {n_type3} Type-3 bitmap fonts; spot-check symbols"
    else:
        cls, note = "CLEAN", "born-digital text layer, symbols surviving"

    return dict(pdf=base, cls=cls, maths_unsafe=cls in UNSAFE_CLASSES,
                pages=pages, chars_per_page=round(cpp), greek=greek, ligatures=lig,
                replacement=repl, type3=n_type3, math_fonts=n_math, eq_density=eqd,
                caps_splits=len(csplits), caps_distinct=len(set(csplits)), caps_top=cs_top,
                creator=creator[:44],
                text=os.path.basename(tpath) if tpath else None, note=note)


def sweep() -> list:
    rows = [classify(p) for p in sorted(glob.glob(os.path.join(PDFS, "*.pdf")))]
    with open(STATE, "w") as fh:
        json.dump(rows, fh, indent=1)

    counts = {k: sum(1 for r in rows if r["cls"] == k) for k in ORDER}
    unsafe = [r for r in rows if r["maths_unsafe"]]
    ligs = [r for r in rows if r.get("ligatures")]

    L = ["# Extraction integrity — shelf sweep", "",
         "Generated by `tools/extraction_integrity.py sweep`. Regenerate; do not hand-edit.", "",
         "**A `CLEAN` verdict licenses quoting prose. It never licenses trusting an equation** —",
         "Rychlik's lost denominator carried no Greek and would pass every check here.", "",
         f"`{len(rows)}` PDFs on the shelf. **`{len(unsafe)}` are maths-unsafe.**", ""]
    L += ["| class | n | meaning |", "|---|---:|---|"]
    meaning = {
        "NOT-A-PDF": "the file is a block page or stub — **the artifact is not the paper**",
        "IMAGE-ONLY": "no text layer; nothing may be quoted from text",
        "SCAN-OCR": "text layer is OCR; prose quotable with care, maths never",
        "GLYPH-LOSS": "maths fonts embedded, zero Greek extracted — **symbols deleted silently**",
        "GLYPH-THIN": "maths fonts but Greek far below expected density; partial loss",
        "GLYPH-RISK": "replacement chars or many Type-3 fonts; spot-check",
        "CLEAN": "born-digital layer; prose trustworthy, equations still need the image",
    }
    for k in ORDER:
        L.append(f"| `{k}` | {counts[k]} | {meaning[k]} |")

    L += ["", "## Maths-unsafe papers", "",
          "Any equation, inequality, constant or bound taken from these must be read off the",
          "rendered page: `tools/extraction_integrity.py page <stem> <page>`.", "",
          "`eq_density` is `=` per 1000 chars — how mathematical the paper is, measured",
          "independently of whether its symbols survived. **Sorted by it**: a survey with no Greek",
          "is unremarkable, a paper at density 6 with zero Greek has certainly lost something.",
          "A flag here is a *candidate*; confirmation is one page image, never another text pass.", "",
          "| paper | class | pages | eq_density | greek | why |", "|---|---|---:|---:|---:|---|"]
    for r in sorted(unsafe, key=lambda r: (ORDER.index(r["cls"]), -r.get("eq_density", 0))):
        L.append(f"| `{r['pdf']}` | {r['cls']} | {r.get('pages','-')} | "
                 f"{r.get('eq_density','-')} | {r.get('greek','-')} | {r['note']} |")

    if ligs:
        L += ["", "## Ligature-bearing extractions", "",
              "A term-scan over these lies unless the needle and haystack are both",
              "`unicodedata.normalize(\"NFKC\", ...)`-ed first: `differentiab` returned 0 while",
              "`di<ff-ligature>erentiab` returned 2, on the very assumption under test.", ""]
        L += ["| paper | ligatures |", "|---|---:|"]
        for r in sorted(ligs, key=lambda r: -r["ligatures"])[:25]:
            L.append(f"| `{r['pdf']}` | {r['ligatures']} |")

    caps = [r for r in rows if r.get("caps_splits", 0) >= 15]
    if caps:
        L += ["", "## Name-scan hazards — small-caps splitting", "",
              "`pdftotext` renders LaTeX small caps with an intruding space: `\\textsc{Leadbetter}`",
              "becomes `L EADBETTER`. **Nothing is lost**, so these files score `CLEAN` — and a",
              "hand-written `grep Leadbetter` returns a false zero anyway. Measured on Pappadà",
              "2014, where `Embrechts` is cited three times and no raw grep could match.", "",
              "**Search these with a matcher that squashes whitespace and punctuation**, so the",
              "intruding space never reaches the comparison. A raw `grep` is the wrong instrument",
              "for any name or title scan over this list.", "",
              "Read the sample column before worrying: `P ROOF`/`L EMMA`/author names mean genuine",
              "`\\textsc` and a real hazard; `A TAXONOMY`-style article-plus-word means OCR noise and",
              "no surnames are at risk.", "",
              "| paper | splits | distinct | sample |", "|---|---:|---:|---|"]
        for r in sorted(caps, key=lambda r: -r["caps_splits"])[:25]:
            L.append(f"| `{r['pdf']}` | {r['caps_splits']} | {r['caps_distinct']} | "
                     f"{', '.join('`' + w + '`' for w in r.get('caps_top', [])[:4])} |")

    with open(REPORT, "w") as fh:
        fh.write("\n".join(L) + "\n")

    print(f"{len(rows)} PDFs swept  ->  {REPORT}")
    print(f"index for the gate    ->  {STATE}")
    for k in ORDER:
        print(f"  {counts[k]:4d}  {k}")
    print(f"\n  {len(unsafe)} maths-unsafe, {len(ligs)} ligature-bearing, "
          f"{len(caps)} name-scan hazards")
    return rows


def check(stem: str):
    hits = [p for p in glob.glob(os.path.join(PDFS, "*.pdf")) if stem in os.path.basename(p)]
    if not hits:
        sys.exit(f"no shelf PDF matching {stem!r} under {PDFS}")
    for p in hits:
        r = classify(p)
        print(f"\n{r['pdf']}\n  verdict : {r['cls']}"
              f"{'   ** MATHS-UNSAFE **' if r['maths_unsafe'] else ''}\n  why     : {r['note']}")
        if r["cls"] != "NOT-A-PDF":
            print(f"  pages={r['pages']} chars/pg={r['chars_per_page']} greek={r['greek']} "
                  f"ligatures={r['ligatures']} U+FFFD={r['replacement']} type3={r['type3']}")
        if r["maths_unsafe"]:
            print("  action  : read equations off the image — "
                  f"tools/extraction_integrity.py page {stem} <page>")


def page(stem: str, pages: list):
    hits = [p for p in glob.glob(os.path.join(PDFS, "*.pdf")) if stem in os.path.basename(p)]
    if not hits:
        sys.exit(f"no shelf PDF matching {stem!r} under {PDFS}")
    pdf = hits[0]
    out = os.path.join(IMGS, os.path.basename(pdf)[:-4])
    os.makedirs(out, exist_ok=True)

    for pg in pages:
        prefix = os.path.join(out, f"p{int(pg):04d}")
        subprocess.run(["pdftoppm", "-r", "300", "-f", str(pg), "-l", str(pg), "-png", pdf, prefix],
                       capture_output=True, timeout=180)
        img = sorted(glob.glob(prefix + "*.png"))
        layer = sh(["pdftotext", "-f", str(pg), "-l", str(pg), pdf, "-"])
        ocr = ""
        if img:
            subprocess.run(["tesseract", img[0], prefix, "--psm", "6"],
                           capture_output=True, timeout=300)
            if os.path.exists(prefix + ".txt"):
                ocr = open(prefix + ".txt", errors="ignore").read()

        def stat(s):
            return (f"chars={len(s):5d} greek={len(GREEK.findall(s)):3d} "
                    f"relations={len(RELATION.findall(s)):3d}")

        print(f"\n=== page {pg} of {os.path.basename(pdf)} ===")
        print(f"  embedded layer : {stat(layer)}")
        print(f"  tesseract      : {stat(ocr)}")
        if img:
            print(f"  PAGE IMAGE     : {img[0]}")
            print("  ^ this is the authority. Read it. The two text rows above are")
            print("    divergence detectors only — where they disagree, neither is trusted,")
            print("    and where they AGREE they may still share the same deletion.")
        print(f"\n  --- embedded layer ---\n{layer[:1200]}")
        print(f"\n  --- tesseract ---\n{ocr[:1200]}")


if __name__ == "__main__":
    argv = configure(sys.argv[1:])
    if not argv or argv[0] not in ("sweep", "check", "page"):
        sys.exit(__doc__)
    mode = argv[0]
    if mode == "sweep":
        sweep()
    elif mode == "check":
        check(argv[1])
    else:
        page(argv[1], argv[2:] or ["1"])
