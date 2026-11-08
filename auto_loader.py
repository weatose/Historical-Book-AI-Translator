import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='Process one PDF page at a time with cooldown and retries')
    parser.add_argument('--start', type=int, required=True)
    parser.add_argument('--end', type=int, required=True)
    parser.add_argument('--wait', type=float, default=30, help='Seconds between completed pages')
    parser.add_argument('--retry-wait', type=float, default=120, help='Seconds after a failed attempt')
    parser.add_argument('--retries', type=int, default=3, help='Extra attempts per page before stopping')
    parser.add_argument('--config', default='config.toml')
    parser.add_argument('--correct', action='store_true', help='also proofread scanned Latin and translate corrected text')
    args = parser.parse_args()
    if args.start < 1 or args.end < args.start or args.wait < 0 or args.retry_wait < 0 or args.retries < 0:
        parser.error('Invalid page range, wait time, or retry count')
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib
    config_path = Path(args.config).resolve()
    with config_path.open('rb') as f:
        cfg = tomllib.load(f)
    workdir = config_path.parent
    out = Path(cfg['book'].get('out_dir', 'out'))
    if not out.is_absolute():
        out = workdir / out
    log_path = workdir / 'auto_loader.log'

    def log(msg):
        line = f'[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}'
        print(line, flush=True)
        with log_path.open('a', encoding='utf-8') as f:
            f.write(line + '\n')

    def completed(page, corrected=False):
        name = f'{page:04d}.txt'
        folders = ('corrected', 'translations_corrected') if corrected else ('transcripts', 'translations')
        return all((out / sub / name).is_file() and (out / sub / name).stat().st_size > 0 for sub in folders)

    def run_command(cmd):
        with log_path.open('a', encoding='utf-8') as f:
            return subprocess.run(cmd, cwd=workdir, stdout=f, stderr=subprocess.STDOUT).returncode

    log(f'Starting pages {args.start}-{args.end}; cooldown={args.wait}s; retry wait={args.retry_wait}s; correction={args.correct}')
    for page in range(args.start, args.end + 1):
        if completed(page) and (not args.correct or completed(page, corrected=True)):
            log(f'Page {page} already complete; skipping')
            continue
        for attempt in range(1, args.retries + 2):
            log(f'Page {page}: attempt {attempt}/{args.retries + 1}')
            result = 0
            if not completed(page):
                cmd = [sys.executable, '-u', str(workdir / 'pipeline.py'), 'run', '--config', str(config_path), '--pages', str(page)]
                result = run_command(cmd)
            if result == 0 and completed(page) and args.correct and not completed(page, corrected=True):
                log(f'Page {page}: proofreading and retranslating')
                cmd = [sys.executable, '-u', str(workdir / 'correct_latin.py'), '--config', str(config_path), '--pages', str(page)]
                result = run_command(cmd)
            if result == 0 and completed(page) and (not args.correct or completed(page, corrected=True)):
                log(f'Page {page} complete' + (' (including correction)' if args.correct else ''))
                break
            log(f'Page {page} failed or incomplete (exit {result}); see auto_loader.log')
            if attempt <= args.retries:
                log(f'Waiting {args.retry_wait}s before retry')
                time.sleep(args.retry_wait)
        else:
            log(f'Stopping at page {page} after {args.retries + 1} attempts. Re-run to resume.')
            return 1
        if page < args.end:
            log(f'Cooling down {args.wait}s')
            time.sleep(args.wait)
    log('All requested pages complete')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print('\nStopped by user; run the same command to resume.', flush=True)
        sys.exit(130)
