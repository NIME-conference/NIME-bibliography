"""
NIME PDF Compressor
===================

Compress NIME PDF papers so their size is just below 5 MB (Google Scholar's
limit), with a preferred target of 4.8 MB.

IMPORTANT:
- Public-facing PDFs are the compressed ones.
- Original/uncompressed PDFs are preserved as *_uncompressed.pdf alongside.
- Zenodo holds the true originals; those are not Google Scholar-indexed.

Size model
----------

Google Scholar's documentation uses standard decimal megabytes:

- 1 MB = 1,000,000 bytes (decimal, not binary MiB).
- Hard limit: 5 MB = 5,000,000 bytes.

To ensure a document is never skipped by the parser, it is safest to keep
the final file size strictly under 5,000,000 bytes.

We therefore set:

- SCHOLAR_LIMIT_BYTES = 5_000_000 (hard ceiling).
- MAX_BYTES = SCHOLAR_LIMIT_BYTES.
- Preferred target: TARGET_BYTES = 4_800_000 (4.8 MB).
- EARLY_EXIT_BYTES = 4_750_000.

We aim for TARGET_BYTES, but if the best we can do without destroying quality
is somewhere between TARGET_BYTES and MAX_BYTES, we keep that and *flag* the file.

Tools required
--------------

This script uses:

1. Ghostscript (`gs`) — for PDF compression via manual profiles + /ebook fallback.
2. cpdf (`cpdf`) — for image recompression (using ImageMagick) when Ghostscript
   cannot get under the limit.

Ghostscript
-----------

- macOS (Homebrew):

    # If you don't have Homebrew yet:
    # /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    brew install ghostscript

- Ubuntu / Debian:

    sudo apt-get update
    sudo apt-get install ghostscript

- Fedora / RHEL:

    sudo dnf install ghostscript

- Windows:

    - Download from: https://ghostscript.com/download.html
    - Install and ensure the Ghostscript "bin" directory (e.g.
      "C:\\Program Files\\gs\\gs10.XX\\bin") is in your PATH.
    - Test:
        gs --version

cpdf
----

- macOS (Homebrew):

    brew install cpdf

- Linux:

    - Download binaries from: https://community.coherentpdf.com/downloads.html
    - Extract and place `cpdf` in a directory in your PATH, e.g.:

        tar xzf cpdf-binaries.tar.gz
        sudo mv cpdf /usr/local/bin/
        sudo chmod +x /usr/local/bin/cpdf

    - Test:
        cpdf -version

- Windows:

    - Download `cpdf.exe` from: https://community.coherentpdf.com/downloads.html
    - Put it in a directory like `C:\\Tools\\cpdf` and add that to your PATH.
    - Test:
        cpdf -version

ImageMagick (for cpdf image resampling)
---------------------------------------

cpdf’s -process-images downsampling relies on `magick` (ImageMagick).

- macOS (Homebrew):

    brew install imagemagick

- Linux:

    sudo apt-get install imagemagick

- Windows:

    - Install from https://imagemagick.org
    - Ensure `magick` is on your PATH.

Verify:

    which magick   # macOS / Linux
    magick -version
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

SCHOLAR_LIMIT_BYTES = 5_000_000      # hard Google Scholar ceiling (decimal MB)
MAX_BYTES = SCHOLAR_LIMIT_BYTES      # no file may exceed this

TARGET_BYTES = 4_800_000             # 4.8 MB preferred target
EARLY_EXIT_BYTES = 4_750_000         # early exit band near the target

# Ghostscript MANUAL profiles (no /ebook here).
# We progressively lower resolution and JPEG quality.
GS_MANUAL_PROFILES = [
    # 1) Very light: no downsampling, auto image filters.
    {
        "name": "gs_losslessish_no_downsample",
        "downsample": False,
        "color_res": None,
        "jpeg_q": None,
    },
    # 2) 600 dpi, JPEG Q=95
    {
        "name": "gs_600dpi_q95",
        "downsample": True,
        "color_res": 600,
        "jpeg_q": 95,
    },
    # 3) 450 dpi, JPEG Q=95
    {
        "name": "gs_450dpi_q95",
        "downsample": True,
        "color_res": 450,
        "jpeg_q": 95,
    },
    # 4) 300 dpi, JPEG Q=95
    {
        "name": "gs_300dpi_q95",
        "downsample": True,
        "color_res": 300,
        "jpeg_q": 95,
    },
    # 5) 250 dpi, JPEG Q=90
    {
        "name": "gs_250dpi_q90",
        "downsample": True,
        "color_res": 250,
        "jpeg_q": 90,
    },
    # 6) 200 dpi, JPEG Q=90
    {
        "name": "gs_200dpi_q90",
        "downsample": True,
        "color_res": 200,
        "jpeg_q": 90,
    },
    # 7) 150 dpi, JPEG Q=85
    {
        "name": "gs_150dpi_q85",
        "downsample": True,
        "color_res": 150,
        "jpeg_q": 85,
    },
    # 8) 120 dpi, JPEG Q=85
    {
        "name": "gs_120dpi_q85",
        "downsample": True,
        "color_res": 120,
        "jpeg_q": 85,
    },
    # 9) 100 dpi, JPEG Q=80
    {
        "name": "gs_100dpi_q80",
        "downsample": True,
        "color_res": 100,
        "jpeg_q": 80,
    },
]

# Ghostscript /ebook fallback profile
GS_EBOOK_PROFILE = {
    "name": "gs_ebook",
    "type": "ebook",
}

# cpdf image recompression profiles mirroring the GS ladder
# cpdf uses floats for quality (e.g. 0.8 ~ 80%).
CPDF_PROFILES = [
    {"name": "cpdf_600dpi_q0.95", "jpeg_dpi": 600, "jpeg_quality": 0.95},
    {"name": "cpdf_450dpi_q0.95", "jpeg_dpi": 450, "jpeg_quality": 0.95},
    {"name": "cpdf_300dpi_q0.95", "jpeg_dpi": 300, "jpeg_quality": 0.95},
    {"name": "cpdf_250dpi_q0.90", "jpeg_dpi": 250, "jpeg_quality": 0.90},
    {"name": "cpdf_200dpi_q0.90", "jpeg_dpi": 200, "jpeg_quality": 0.90},
    {"name": "cpdf_150dpi_q0.85", "jpeg_dpi": 150, "jpeg_quality": 0.85},
    {"name": "cpdf_120dpi_q0.85", "jpeg_dpi": 120, "jpeg_quality": 0.85},
    {"name": "cpdf_100dpi_q0.80", "jpeg_dpi": 100, "jpeg_quality": 0.80},
]

# Only consider NIME PDFs with the canonical naming patterns.
NIME_PDF_PATTERN = re.compile(
    r"""^nime(?P<year>\d{4})_(
           \d+|
           paper\d+|
           music_\d+|
           music\d+|
           installations_\d+|
           alt_\d+
        )\.pdf$""",
    re.VERBOSE,
)

# Skip supplementary files like *_file01.pdf
EXCLUDE_FILE_RE = re.compile(r"_file\d+\.pdf$", re.IGNORECASE)


# ---------- Helpers ----------

def human_size(num_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024 or unit == "GB":
            return f"{num_bytes:.1f} {unit}" if unit != "B" else f"{num_bytes} {unit}"
        num_bytes /= 1024.0


def run_ghostscript_manual(input_pdf: Path, output_pdf: Path, profile: Dict) -> bool:
    """
    Run Ghostscript with a manual profile (moderate downsampling + JPEG).
    """
    base_cmd = [
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

    cmd = list(base_cmd)

    downsample = profile.get("downsample", False)
    color_res = profile.get("color_res", None)
    jpeg_q = profile.get("jpeg_q", None)

    if downsample and color_res is not None:
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
        cmd += [
            "-dDownsampleColorImages=false",
            "-dDownsampleGrayImages=false",
            "-dDownsampleMonoImages=false",
        ]

    if jpeg_q is not None:
        cmd += [
            "-dAutoFilterColorImages=false",
            "-dColorImageFilter=/DCTEncode",
            f"-dJPEGQ={jpeg_q}",
        ]
    else:
        cmd += ["-dAutoFilterColorImages=true"]

    cmd += [
        "-dAutoFilterGrayImages=true",
        f"-sOutputFile={str(output_pdf)}",
        str(input_pdf),
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_pdf.exists()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def run_ghostscript_ebook(input_pdf: Path, output_pdf: Path) -> bool:
    """
    Run Ghostscript with /ebook preset (last resort).
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
        "-dPDFSETTINGS=/ebook",
        f"-sOutputFile={str(output_pdf)}",
        str(input_pdf),
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_pdf.exists()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def run_cpdf_process_images(input_pdf: Path, output_pdf: Path, profile: Dict) -> bool:
    """
    Run cpdf image-processing profile:

        cpdf -process-images \
             -lossless-to-jpeg <quality> \
             -jpeg-to-jpeg <quality> \
             -jpeg-to-jpeg-dpi <dpi> \
             in.pdf AND -compress -o out.pdf

    Using ImageMagick (magick) under the hood for downsampling.
    """
    jpeg_dpi = profile.get("jpeg_dpi", 300)
    jpeg_quality = profile.get("jpeg_quality", 0.90)

    cmd = [
        "cpdf",
        "-process-images",
        "-lossless-to-jpeg",
        str(jpeg_quality),
        "-jpeg-to-jpeg",
        str(jpeg_quality),
        "-jpeg-to-jpeg-dpi",
        str(jpeg_dpi),
        str(input_pdf),
        "AND",
        "-compress",
        "-o",
        str(output_pdf),
    ]
    try:
        result = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            return False
        return output_pdf.exists()
    except FileNotFoundError:
        return False


