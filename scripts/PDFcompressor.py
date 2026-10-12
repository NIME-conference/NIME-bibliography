"""
NIME PDF Compressor
===================

This script is used to compress NIME PDF papers so that their size is just
below 5 MB, which is necessary because Google Scholar does not index PDF files
larger than 5 MB. Without this compression, many NIME papers would not be
discoverable via Google Scholar.

IMPORTANT:
- The *compressed* PDFs produced by this script are the ones intended for the
  public-facing website (so that Google Scholar can index them).
- The *high-resolution* originals are preserved under new names ending in
  "_highres.pdf" in the same folder.
- The true, unmodified high-resolution versions are also preserved and shared
  on Zenodo. Zenodo itself is not indexed by Google Scholar, so we keep the
  full-quality files there while serving compressed versions on the NIME site.

Usage
-----

Run this script from the "proceedings" root directory, which contains year
subdirectories (2001, 2002, ..., 2026, and future years):

  - Dry run (no changes, just show what would be done):
      python3 PDFcompressor.py --dry-run

  - Compress all eligible NIME PDFs > 5 MB:
      python3 PDFcompressor.py

  - Undo compression (restore all *_highres.pdf files back
    to their original names):
      python3 PDFcompressor.py --undo

The script:
- Only considers files matching:
    nimeYEAR_NUMBER.pdf
    nimeYEAR_paperNUMBER.pdf
    nimeYEAR_music_NUMBER.pdf
    nimeYEAR_installations_NUMBER.pdf
- Skips any PDF whose name ends with "_fileNN.pdf" (e.g. "_file01.pdf"), which
  are supplementary files.
- Only compresses files larger than 5 MB.
- Renames the original to "*_highres.pdf" and writes a
  compressed version with the original filename.
- Iteratively adjusts Ghostscript image compression parameters to keep images
  as high quality as possible while bringing the PDF just under the 5 MB limit.
- Prints per-file details and a summary per year and overall.

Ghostscript Requirement
-----------------------

This script depends on Ghostscript (`gs`) to perform the actual PDF compression.
You **must** have Ghostscript installed and available in your system PATH.

Install instructions:

- macOS (Homebrew):
    1. Install Homebrew if you don't have it:
         /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    2. Install Ghostscript:
         brew install ghostscript

- Ubuntu / Debian (Linux):
    1. Update package lists:
         sudo apt-get update
    2. Install Ghostscript:
         sudo apt-get install ghostscript

- Fedora / RHEL (Linux):
    1. Install Ghostscript:
         sudo dnf install ghostscript

- Windows:
    1. Download the Ghostscript installer from:
         https://ghostscript.com/download.html
    2. Run the installer and follow the prompts.
    3. During installation, ensure that the option to add Ghostscript to the
       system PATH is enabled. If not, you may need to manually add the
       Ghostscript "bin" directory (e.g. "C:\\Program Files\\gs\\gs10.XX\\bin")
       to your PATH environment variable.
    4. Verify installation by running in a Command Prompt:
         gswin64c --version
       or (depending on version):
         gs --version

After Ghostscript is installed, verify it is available by running in a terminal:

    gs --version

If this prints a version number (e.g. "10.03.1"), the script should be able to
use Ghostscript for compression.
"""

import argparse
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Tuple, List, Optional

# ---------- Configuration ----------

MAX_BYTES = 5 * 1024 * 1024          # 5 MB
# We prefer to be safely below 5 MB; we will early-exit once we are under this.
EARLY_EXIT_BYTES = 4_800_000         # ~4.58 MB

# We also track the largest candidate <= MAX_BYTES as "best".
SAFETY_MARGIN = 64 * 1024
TARGET_BYTES = MAX_BYTES - SAFETY_MARGIN

