"""Old-book pipeline: scanned PDF -> page images -> transcription -> translation.

Works with any OpenAI-compatible endpoint (AMD Lemonade, AMD Token Lab, ...).
Switch backends with the `active` line in config.toml.
Rendered PNG pages stay on disk; compressed JPEG copies are sent to the vision API.

Usage:
    python pipeline.py render      --pages 1-10
    python pipeline.py transcribe  --pages 1-10
    python pipeline.py translate   --pages 1-10
    python pipeline.py assemble
    python pipeline.py run         --pages 1-10
    python pipeline.py eval
    python pipeline.py stats
"""

import argparse
import base64
import csv
import json
import os
import re
import random
from openai import APIConnectionError, APITimeoutError
import sys
import time
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


PROMPT_VERSION = "v2-retry-jpeg"

TRANSCRIBE_SYSTEM = (
    "You are a careful transcriber of early printed books. Transcribe the page image "
    "exactly as printed. Keep the original spelling, capitalization, punctuation, "
    "abbreviations and line breaks. Do not expand abbreviations, do not modernize, "
    "do not correct anything, and do not translate. Mark any word you cannot read as [?]. "
    "Leave out running page numbers only if they are clearly separate from the text. "
    "Output only the transcription, with no commentary."
)

TRANSCRIBE_USER = "Transcribe this page."

TRANSLATE_SYSTEM = (
    "You are an expert translator of early printed books. Translate the {src} text you are "
    "given into clear, faithful {dst}. Rules: translate only what is on the page; keep the "
    "paragraph and line structure (verse stays verse); keep proper names; if the page begins "
    "or ends in the middle of a sentence, translate the fragment as it stands; add no notes "
    "or commentary; use the glossary renderings exactly as given. Output only the translation."
)


# ----------------------------------------------------------------
# CONFIG / BACKEND
# ----------------------------------------------------------------

def load_config(path):
    with open(path, "rb") as f:
        cfg = tomllib.load(f)

    name = cfg["active"]

    if name not in cfg["backends"]:
        sys.exit(
            f"config.toml: active backend '{name}' "
            f"not found under [backends]"
        )

    cfg["backend"] = cfg["backends"][name]
    cfg["backend_name"] = name

    return cfg