def choose_uncompressed_name(original: Path) -> Path:
    stem = original.stem
    parent = original.parent

    candidate = parent / f"{stem}_uncompressed.pdf"
    if not candidate.exists():
        return candidate

    i = 1
    while True:
        c = parent / f"{stem}_uncompressed_{i}.pdf"
        if not c.exists():
            return c
        i += 1


def is_nime_target_pdf(path: Path) -> Optional[str]:
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


# ---------- Profile runners ----------

def run_gs_manual_profiles(src: Path, original: Path) -> Tuple[
    Optional[Path], Optional[int], Optional[Path], Optional[int]
]:
    """
    Run Ghostscript manual profiles (no /ebook) against `src`, tracking:

    - best_under: largest size <= MAX_BYTES
    - best_over: smallest size > MAX_BYTES

    Returns:
        best_under_path, best_under_size, best_over_path, best_over_size
    """
    tmp_output = original.with_suffix(".gs_tmp.pdf")

    best_under_size: Optional[int] = None
    best_under_path: Optional[Path] = None
    best_over_size: Optional[int] = None
    best_over_path: Optional[Path] = None

    for profile in GS_MANUAL_PROFILES:
        prof_name = profile.get("name", "gs_profile")

        if tmp_output.exists():
            tmp_output.unlink()

        ok = run_ghostscript_manual(src, tmp_output, profile)
        if not ok or not tmp_output.exists():
            continue

        size = tmp_output.stat().st_size

        if size <= MAX_BYTES:
            if (best_under_size is None) or (size > best_under_size):
                if best_under_path is not None and best_under_path.exists():
                    best_under_path.unlink()
                best_under_path = original.with_suffix(f".under_{prof_name}.pdf")
                tmp_output.replace(best_under_path)
                best_under_size = size
            else:
                tmp_output.unlink()

            if size <= TARGET_BYTES and size >= EARLY_EXIT_BYTES:
                break
        else:
            if (best_over_size is None) or (size < best_over_size):
                if best_over_path is not None and best_over_path.exists():
                    best_over_path.unlink()
                best_over_path = original.with_suffix(f".over_{prof_name}.pdf")
                tmp_output.replace(best_over_path)
                best_over_size = size
            else:
                tmp_output.unlink()

    if tmp_output.exists():
        tmp_output.unlink()

    return best_under_path, best_under_size, best_over_path, best_over_size