# Compression profiles from very light to stronger.
# Each profile is a dict interpreted in run_ghostscript_profile().
COMPRESSION_PROFILES = [
    # 1) Very light: no forced JPEG, no downsampling, let Ghostscript choose filters.
    {
        "name": "losslessish_no_downsample",
        "downsample": False,
        "force_jpeg": False,
        "color_res": None,
        "jpeg_q": None,
    },
    # 2) Mild compression: 600 dpi, JPEG Q=95
    {
        "name": "600dpi_q95",
        "downsample": True,
        "force_jpeg": True,
        "color_res": 600,
        "jpeg_q": 95,
    },
    # 3) 450 dpi, JPEG Q=95
    {
        "name": "450dpi_q95",
        "downsample": True,
        "force_jpeg": True,
        "color_res": 450,
        "jpeg_q": 95,
    },
    # 4) 300 dpi, JPEG Q=95
    {
        "name": "300dpi_q95",
        "downsample": True,
        "force_jpeg": True,
        "color_res": 300,
        "jpeg_q": 95,
    },
    # 5) 300 dpi, JPEG Q=90
    {
        "name": "300dpi_q90",
        "downsample": True,
        "force_jpeg": True,
        "color_res": 300,
        "jpeg_q": 90,
    },
    # 6) 250 dpi, JPEG Q=85
    {
        "name": "250dpi_q85",
        "downsample": True,
        "force_jpeg": True,
        "color_res": 250,
        "jpeg_q": 85,
    },
    # 7) 200 dpi, JPEG Q=80
    {
        "name": "200dpi_q80",
        "downsample": True,
        "force_jpeg": True,
        "color_res": 200,
        "jpeg_q": 80,
    },
    # 8) 180 dpi, JPEG Q=75
    {
        "name": "180dpi_q75",
        "downsample": True,
        "force_jpeg": True,
        "color_res": 180,
        "jpeg_q": 75,
    },
    # 9) 150 dpi, JPEG Q=70
    {
        "name": "150dpi_q70",
        "downsample": True,
        "force_jpeg": True,
        "color_res": 150,
        "jpeg_q": 70,
    },
]

# Regex to match relevant NIME PDFs
NIME_PDF_PATTERN = re.compile(
    r"""^nime(?P<year>\d{4})_(
           \d+|
           paper\d+|
           music_\d+|
           installations_\d+
        )\.pdf$""",
    re.VERBOSE,
)

# Files containing _file01.pdf (or file02, etc.) are excluded entirely
EXCLUDE_FILE_RE = re.compile(r"_file\d+\.pdf$", re.IGNORECASE)


# ---------- Helpers ----------