class Backend:
    """OpenAI-compatible API with rate limiting and retries."""

    def __init__(self, cfg):
        from openai import OpenAI, APIConnectionError, APITimeoutError

        b = cfg["backend"]
        self.pipeline_cfg = cfg.get("pipeline", {})
        self.backend_name = cfg["backend_name"]
        self.base_url = b["base_url"]

        key = (
            b.get("api_key")
            or os.environ.get(b.get("api_key_env", ""), "")
        )

        if not key:
            sys.exit(
                f"No API key for backend '{cfg['backend_name']}'. "
                f"Set the environment variable "
                f"{b.get('api_key_env')}."
            )

        if "PASTE" in b["base_url"]:
            sys.exit(
                "Set base_url for this backend in config.toml first."
            )

        # Disable the SDK's hidden retries. This script handles retries itself,
        # so the number of attempts and wait times are predictable.
        self.client = OpenAI(
            base_url=b["base_url"],
            api_key=key,
            max_retries=0,
            timeout=float(cfg.get("pipeline", {}).get("request_timeout_seconds", 180))
        )

        self.vision_model = b["vision_model"]
        self.text_model = b["text_model"]

        rpm = b.get("requests_per_minute", 0)

        self.min_interval = 60.0 / rpm if rpm else 0.0
        self._last = 0.0

        print(
            f"Backend: {self.backend_name} | {self.base_url} | "
            f"vision: {self.vision_model} | text: {self.text_model}",
            flush=True
        )

    def _wait(self):
        gap = time.monotonic() - self._last

        if gap < self.min_interval:
            time.sleep(self.min_interval - gap)

        self._last = time.monotonic()

    def chat(self, model, messages, max_tokens=2048):
        """Send a request with controlled retries for temporary failures."""

        pipeline_cfg = getattr(self, "pipeline_cfg", {})
        # Defaults are intentionally safe for temporary hosted-model outages.
        max_attempts = int(pipeline_cfg.get("max_attempts", 10))
        base_wait = float(pipeline_cfg.get("retry_base_seconds", 2))
        max_wait = float(pipeline_cfg.get("retry_max_seconds", 60))
        jitter = float(pipeline_cfg.get("retry_jitter", 0.25))

        max_attempts = max(1, max_attempts)
        base_wait = max(0.1, base_wait)
        max_wait = max(base_wait, max_wait)
        jitter = min(max(jitter, 0.0), 1.0)

        for attempt in range(max_attempts):
            self._wait()

            try:
                r = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.0,
                    max_tokens=max_tokens
                )

                response_text = (r.choices[0].message.content or "").strip()
                u = getattr(r, "usage", None)
                usage = {
                    "prompt_tokens": getattr(u, "prompt_tokens", None),
                    "completion_tokens": getattr(u, "completion_tokens", None),
                }
                if not response_text:
                    raise RuntimeError(
                        f"{self.backend_name} returned an empty response for model "
                        f"{model}. No output was saved. Check model compatibility "
                        "and the server logs."
                    )
                return response_text, usage

            except Exception as e:
                status = getattr(e, "status_code", None)
                response = getattr(e, "response", None)
                if status is None and response is not None:
                    status = getattr(response, "status_code", None)

                # 413 is a request-size problem, not a temporary outage.
                if status == 413:
                    raise RuntimeError(
                        "API returned HTTP 413 (Payload Too Large). The image is "
                        "still too large for this endpoint. Lower book.max_image_dimension, "
                        "book.jpeg_quality, or book.max_image_mb in config.toml."
                    ) from e

                # Do not retry authentication, malformed requests, or other permanent 4xx.
                if status is not None and 400 <= status < 500 and status not in (408, 409, 425, 429):
                    raise RuntimeError(
                        f"API returned HTTP {status}; this is not treated as a temporary "
                        f"error, so the request was not retried: {e}"
                    ) from e

                # Retry connection failures, timeouts, rate limits, and server errors.
                retryable = (
                    isinstance(e, (APIConnectionError, APITimeoutError))
                    or status in (408, 409, 425, 429)
                    or (status is not None and status >= 500)
                )
                if not retryable:
                    raise

                if attempt + 1 >= max_attempts:
                    print(
                        f"  request failed after {max_attempts} attempts ({e})",
                        file=sys.stderr
                    )
                    raise RuntimeError(
                        f"{self.backend_name} ({self.base_url}) failed after "
                        f"{max_attempts} attempts. "
                        "For HTTP 503, the selected model service is unavailable; "
                        "for connection errors, check the server URL and whether "
                        "the server is running. Completed pages are skipped on rerun."
                    ) from e

                # Exponential backoff, capped, with small random jitter to avoid
                # repeatedly hitting an overloaded service at the same moment.
                wait = min(max_wait, base_wait * (2 ** attempt))

                # Respect a numeric Retry-After header when the server supplies one.
                headers = getattr(response, "headers", None) if response is not None else None
                retry_after = None
                if headers:
                    try:
                        retry_after = float(headers.get("retry-after", ""))
                    except (TypeError, ValueError):
                        retry_after = None
                if retry_after is not None and retry_after > 0:
                    wait = min(max_wait, max(wait, retry_after))

                if jitter:
                    wait *= random.uniform(1.0 - jitter, 1.0 + jitter)

                wait = min(max_wait, max(0.1, wait))
                print(
                    f"  request failed (HTTP {status if status is not None else 'network'}: {e}); "
                    f"attempt {attempt + 1}/{max_attempts}; retrying in {wait:.1f}s",
                    file=sys.stderr,
                    flush=True
                )
                time.sleep(wait)


# ----------------------------------------------------------------
# PATHS AND HELPERS
# ----------------------------------------------------------------

def dirs(cfg):

    out = Path(cfg["book"]["out_dir"])

    d = {
        k: out / k
        for k in (
            "pages",
            "transcripts",
            "translations",
            "meta",
            "gold"
        )
    }

    for p in d.values():
        p.mkdir(parents=True, exist_ok=True)

    d["out"] = out

    return d


def parse_range(spec):

    if not spec:
        return 1, 10 ** 9

    if "-" in spec:
        a, b = spec.split("-", 1)
        return int(a), int(b)

    return int(spec), int(spec)


