"""Independent image-first Latin proofreading, followed by image-based reconciliation.

Keeps pipeline.py, auto_loader.py, and original outputs unchanged.
Uses the existing OpenAI-compatible backend and image compression in pipeline.py.
"""
import argparse
import base64
import difflib
import json
import os
import sys
import time
from pathlib import Path

import pipeline

READ_SYSTEM = (
    "You are a specialist in diplomatic transcription of 16th- and 17th-century "
    "printed Latin. Read the SCANNED IMAGE directly, independently, line by line. "
    "There is no previous OCR to follow. Transcribe only visible marks, not what "
    "you expect a Latin author to have written. Preserve spelling, capitals, "
    "punctuation, æ/œ, abbreviations, Greek, line breaks, hyphenated line endings, "
    "and long s (ſ) where visibly distinguishable. Do not translate, normalize, "
    "invent, or silently complete uncertain words. Mark unreadable spans [?]. "
    "Do not duplicate lines. Include partial first and last lines. Output only transcription."
)

RECONCILE_SYSTEM = (
    "You are an exacting historical Latin image proofreader. The IMAGE is the "
    "sole authority. You are given TWO fallible transcriptions: an older OCR draft "
    "and a new independent image reading. They may both be wrong. Re-read the "
    "printed image LINE BY LINE, adjudicating each disagreement by visible letter "
    "shapes, not Latin plausibility. In particular check long-s/f, u/v, i/j, rn/m, "
    "ligatures, broken type, line-end hyphens, headings, and repeated lines. "
    "Suspicious strings in the drafts are NOT evidence of what the page says. "
    "If you cannot verify a word visually, write [?], not a guessed Latin word. "
    "Preserve original spelling, punctuation, capitalization, Greek, and line "
    "breaks; do not modernize, translate, explain, or add material. "
    "Output ONLY the final corrected transcription."
)


def nonempty(path):
    return path.is_file() and path.stat().st_size > 0


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(text, encoding='utf-8')
    os.replace(temp, path)


def record_meta(out, stem, stage, model, cfg, elapsed, usage):
    meta = out / 'meta' / f'{stem}.json'
    data = json.loads(meta.read_text(encoding='utf-8')) if meta.exists() else {}
    data[stage] = {
        'model': model, 'backend': cfg['backend_name'],
        'seconds': round(elapsed, 2), **(usage or {})
    }
    atomic_write(meta, json.dumps(data, indent=2, ensure_ascii=False))