def run_cpdf_profiles(src: Path, original: Path) -> Tuple[
    Optional[Path], Optional[int], Optional[Path], Optional[int]
]:
    """
    Run cpdf-based image recompression profiles (matching the GS ladder):

    - For each CPDF_PROFILE:
      cpdf -process-images -lossless-to-jpeg <q> -jpeg-to-jpeg <q> -jpeg-to-jpeg-dpi <dpi>
           src AND -compress -o tmp

    Track best_under / best_over similar to GS.
    """
    tmp_output = original.with_suffix(".cpdf_tmp.pdf")

    best_under_size: Optional[int] = None
    best_under_path: Optional[Path] = None
    best_over_size: Optional[int] = None
    best_over_path: Optional[Path] = None

    for profile in CPDF_PROFILES:
        prof_name = profile.get("name", "cpdf_profile")

        if tmp_output.exists():
            tmp_output.unlink()

        ok = run_cpdf_process_images(src, tmp_output, profile)
        if not ok or not tmp_output.exists():
            continue

        size = tmp_output.stat().st_size

        if size <= MAX_BYTES:
            if (best_under_size is None) or (size > best_under_size):
                if best_under_path is not None and best_under_path.exists():
                    best_under_path.unlink()
                best_under_path = original.with_suffix(f".under_{prof_name}.pdf")
                tmp_output.replace(best_under_path)
                best_under_size = size
            else:
                tmp_output.unlink()

            if size <= TARGET_BYTES and size >= EARLY_EXIT_BYTES:
                break
        else:
            if (best_over_size is None) or (size < best_over_size):
                if best_over_path is not None and best_over_path.exists():
                    best_over_path.unlink()
                best_over_path = original.with_suffix(f".over_{prof_name}.pdf")
                tmp_output.replace(best_over_path)
                best_over_size = size
            else:
                tmp_output.unlink()

    if tmp_output.exists():
        tmp_output.unlink()

    return best_under_path, best_under_size, best_over_path, best_over_size