def in_range(stem, rng):

    return rng[0] <= int(stem) <= rng[1]


def save_meta(
    d,
    stem,
    stage,
    model,
    seconds,
    usage,
    cfg
):

    path = d["meta"] / f"{stem}.json"

    meta = (
        json.loads(path.read_text())
        if path.exists()
        else {}
    )

    meta[stage] = {
        "model": model,
        "backend": cfg["backend_name"],
        "prompt_version": PROMPT_VERSION,
        "seconds": round(seconds, 2),
        **usage,
    }

    path.write_text(
        json.dumps(meta, indent=2)
    )


# ----------------------------------------------------------------
# RENDER PDF PAGES
# ----------------------------------------------------------------

def cmd_render(cfg, args):

    import pymupdf

    d = dirs(cfg)

    doc = pymupdf.open(cfg["book"]["pdf"])

    try:
        first, last = parse_range(args.pages)

        first = max(1, first)
        last = min(last, len(doc))

        zoom = cfg["book"].get("dpi", 200) / 72

        for i in range(first, last + 1):

            dest = d["pages"] / f"{i:04d}.png"

            if dest.exists() and not args.force:
                continue

            doc[i - 1].get_pixmap(
                matrix=pymupdf.Matrix(zoom, zoom)
            ).save(str(dest))

            print(f"rendered page {i}")

    finally:
        doc.close()


# ----------------------------------------------------------------
# COMPRESS IMAGES FOR API
# ----------------------------------------------------------------

def make_api_image(img_path, cfg):
    """
    Make a compressed JPEG copy of a rendered page.

    Original PNG remains untouched on disk.

    PyMuPDF performs conversion and resizing.
    No Pillow dependency required.
    """

    import pymupdf

    book_cfg = cfg["book"]

    max_dimension = int(
        book_cfg.get("max_image_dimension", 2200)
    )

    quality = int(
        book_cfg.get("jpeg_quality", 80)
    )

    max_image_mb = float(
        book_cfg.get("max_image_mb", 4.0)
    )

    if max_dimension < 512:
        raise ValueError(
            "book.max_image_dimension must be at least 512"
        )

    if not 40 <= quality <= 95:
        raise ValueError(
            "book.jpeg_quality must be between 40 and 95"
        )

    if max_image_mb <= 0:
        raise ValueError(
            "book.max_image_mb must be greater than 0"
        )

    with pymupdf.open(str(img_path)) as doc:

        page = doc[0]

        rect = page.rect

        largest_side = max(
            rect.width,
            rect.height
        )

        scale = (
            min(1.0, max_dimension / largest_side)
            if largest_side
            else 1.0
        )

        pix = page.get_pixmap(
            matrix=pymupdf.Matrix(scale, scale),
            colorspace=pymupdf.csRGB,
            alpha=False
        )

        jpeg_bytes = pix.tobytes(
            "jpeg",
            jpg_quality=quality
        )

    max_bytes = int(
        max_image_mb * 1024 * 1024
    )

    if len(jpeg_bytes) > max_bytes:

        raise RuntimeError(
            f"Compressed image is "
            f"{len(jpeg_bytes) / 1024 / 1024:.2f} MB, "
            f"above book.max_image_mb={max_image_mb}. "
            "Lower book.max_image_dimension or "
            "book.jpeg_quality in config.toml."
        )

    return jpeg_bytes


# ----------------------------------------------------------------
# TRANSCRIBE
# ----------------------------------------------------------------

def cmd_transcribe(cfg, be, args):

    d = dirs(cfg)

    rng = parse_range(args.pages)

    for img in sorted(d["pages"].glob("*.png")):

        if not in_range(img.stem, rng):
            continue

        dest = (
            d["transcripts"] / f"{img.stem}.txt"
        )

        if dest.exists() and not args.force:
            continue

        # Compress PNG into JPEG for API upload.
        image_bytes = make_api_image(img, cfg)

        b64 = base64.b64encode(
            image_bytes
        ).decode("ascii")

        print(
            f"  page {int(img.stem)}: sending "
            f"{len(image_bytes) / 1024:.0f} KB JPEG",
            file=sys.stderr
        )

        messages = [

            {
                "role": "system",
                "content": TRANSCRIBE_SYSTEM
            },

            {
                "role": "user",
                "content": [

                    {
                        "type": "text",
                        "text": TRANSCRIBE_USER
                    },

                    {
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                "data:image/jpeg;base64,"
                                f"{b64}"
                            )
                        }
                    },

                ]
            },

        ]

        t0 = time.time()

        text, usage = be.chat(
            be.vision_model,
            messages
        )

        dest.write_text(
            text,
            encoding="utf-8"
        )

        save_meta(
            d,
            img.stem,
            "transcribe",
            be.vision_model,
            time.time() - t0,
            usage,
            cfg
        )

        print(
            f"transcribed page {int(img.stem)}"
        )