def vision_messages(system, image_url, text):
    # The image appears BEFORE any previous OCR, reducing anchoring on bad text.
    return [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': [
            {'type': 'image_url', 'image_url': {'url': image_url}},
            {'type': 'text', 'text': text},
        ]},
    ]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pages', required=True, help='PDF page number or range, e.g. 16 or 16-20')
    ap.add_argument('--config', default='config.toml')
    ap.add_argument('--force', action='store_true', help='redo both vision passes and translation')
    ap.add_argument('--single-pass', action='store_true',
                    help='one image-based correction call instead of two (cheaper, less independent)')
    args = ap.parse_args()

    config_path = Path(args.config).resolve()
    os.chdir(config_path.parent)
    cfg = pipeline.load_config(str(config_path))
    out = Path(cfg['book'].get('out_dir', 'out'))
    corrected_dir = out / 'corrected'
    english_dir = out / 'translations_corrected'
    independent_dir = out / 'independent_readings'
    diff_dir = out / 'correction_diffs'
    for directory in (corrected_dir, english_dir, independent_dir, diff_dir):
        directory.mkdir(parents=True, exist_ok=True)
    first, last = pipeline.parse_range(args.pages)
    if first < 1 or last < first:
        ap.error('Invalid page range')

    glossary_file = Path('glossary.txt')
    glossary = glossary_file.read_text(encoding='utf-8').strip() if glossary_file.exists() else ''
    backend = None
    for page in range(first, last + 1):
        stem = f'{page:04d}'
        image = out / 'pages' / f'{stem}.png'
        source = out / 'transcripts' / f'{stem}.txt'
        independent = independent_dir / f'{stem}.txt'
        corrected = corrected_dir / f'{stem}.txt'
        english = english_dir / f'{stem}.txt'
        diff_file = diff_dir / f'{stem}.diff.txt'

        if not nonempty(image) or not nonempty(source):
            print(f'Page {page}: missing image or original transcript; run pipeline.py first.', file=sys.stderr)
            return 1
        if nonempty(corrected) and nonempty(english) and not args.force:
            print(f'Page {page}: existing corrected results; skipping (use --force to retest)', flush=True)
            continue
        if backend is None:
            backend = pipeline.Backend(cfg)

        if args.force or not nonempty(corrected):
            jpeg = pipeline.make_api_image(image, cfg)
            image_url = 'data:image/jpeg;base64,' + base64.b64encode(jpeg).decode('ascii')
            draft = source.read_text(encoding='utf-8')

            if not args.single_pass:
                if args.force or not nonempty(independent):
                    print(f'Page {page}: pass 1/2, independent image transcription...', flush=True)
                    start = time.time()
                    result, usage = backend.chat(
                        backend.vision_model,
                        vision_messages(READ_SYSTEM, image_url, 'Read and transcribe this image. No commentary.'),
                        max_tokens=4096,
                    )
                    atomic_write(independent, result)
                    record_meta(out, stem, 'independent_read', backend.vision_model,
                                cfg, time.time() - start, usage)
                independent_text = independent.read_text(encoding='utf-8')
                user_text = (
                    'OLDER OCR DRAFT (unreliable):\n' + draft +
                    '\n\nINDEPENDENT IMAGE TRANSCRIPTION (also unreliable):\n' + independent_text +
                    '\n\nNow verify every line against the IMAGE and output the image-faithful Latin only.'
                )
                print(f'Page {page}: pass 2/2, reconcile both drafts against image...', flush=True)
            else:
                user_text = (
                    'UNRELIABLE OCR DRAFT:\n' + draft +
                    '\n\nRead the image independently, check every line, and output only verified Latin.'
                )
                print(f'Page {page}: single image-based correction pass...', flush=True)

            start = time.time()
            result, usage = backend.chat(
                backend.vision_model,
                vision_messages(RECONCILE_SYSTEM, image_url, user_text),
                max_tokens=4096,
            )
            atomic_write(corrected, result)
            record_meta(out, stem, 'correct_latin', backend.vision_model,
                        cfg, time.time() - start, usage)
            diff = ''.join(difflib.unified_diff(
                draft.splitlines(keepends=True), result.splitlines(keepends=True),
                fromfile='original OCR', tofile='corrected Latin',
            ))
            atomic_write(diff_file, diff if diff else 'No textual differences detected.\n')
            print(f'Page {page}: saved corrected Latin and comparison diff', flush=True)
            # A new correction invalidates the old corrected translation.
            if english.exists():
                english.unlink()

        if not nonempty(english):
            print(f'Page {page}: translating corrected Latin...', flush=True)
            src = cfg['book']['source_language']
            dst = cfg['book']['target_language']
            system = pipeline.TRANSLATE_SYSTEM.format(src=src, dst=dst)
            parts = []
            if glossary:
                parts.append('Glossary (use these renderings):\n' + glossary)
            parts.append(f'{src} text to translate:\n' + corrected.read_text(encoding='utf-8'))
            start = time.time()
            result, usage = backend.chat(backend.text_model, [
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': '\n\n'.join(parts)},
            ], max_tokens=4096)
            atomic_write(english, result)
            record_meta(out, stem, 'translate_corrected', backend.text_model,
                        cfg, time.time() - start, usage)
            print(f'Page {page}: corrected English saved', flush=True)

    lines = [f"# {Path(cfg['book']['pdf']).stem}: corrected {cfg['book']['source_language']} to {cfg['book']['target_language']}\n"]
    for p in sorted(corrected_dir.glob('*.txt')):
        translation = english_dir / p.name
        if nonempty(p) and nonempty(translation):
            lines.extend([f'## Page {int(p.stem)}\n', '### Corrected original\n',
                          p.read_text(encoding='utf-8'), '\n### Translation\n',
                          translation.read_text(encoding='utf-8'), '\n---\n'])
    assembled = out / 'side_by_side_corrected.md'
    atomic_write(assembled, '\n'.join(lines))
    print(f'Updated {assembled}', flush=True)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print('\nInterrupted. Re-run to resume.', file=sys.stderr)
        sys.exit(130)