# ---------- Compression Logic ----------

def compress_pdf_to_target(original: Path, backup_uncompressed: Path) -> Tuple[bool, int, bool]:
    """
    Compress `original` PDF (already renamed to `backup_uncompressed`).

    Strategy:

    1. Run Ghostscript manual profiles on backup_uncompressed.
       - If we find a candidate <= MAX_BYTES: choose best_under.
    2. If Ghostscript manual fails to produce <= MAX_BYTES:
       - Run cpdf profiles on backup_uncompressed.
       - If we find a candidate <= MAX_BYTES: choose best_under.
    3. If still no <= MAX_BYTES:
       - Run Ghostscript /ebook on backup_uncompressed.
       - Choose the smallest among:
         - GS manual best_over
         - cpdf best_over
         - /ebook output
       - Note: we still enforce MAX_BYTES; we will only accept candidates
         whose size <= MAX_BYTES.
    4. If nothing at all is produced:
       - Restore the original.
    5. Flag the file if final_size > TARGET_BYTES.

    Returns:
        success (bool),
        final_size (int),
        flagged (bool): True if final_size > TARGET_BYTES
    """
    src = backup_uncompressed

    # 1) Ghostscript manual
    gs_under_path, gs_under_size, gs_over_path, gs_over_size = run_gs_manual_profiles(src, original)

    if gs_under_size is not None and gs_under_size <= MAX_BYTES:
        chosen_path = gs_under_path
        chosen_size = gs_under_size
        if gs_over_path is not None and gs_over_path.exists():
            gs_over_path.unlink()
    else:
        # 2) cpdf image recompression
        cpdf_under_path, cpdf_under_size, cpdf_over_path, cpdf_over_size = run_cpdf_profiles(src, original)

        if cpdf_under_size is not None and cpdf_under_size <= MAX_BYTES:
            chosen_path = cpdf_under_path
            chosen_size = cpdf_under_size
            if gs_over_path is not None and gs_over_path.exists():
                gs_over_path.unlink()
            if cpdf_over_path is not None and cpdf_over_path.exists():
                cpdf_over_path.unlink()
        else:
            # 3) Ghostscript /ebook fallback
            ebook_output = original.with_suffix(".gs_ebook_tmp.pdf")
            ok_ebook = run_ghostscript_ebook(src, ebook_output)
            ebook_size = ebook_output.stat().st_size if (ok_ebook and ebook_output.exists()) else None

            # Collect all candidates (over-limit from GS/cpdf + /ebook),
            # but we will only accept <= MAX_BYTES.
            candidates: List[Tuple[Path, int]] = []
            if gs_over_path is not None and gs_over_size is not None:
                candidates.append((gs_over_path, gs_over_size))
            if cpdf_over_path is not None and cpdf_over_size is not None:
                candidates.append((cpdf_over_path, cpdf_over_size))
            if ebook_size is not None:
                candidates.append((ebook_output, ebook_size))

            # Filter to those within MAX_BYTES
            candidates = [(p, s) for (p, s) in candidates if s <= MAX_BYTES]

            if not candidates:
                # Nothing usable under MAX_BYTES; restore original
                if original.exists():
                    original.unlink()
                backup_uncompressed.replace(original)
                # size of restored original:
                restored_size = original.stat().st_size
                return False, restored_size, False

            candidates.sort(key=lambda x: x[1])
            chosen_path, chosen_size = candidates[0]

            # Delete other candidates
            for path, _sz in candidates[1:]:
                if path.exists():
                    path.unlink()

    # Replace original with chosen candidate
    if original.exists():
        original.unlink()
    chosen_path.replace(original)

    # Clean up leftover candidate files
    for f in original.parent.glob(f"{original.stem}.under_*.pdf"):
        if f.exists():
            f.unlink()
    for f in original.parent.glob(f"{original.stem}.over_*.pdf"):
        if f.exists():
            f.unlink()
    for f in original.parent.glob(f"{original.stem}.gs_tmp.pdf"):
        if f.exists():
            f.unlink()
    for f in original.parent.glob(f"{original.stem}.cpdf_tmp.pdf"):
        if f.exists():
            f.unlink()
    for f in original.parent.glob(f"{original.stem}.gs_ebook_tmp.pdf"):
        if f.exists():
            f.unlink()

    flagged = chosen_size > TARGET_BYTES if chosen_size is not None else False
    return True, chosen_size, flagged  # type: ignore[arg-type]