# ----------------------------------------------------------------
# TRANSLATE
# ----------------------------------------------------------------

def cmd_translate(cfg, be, args):

    d = dirs(cfg)

    rng = parse_range(args.pages)

    src = cfg["book"]["source_language"]
    dst = cfg["book"]["target_language"]

    gpath = Path("glossary.txt")

    glossary = (
        gpath.read_text(encoding="utf-8").strip()
        if gpath.exists()
        else ""
    )

    system = TRANSLATE_SYSTEM.format(
        src=src,
        dst=dst
    )

    prev_tail = ""

    for tr in sorted(
        d["transcripts"].glob("*.txt")
    ):

        if not in_range(tr.stem, rng):
            continue

        dest = (
            d["translations"] / f"{tr.stem}.txt"
        )

        if dest.exists() and not args.force:

            prev_tail = dest.read_text(
                encoding="utf-8"
            )[-600:]

            continue

        text = tr.read_text(
            encoding="utf-8"
        )

        if not text.strip():

            dest.write_text(
                "",
                encoding="utf-8"
            )

            continue

        parts = []

        if glossary:

            parts.append(
                f"Glossary (use these renderings):\n"
                f"{glossary}"
            )

        if prev_tail:

            parts.append(
                "End of the previous page's translation "
                "(for continuity only, do not translate it again):\n"
                f"{prev_tail}"
            )

        parts.append(
            f"{src} text to translate:\n{text}"
        )

        messages = [

            {
                "role": "system",
                "content": system
            },

            {
                "role": "user",
                "content": "\n\n".join(parts)
            }

        ]

        t0 = time.time()

        out, usage = be.chat(
            be.text_model,
            messages
        )

        dest.write_text(
            out,
            encoding="utf-8"
        )

        save_meta(
            d,
            tr.stem,
            "translate",
            be.text_model,
            time.time() - t0,
            usage,
            cfg
        )

        prev_tail = out[-600:]

        print(
            f"translated page {int(tr.stem)}"
        )


# ----------------------------------------------------------------
# ASSEMBLE RESULTS
# ----------------------------------------------------------------

def cmd_assemble(cfg, args):

    d = dirs(cfg)

    lines = [

        f"# {Path(cfg['book']['pdf']).stem}: "
        f"{cfg['book']['source_language']} to "
        f"{cfg['book']['target_language']}\n"

    ]

    for tr in sorted(
        d["transcripts"].glob("*.txt")
    ):

        t = (
            d["translations"] / f"{tr.stem}.txt"
        )

        if not t.exists():
            continue

        lines += [

            f"## Page {int(tr.stem)}\n",

            "### Original\n",

            tr.read_text(
                encoding="utf-8"
            ),

            "\n### Translation\n",

            t.read_text(
                encoding="utf-8"
            ),

            "\n---\n"

        ]

    dest = d["out"] / "side_by_side.md"

    dest.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    print(f"wrote {dest}")


# ----------------------------------------------------------------
# EVALUATION
# ----------------------------------------------------------------

def edit_distance(a, b):

    prev = list(range(len(b) + 1))

    for i, x in enumerate(a, 1):

        cur = [i]

        for j, y in enumerate(b, 1):

            cur.append(
                min(
                    prev[j] + 1,
                    cur[j - 1] + 1,
                    prev[j - 1] + (x != y)
                )
            )

        prev = cur

    return prev[-1]


def norm(s):

    return re.sub(r"\s+", " ", s).strip()


