import logging
import shlex
import subprocess
import sys
from pathlib import Path

def _git(*args, cwd):
    try:
        return subprocess.check_output(
            ["git", *args], cwd=cwd, stderr=subprocess.DEVNULL, text=True,
        ).strip()
    except Exception:
        return None


def _find_repo_root(path):
    path = Path(path).expanduser().resolve()
    for candidate in (path, *path.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


class GitFilter(logging.Filter):
    first = True
    def __init__(self):
        super().__init__()
        self._fields = None

    def _build_fields(self):
        from odoo.tools import config  # noqa: PLC0415

        repos = []
        addons_path = config.get('addons_path')
        if not isinstance(addons_path, (list, tuple)):
            addons_path = addons_path.split(",")
        for raw in addons_path:
            raw = raw.strip()
            if not raw:
                continue
            repo = _find_repo_root(raw)
            if repo is None or repo in repos:
                continue
            repos.append(repo)

        fields = {}
        for root in repos:
            fields[f'git_branch_{root.name}'] = _git('rev-parse', '--abbrev-ref', 'HEAD', cwd=root)
            fields[f'git_commit_{root.name}'] = _git('rev-parse', '--short', 'HEAD', cwd=root)
        return fields

    def filter(self, record):
        if type(self).first:
            type(self).first = False
            logger = logging.getLogger('git_filter')
            logger.runbot(shlex.join(sys.argv))
        if self._fields is None:
            self._fields = self._build_fields()
        for key, value in self._fields.items():
            setattr(record, key, value)
        return True