# ---------- Stats structures ----------

class FolderStats:
    def __init__(self):
        self.total_size_before = 0
        self.total_size_after = 0
        self.file_count = 0
        self.above_limit_count = 0
        self.compressed_count = 0
        self.flagged_over_target = 0


def scan_and_compress(root: Path, dry_run: bool = False) -> None:
    year_stats: Dict[str, FolderStats] = defaultdict(FolderStats)
    total_big_files = 0
    total_compressed_files = 0
    flagged_files: List[Path] = []

    pdfs_to_process: List[Tuple[str, Path]] = []

    for year_dir in sorted(root.iterdir()):
        if not year_dir.is_dir():
            continue
        for path in year_dir.rglob("*.pdf"):
            year = is_nime_target_pdf(path)
            if year is None:
                continue
            pdfs_to_process.append((year, path))

    for year, path in pdfs_to_process:
        size = path.stat().st_size
        st = year_stats[year]
        st.file_count += 1
        st.total_size_before += size
        st.total_size_after += size

        if size > MAX_BYTES:
            st.above_limit_count += 1
            total_big_files += 1

    print(f"Found {len(pdfs_to_process)} candidate NIME PDFs.")
    print(f"Files above {human_size(MAX_BYTES)}: {total_big_files}")
    print()

    for year, path in pdfs_to_process:
        size_before = path.stat().st_size
        if size_before <= MAX_BYTES:
            continue

        st = year_stats[year]

        existing_backups = list(path.parent.glob(path.stem + "_uncompressed*.pdf"))
        if existing_backups:
            print(f"[SKIP] {path} (uncompressed backup already present; probably compressed earlier)")
            continue

        print(f"[COMPRESS] {path}")
        print(f"  Original size: {human_size(size_before)}")

        if dry_run:
            print("  Dry run: no changes made.")
            print()
            continue

        backup_uncompressed = choose_uncompressed_name(path)
        try:
            path.replace(backup_uncompressed)
        except OSError as e:
            print(f"  ERROR: Could not rename to backup ({e}); skipping.")
            continue

        success, size_after, flagged = compress_pdf_to_target(path, backup_uncompressed)

        if not success:
            print("  Compression failed. Original restored.")
            year_stats[year].total_size_after -= size_before
            year_stats[year].total_size_after += path.stat().st_size
            print()
            continue

        st.compressed_count += 1
        total_compressed_files += 1

        st.total_size_after -= size_before
        st.total_size_after += size_after

        if flagged:
            st.flagged_over_target += 1
            flagged_files.append(path)
            print(f"  WARNING: final size {human_size(size_after)} > target {human_size(TARGET_BYTES)}")
        else:
            print(f"  New size:      {human_size(size_after)}")

        delta = size_before - size_after
        print(f"  Saved:         {human_size(delta)}")
        print(f"  Backup (uncompressed/original): {backup_uncompressed.name}")
        print()

    print("\n=== Per-year statistics ===")
    for year in sorted(year_stats.keys()):
        st = year_stats[year]
        if st.file_count == 0:
            continue
        avg_before = st.total_size_before / st.file_count
        avg_after = st.total_size_after / st.file_count
        print(f"Year {year}:")
        print(f"  Files considered: {st.file_count}")
        print(f"  Above {human_size(MAX_BYTES)} (before): {st.above_limit_count}")
        print(f"  Compressed: {st.compressed_count}")
        print(f"  Still > {human_size(TARGET_BYTES)}: {st.flagged_over_target}")
        print(f"  Avg size before: {human_size(avg_before)}")
        print(f"  Avg size after:  {human_size(avg_after)}")
        print()

    print("=== Overall ===")
    total_files = sum(st.file_count for st in year_stats.values())
    total_before = sum(st.total_size_before for st in year_stats.values())
    total_after = sum(st.total_size_after for st in year_stats.values())
    total_flagged = sum(st.flagged_over_target for st in year_stats.values())
    print(f"Total files considered: {total_files}")
    print(f"Total > {human_size(MAX_BYTES)} (before): {total_big_files}")
    print(f"Total compressed: {total_compressed_files}")
    print(f"Total still > {human_size(TARGET_BYTES)}: {total_flagged}")
    if total_files > 0:
        print(f"Overall average before: {human_size(total_before / total_files)}")
        print(f"Overall average after:  {human_size(total_after / total_files)}")

    if flagged_files:
        print("\n=== Files still exceeding TARGET_BYTES ===")
        print(f"TARGET_BYTES = {TARGET_BYTES} ({human_size(TARGET_BYTES)})")
        for p in flagged_files:
            sz = p.stat().st_size
            print(f"  {p} -> {human_size(sz)} ({sz} bytes)")


# ---------- Undo logic ----------

def undo_compression(root: Path, dry_run: bool = False) -> None:
    restored_count = 0

    for pdf in root.rglob("*.pdf"):
        name = pdf.name
        if name.endswith("_uncompressed.pdf"):
            base_name = name[:-len("_uncompressed.pdf")] + ".pdf"
        else:
            continue

        original_path = pdf.parent / base_name

        if dry_run:
            print(f"[UNDO dry-run] Would restore {pdf} -> {original_path}")
        else:
            if original_path.exists():
                tmp_backup = original_path.with_suffix(".undo_backup.pdf")
                shutil.move(str(original_path), str(tmp_backup))
                try:
                    pdf.replace(original_path)
                finally:
                    if tmp_backup.exists():
                        tmp_backup.unlink()
            else:
                pdf.replace(original_path)

        restored_count += 1

    print(f"Restored uncompressed/original PDFs for {restored_count} files.")


# ---------- CLI ----------

def main():
    parser = argparse.ArgumentParser(
        description="Compress NIME PDFs to comfortably under Google Scholar's 5MB limit (decimal) using Ghostscript + cpdf fallback."
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
        help="Undo mode: restore *_uncompressed.pdf backups.",
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
