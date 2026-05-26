#!/usr/bin/env python3
"""Merge single-column CSV files from one folder into a single output CSV."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Merge single-column CSV files from a folder into one output CSV file. "
            "Files are merged in alphabetical order."
        )
    )
    parser.add_argument("input_dir", type=Path, help="Folder containing input CSV files")
    parser.add_argument("output_file", type=Path, help="Path to the merged output CSV file")
    parser.add_argument(
        "--pattern",
        default="*.csv",
        help="Glob pattern used to select input files (default: *.csv)",
    )
    return parser.parse_args()


def read_rows(file_path: Path) -> list[str]:
    with file_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        rows = [row for row in csv.reader(csv_file) if row]

    for index, row in enumerate(rows, start=1):
        if len(row) != 1:
            raise ValueError(f"{file_path} row {index} has {len(row)} columns; expected 1")

    return [row[0] for row in rows]


def detect_has_header(all_rows: list[list[str]]) -> bool:
    non_empty = [rows for rows in all_rows if rows]
    if not non_empty:
        return False

    first_values = {rows[0] for rows in non_empty}
    return len(first_values) == 1 and any(len(rows) > 1 for rows in non_empty)


def merge_files(input_files: Iterable[Path]) -> tuple[str | None, list[str]]:
    files = list(input_files)
    all_rows = [read_rows(file_path) for file_path in files]
    has_header = detect_has_header(all_rows)
    merged_values: list[str] = []
    header: str | None = None

    for file_path, rows in zip(files, all_rows):
        if has_header and rows:
            if header is None:
                header = rows[0]
            elif rows[0] != header:
                raise ValueError(
                    f"Header mismatch in {file_path}: expected '{header}', found '{rows[0]}'"
                )
            merged_values.extend(rows[1:])
        else:
            merged_values.extend(rows)

    return header, merged_values


def write_output(output_file: Path, header: str | None, values: list[str]) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        if header is not None:
            writer.writerow([header])
        writer.writerows([[value] for value in values])


def main() -> None:
    args = parse_args()

    if not args.input_dir.exists() or not args.input_dir.is_dir():
        raise SystemExit(f"Input directory not found: {args.input_dir}")

    input_files = sorted(path for path in args.input_dir.glob(args.pattern) if path.is_file())

    if not input_files:
        raise SystemExit(
            f"No files matched pattern '{args.pattern}' in directory {args.input_dir}"
        )

    output_path = args.output_file.resolve()
    files_to_merge = [path for path in input_files if path.resolve() != output_path]

    if not files_to_merge:
        raise SystemExit("No input files to merge after excluding output file")

    header, merged_values = merge_files(files_to_merge)
    write_output(args.output_file, header, merged_values)


if __name__ == "__main__":
    main()