def cmd_eval(cfg, args):

    """Compare transcripts with hand-corrected pages."""

    d = dirs(cfg)

    rows = []
    tc = te = tw = twe = 0

    for gold in sorted(
        d["gold"].glob("*.txt")
    ):

        hyp_path = (
            d["transcripts"] / gold.name
        )

        if not hyp_path.exists():
            continue

        g = norm(
            gold.read_text(encoding="utf-8")
        )

        h = norm(
            hyp_path.read_text(encoding="utf-8")
        )

        ce = edit_distance(g, h)

        we = edit_distance(
            g.split(),
            h.split()
        )

        rows.append([

            gold.stem,
            len(g),
            ce,
            round(ce / max(len(g), 1), 4),
            len(g.split()),
            we,
            round(
                we / max(len(g.split()), 1),
                4
            )

        ])

        tc += len(g)
        te += ce
        tw += len(g.split())
        twe += we

    if not rows:

        sys.exit(
            "No matching pages. Put hand-corrected text "
            "in out/gold/0001.txt etc."
        )

    print(
        f"{'page':>6} {'chars':>7} "
        f"{'CER':>8} {'words':>7} {'WER':>8}"
    )

    for r in rows:

        print(
            f"{r[0]:>6} {r[1]:>7} "
            f"{r[3]:>8.2%} {r[4]:>7} "
            f"{r[6]:>8.2%}"
        )

    print(
        f"{'ALL':>6} {tc:>7} "
        f"{te / max(tc, 1):>8.2%} "
        f"{tw:>7} "
        f"{twe / max(tw, 1):>8.2%}"
    )

    dest = d["out"] / "eval.csv"

    with open(
        dest,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        w = csv.writer(f)

        w.writerow([
            "page",
            "gold_chars",
            "char_errors",
            "CER",
            "gold_words",
            "word_errors",
            "WER"
        ])

        w.writerows(rows)

    print(f"wrote {dest}")


# ----------------------------------------------------------------
# STATISTICS
# ----------------------------------------------------------------

def cmd_stats(cfg, args):

    d = dirs(cfg)

    totals = {}

    for p in d["meta"].glob("*.json"):

        for stage, m in json.loads(
            p.read_text()
        ).items():

            t = totals.setdefault(
                (
                    stage,
                    m["backend"],
                    m["model"]
                ),
                [0, 0.0, 0, 0]
            )

            t[0] += 1
            t[1] += m["seconds"]

            t[2] += (
                m.get("prompt_tokens") or 0
            )

            t[3] += (
                m.get("completion_tokens") or 0
            )

    if not totals:

        sys.exit(
            "No meta files yet. "
            "Run transcribe/translate first."
        )

    for (
        stage,
        backend,
        model
    ), (
        n,
        sec,
        pt,
        ct
    ) in sorted(totals.items()):

        rate = (
            f"{3600 * n / sec:.0f}"
            if sec > 0
            else "n/a"
        )

        print(
            f"{stage:<11} "
            f"{backend}/{model}: "
            f"{n} pages, "
            f"{sec / n:.1f}s/page, "
            f"{rate} pages/hour, "
            f"{pt} prompt + "
            f"{ct} completion tokens"
        )


# ----------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------

def main():

    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter
    )

    ap.add_argument(
        "command",
        choices=[
            "render",
            "transcribe",
            "translate",
            "assemble",
            "run",
            "eval",
            "stats"
        ]
    )

    ap.add_argument(
        "--config",
        default="config.toml"
    )

    ap.add_argument(
        "--pages",
        help="e.g. 5 or 10-20 (default: all)"
    )

    ap.add_argument(
        "--force",
        action="store_true",
        help="redo pages that already have output"
    )

    args = ap.parse_args()

    cfg = load_config(args.config)

    if args.command in ("render", "run"):

        cmd_render(cfg, args)

    if args.command in (
        "transcribe",
        "translate",
        "run"
    ):

        be = Backend(cfg)

        if args.command in (
            "transcribe",
            "run"
        ):

            cmd_transcribe(
                cfg,
                be,
                args
            )

        if args.command in (
            "translate",
            "run"
        ):

            cmd_translate(
                cfg,
                be,
                args
            )

    if args.command in (
        "assemble",
        "run"
    ):

        cmd_assemble(cfg, args)

    if args.command == "eval":

        cmd_eval(cfg, args)

    if args.command == "stats":

        cmd_stats(cfg, args)


if __name__ == "__main__":
    main()
