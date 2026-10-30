"""Locate (or download) texcount and a Perl interpreter to run it."""
import os
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

TEXCOUNT_URL = "https://app.uio.no/ifi/texcount/download.php?file=texcount_3_2_0_41.zip"
PERL_URL = ("https://github.com/StrawberryPerl/Perl-Dist-Strawberry/releases/download/"
            "SP_54231_64bit/strawberry-perl-5.42.3.1-64bit-portable.zip")


def cache_dir():
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return base / "chi-preflight"


def _download_zip(url, dest, attempts=3):
    dest.mkdir(parents=True, exist_ok=True)
    zpath = dest / "download.zip"
    last = None
    for _ in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "chi-preflight"})
            with urllib.request.urlopen(req, timeout=120) as r, open(zpath, "wb") as f:
                shutil.copyfileobj(r, f)
            with zipfile.ZipFile(zpath) as z:
                z.extractall(dest)
            return
        except Exception as e:
            last = e
        finally:
            zpath.unlink(missing_ok=True)
    raise RuntimeError(f"{type(last).__name__}: {last}")


def _find_texcount(root):
    return next(iter(root.rglob("texcount.pl")), None)


def _find_perl(root):
    return next(iter(root.rglob("perl.exe")), None) if sys.platform == "win32" else None


def get_texcount(log=None):
    """Return ([command prefix], None) ready to append texcount args to, or (None, reason)."""
    log = log or (lambda msg: None)
    exe = shutil.which("texcount")
    if exe:
        return [exe], None

    root = cache_dir()
    script = _find_texcount(root / "texcount")
    if not script:
        try:
            log("Downloading texcount...")
            _download_zip(TEXCOUNT_URL, root / "texcount")
        except Exception as e:
            return None, f"Could not download texcount: {e}"
        script = _find_texcount(root / "texcount")
        if not script:
            return None, "Downloaded texcount archive did not contain texcount.pl"

    perl = shutil.which("perl")
    if not perl and sys.platform == "win32":
        portable = _find_perl(root / "perl")
        # Strawberry's perl.exe lives under perl\bin; skip the c\bin helpers
        if not portable:
            try:
                log("Perl not found; downloading portable Strawberry Perl (large download)...")
                _download_zip(PERL_URL, root / "perl")
            except Exception as e:
                return None, f"Perl not found and download failed: {e}"
            portable = _find_perl(root / "perl")
        perl = str(portable) if portable else None
    if not perl:
        return None, ("Perl not found; texcount needs Perl. "
                      "Install it with your package manager (e.g. apt install perl / brew install perl)")
    return [perl, str(script)], None