def human_size(num_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024 or unit == "GB":
            return f"{num_bytes:.1f} {unit}" if unit != "B" else f"{num_bytes} {unit}"
        num_bytes /= 1024.0


def run_ghostscript_profile(input_pdf: Path, output_pdf: Path, profile: Dict) -> bool:
    """
    Run Ghostscript to compress one PDF according to a given profile.
    Returns True on success, False on failure.
    """
    cmd = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        "-dNOPAUSE",
        "-dBATCH",
        "-dQUIET",
        "-dDetectDuplicateImages=true",
        "-dCompressFonts=true",
        "-dSubsetFonts=true",
    ]

    downsample = profile.get("downsample", False)
    force_jpeg = profile.get("force_jpeg", False)
    color_res = profile.get("color_res", None)
    jpeg_q = profile.get("jpeg_q", None)

    if downsample and color_res is not None:
        # Downsampling enabled
        cmd += [
            "-dDownsampleColorImages=true",
            "-dColorImageDownsampleType=/Bicubic",
            f"-dColorImageResolution={color_res}",

            "-dDownsampleGrayImages=true",
            "-dGrayImageDownsampleType=/Bicubic",
            f"-dGrayImageResolution={color_res}",

            "-dDownsampleMonoImages=true",
            "-dMonoImageDownsampleType=/Subsample",
            "-dMonoImageResolution=600",
        ]
    else:
        # No downsampling
        cmd += [
            "-dDownsampleColorImages=false",
            "-dDownsampleGrayImages=false",
            "-dDownsampleMonoImages=false",
        ]

    # Image encoding
    if force_jpeg and jpeg_q is not None:
        cmd += [
            "-dEncodeColorImages=true",
            "-dEncodeGrayImages=true",
            "-dEncodeMonoImages=true",
            "-dAutoFilterColorImages=false",
            "-dAutoFilterGrayImages=false",
            "-dColorImageFilter=/DCTEncode",
            "-dGrayImageFilter=/DCTEncode",
            f"-dJPEGQ={jpeg_q}",
        ]
    else:
        # Let Ghostscript choose filters; typically more "lossless" / gentle
        cmd += [
            "-dAutoFilterColorImages=true",
            "-dAutoFilterGrayImages=true",
        ]
        # Do not set JPEGQ or explicit DCTEncode filters here.

    cmd += [
        f"-sOutputFile={str(output_pdf)}",
        str(input_pdf),
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def choose_highres_name(original: Path) -> Path:
    """
    Choose a backup filename for the original, using *_highres.pdf only.
    If that name already exists, append a numerical suffix.
    """
    stem = original.stem
    parent = original.parent

    candidate = parent / f"{stem}_highres.pdf"
    if not candidate.exists():
        return candidate

    # If *_highres.pdf exists, append a numerical suffix
    i = 1
    while True:
        c = parent / f"{stem}_highres_{i}.pdf"
        if not c.exists():
            return c
        i += 1


def is_nime_target_pdf(path: Path) -> Optional[str]:
    """
    Return the year as a string if this path is a target NIME PDF, otherwise None.
    """
    if not path.is_file():
        return None
    if path.suffix.lower() != ".pdf":
        return None
    name = path.name
    if EXCLUDE_FILE_RE.search(name):
        return None

    m = NIME_PDF_PATTERN.match(name)
    if not m:
        return None
    return m.group("year")


# ---------- Compression Logic ----------

def compress_pdf_to_target(original: Path, backup_highres: Path) -> Tuple[bool, int]:
    """
    Compress `original` PDF (which is already renamed to `backup_highres`).
    Iteratively tries different Ghostscript profiles starting from the original
    high-res PDF each time.

    Strategy:
    - Try profiles from lightest to stronger compression.
    - Track:
        * best_under: largest size <= MAX_BYTES (closest under the limit)
        * best_over: smallest size > MAX_BYTES (in case nothing gets under)
    - Prefer best_under; if none, fall back to best_over (may still be > 5 MB).

    We early-exit as soon as we get a candidate at or above EARLY_EXIT_BYTES,
    i.e. safely under 5 MB, to avoid over-compressing.
    """
    src = backup_highres
    tmp_output = original.with_suffix(".tmp.pdf")

    best_under_size: Optional[int] = None
    best_under_path: Optional[Path] = None
    best_over_size: Optional[int] = None
    best_over_path: Optional[Path] = None

    for profile in COMPRESSION_PROFILES:
        if tmp_output.exists():
            tmp_output.unlink()

        ok = run_ghostscript_profile(src, tmp_output, profile)
        if not ok or not tmp_output.exists():
            continue

        size = tmp_output.stat().st_size

        if size <= MAX_BYTES:
            # Candidate under the 5 MB limit: keep the largest one
            if (best_under_size is None) or (size > best_under_size):
                if best_under_path is not None and best_under_path.exists():
                    best_under_path.unlink()
                prof_name = profile.get("name", "profile")
                best_under_path = original.with_suffix(f".under_{prof_name}.pdf")
                tmp_output.replace(best_under_path)
                best_under_size = size
            else:
                # Not a new best; delete this tmp_output
                tmp_output.unlink()

            # Early exit if we are already safely under the limit
            if size >= EARLY_EXIT_BYTES:
                break

        else:
            # size > MAX_BYTES – track the smallest over-limit candidate
            if (best_over_size is None) or (size < best_over_size):
                if best_over_path is not None and best_over_path.exists():
                    best_over_path.unlink()
                prof_name = profile.get("name", "profile")
                best_over_path = original.with_suffix(f".over_{prof_name}.pdf")
                tmp_output.replace(best_over_path)
                best_over_size = size
            else:
                # Not a new best-over; delete tmp_output
                tmp_output.unlink()

    # Final safety: ensure tmp_output is removed
    if tmp_output.exists():
        tmp_output.unlink()

    # Decide which candidate to use
    chosen_path: Optional[Path] = None
    chosen_size: Optional[int] = None

    if best_under_path is not None:
        chosen_path = best_under_path
        chosen_size = best_under_size
        # We don't need the "over" candidate anymore
        if best_over_path is not None and best_over_path.exists():
            best_over_path.unlink()
    elif best_over_path is not None:
        # Nothing got under 5 MB; use the least-bad over-limit version
        chosen_path = best_over_path
        chosen_size = best_over_size
    else:
        # No candidate created – restore original
        if original.exists():
            original.unlink()
        backup_highres.replace(original)
        # Clean up any accidental tmp file
        if tmp_output.exists():
            tmp_output.unlink()
        return False, backup_highres.stat().st_size

    # Replace original with chosen candidate
    if original.exists():
        original.unlink()
    chosen_path.replace(original)

    # Clean up any leftover candidate files (.under_*.pdf or .over_*.pdf)
    for f in original.parent.glob(f"{original.stem}.under_*.pdf"):
        if f.exists():
            f.unlink()
    for f in original.parent.glob(f"{original.stem}.over_*.pdf"):
        if f.exists():
            f.unlink()

    # One more safety cleanup: remove any lingering .tmp.pdf for this base name
    tmp_glob = original.parent.glob(f"{original.stem}.tmp.pdf")
    for f in tmp_glob:
        if f.exists():
            f.unlink()

    return True, chosen_size  # type: ignore[arg-type]


# ---------- Stats structures ----------

class FolderStats:
    def __init__(self):
        self.total_size_before = 0
        self.total_size_after = 0
        self.file_count = 0
        self.above_limit_count = 0
        self.compressed_count = 0


def scan_and_compress(root: Path, dry_run: bool = False) -> None:
    """
    Scan year folders under `root`, compress PDFs over 5 MB,
    and print detailed statistics.
    """
    year_stats: Dict[str, FolderStats] = defaultdict(FolderStats)
    total_big_files = 0
    total_compressed_files = 0

    # Collect all candidate PDFs first
    pdfs_to_process: List[Tuple[str, Path]] = []

    for year_dir in sorted(root.iterdir()):
        if not year_dir.is_dir():
            continue
        for path in year_dir.rglob("*.pdf"):
            year = is_nime_target_pdf(path)
            if year is None:
                continue
            pdfs_to_process.append((year, path))

    # First pass: compute "before" sizes and count big files
    for year, path in pdfs_to_process:
        size = path.stat().st_size
        st = year_stats[year]
        st.file_count += 1
        st.total_size_before += size
        st.total_size_after += size  # will be updated if compressed

        if size > MAX_BYTES:
            st.above_limit_count += 1
            total_big_files += 1

    print(f"Found {len(pdfs_to_process)} candidate NIME PDFs.")
    print(f"Files above {human_size(MAX_BYTES)}: {total_big_files}")
    print()

    # Second pass: compress big files
    for year, path in pdfs_to_process:
        size_before = path.stat().st_size
        if size_before <= MAX_BYTES:
            continue

        st = year_stats[year]

        # Skip if a highres backup already exists (to avoid re-compressing)
        backup_candidate = choose_highres_name(path)
        existing_backups = list(path.parent.glob(path.stem + "_highres*.pdf"))
        if existing_backups:
            print(f"[SKIP] {path} (backup already present; probably compressed earlier)")
            continue

        print(f"[COMPRESS] {path}")
        print(f"  Original size: {human_size(size_before)}")

        if dry_run:
            print("  Dry run: no changes made.")
            print()
            continue

        backup_highres = backup_candidate
        # Rename original -> backup_highres
        try:
            path.replace(backup_highres)
        except OSError as e:
            print(f"  ERROR: Could not rename to backup ({e}); skipping.")
            continue

        success, size_after = compress_pdf_to_target(path, backup_highres)

        if not success:
            print("  ERROR: Compression failed. Original restored.")
            # Restore stats: file_after is original size
            year_stats[year].total_size_after -= size_before
            year_stats[year].total_size_after += backup_highres.stat().st_size
            print()
            continue

        st.compressed_count += 1
        total_compressed_files += 1

        st.total_size_after -= size_before
        st.total_size_after += size_after

        print(f"  New size:      {human_size(size_after)}")
        delta = size_before - size_after
        print(f"  Saved:         {human_size(delta)}")
        print(f"  Backup (highres): {backup_highres.name}")
        print()

    # ---------- Summary ----------

    print("\n=== Per-year statistics ===")
    for year in sorted(year_stats.keys()):
        st = year_stats[year]
        if st.file_count == 0:
            continue
        avg_before = st.total_size_before / st.file_count
        avg_after = st.total_size_after / st.file_count
        print(f"Year {year}:")
        print(f"  Files considered: {st.file_count}")
        print(f"  Above {human_size(MAX_BYTES)}: {st.above_limit_count}")
        print(f"  Compressed: {st.compressed_count}")
        print(f"  Avg size before: {human_size(avg_before)}")
        print(f"  Avg size after:  {human_size(avg_after)}")
        print()

    print("=== Overall ===")
    total_files = sum(st.file_count for st in year_stats.values())
    total_before = sum(st.total_size_before for st in year_stats.values())
    total_after = sum(st.total_size_after for st in year_stats.values())
    print(f"Total files considered: {total_files}")
    print(f"Total > {human_size(MAX_BYTES)}: {total_big_files}")
    print(f"Total compressed: {total_compressed_files}")
    if total_files > 0:
        print(f"Overall average before: {human_size(total_before / total_files)}")
        print(f"Overall average after:  {human_size(total_after / total_files)}")


# ---------- Undo logic ----------

def undo_compression(root: Path, dry_run: bool = False) -> None:
    """
    Restore all *_highres.pdf backups to their original names.
    """
    restored_count = 0

    for pdf in root.rglob("*.pdf"):
        name = pdf.name
        if name.endswith("_highres.pdf"):
            base_name = name[:-len("_highres.pdf")] + ".pdf"
        else:
            continue

        original_path = pdf.parent / base_name

        # Overwrite existing compressed version with highres (if any)
        if dry_run:
            print(f"[UNDO dry-run] Would restore {pdf} -> {original_path}")
        else:
            if original_path.exists():
                # Backup current compressed just in case
                tmp_backup = original_path.with_suffix(".undo_backup.pdf")
                shutil.move(str(original_path), str(tmp_backup))
                try:
                    pdf.replace(original_path)
                finally:
                    if tmp_backup.exists():
                        tmp_backup.unlink()
            else:
                # No compressed file present, just rename
                pdf.replace(original_path)

        restored_count += 1

    print(f"Restored highres originals for {restored_count} files.")


# ---------- CLI ----------

def main():
    parser = argparse.ArgumentParser(
        description="Compress NIME PDFs to just under 5MB, with undo support."
    )
    parser.add_argument(
        "--root",
        type=str,
        default=".",
        help="Root folder containing year subfolders (default: current directory).",
    )
    parser.add_argument(
        "--undo",
        action="store_true",
        help="Undo mode: restore *_highres.pdf backups.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run: scan and show actions, but do not modify any files.",
    )

    args = parser.parse_args()
    root = Path(args.root).resolve()

    if not root.exists() or not root.is_dir():
        print(f"Root directory {root} does not exist or is not a directory.", file=sys.stderr)
        sys.exit(1)

    if args.undo:
        print(f"UNDO mode on root: {root}")
        undo_compression(root, dry_run=args.dry_run)
    else:
        print(f"Compression mode on root: {root}")
        if args.dry_run:
            print("Dry run: no files will be modified.\n")
        scan_and_compress(root, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
