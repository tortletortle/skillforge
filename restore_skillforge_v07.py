#!/usr/bin/env python3
"""Restore the verified SKILLFORGE archive to a new remote branch.
Run in WSL2 with Git credentials and Python/numpy already configured.
No force push; no main modifications. Requires archive SHA match.
"""
import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

EXPECTED = '9e4de07a100170641ed2a0d32f1b50b76d006a2993674cedda42a53e065efa93'
REPO = 'https://github.com/tortletortle/skillforge.git'
BRANCH = 'recovery/v0.7'


def run(*args, cwd=None, capture=False):
    p = subprocess.run(args, cwd=cwd, check=True, text=True,
                       stdout=subprocess.PIPE if capture else None)
    return p.stdout.strip() if capture else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('archive', type=Path)
    ap.add_argument('--remote', default=REPO, help='Git remote URL; defaults to the private SkillForge repo')
    ap.add_argument('--branch', default=BRANCH)
    args = ap.parse_args()
    archive = args.archive.resolve()
    if hashlib.sha256(archive.read_bytes()).hexdigest() != EXPECTED:
        raise SystemExit('Archive checksum mismatch; refusing to restore.')
    with tempfile.TemporaryDirectory(prefix='skillforge-restore-') as td:
        root = Path(td)
        checkout = root / 'repo'
        source = root / 'source'
        with ZipFile(archive) as z:
            if z.testzip() is not None:
                raise SystemExit('Archive CRC failure.')
            for member in z.infolist():
                path = PurePosixPath(member.filename)
                if path.is_absolute() or '..' in path.parts or '.git' in path.parts or '\\' in member.filename:
                    raise SystemExit(f'Unsafe archive member: {member.filename}')
            z.extractall(source)
        restored = source / 'SKILLFORGE_V0_7'
        if not (restored / 'skillforge' / '__init__.py').is_file() or not (restored / 'tests').is_dir():
            raise SystemExit('Missing source or tests.')
        run('git', 'clone', '--branch', 'main', '--single-branch', args.remote, str(checkout))
        if run('git', 'ls-remote', '--heads', 'origin', f'refs/heads/{args.branch}', cwd=checkout, capture=True):
            raise SystemExit(f'Remote branch {args.branch} already exists; inspect it or select a new branch. No overwrite performed.')
        run('git', 'checkout', '-b', args.branch, cwd=checkout)
        # Preserve archive reports and experiments; never copy VCS/cache data.
        for path in sorted(restored.rglob('*')):
            if not path.is_file() or path.suffix == '.pyc' or '__pycache__' in path.parts:
                continue
            dest = checkout / path.relative_to(restored)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
        # Verify archived bytes in working tree before test/commit.
        tracked = [p.relative_to(restored) for p in restored.rglob('*') if p.is_file()]
        for rel in tracked:
            if (checkout / rel).read_bytes() != (restored / rel).read_bytes():
                raise SystemExit(f'Content mismatch: {rel}')
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], cwd=checkout, env=env, check=True)
        # Add exact archived paths, including tiny fixtures; no generated local files.
        for rel in tracked:
            run('git', 'add', '-f', '--', rel.as_posix(), cwd=checkout)
        run('git', 'commit', '-m', 'Restore verified SKILLFORGE V0.7 source, experiments and tests', cwd=checkout)
        sha = run('git', 'rev-parse', 'HEAD', cwd=checkout, capture=True)
        run('git', 'push', 'origin', f'HEAD:refs/heads/{args.branch}', cwd=checkout)
        remote = run('git', 'ls-remote', '--heads', 'origin', f'refs/heads/{args.branch}', cwd=checkout, capture=True)
        if not remote or remote.split()[0] != sha:
            raise SystemExit('Remote commit does not match local commit.')
        print(f'REMOTE_VERIFIED branch={args.branch} commit={sha}')
        print('main was not modified. Review the recovery branch before merging.')

if __name__ == '__main__':
    main()
