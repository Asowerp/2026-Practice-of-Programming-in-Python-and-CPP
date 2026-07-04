from __future__ import annotations

import argparse
from pathlib import Path

from engine.warriors4_runner import solve_warriors4_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Warriors4 reference simulator on OJ-style input.")
    parser.add_argument("input", help="Path to Warriors4 input file, for example warriors4_data/Warcraft.in")
    parser.add_argument("-o", "--output", help="Optional output file path. Prints to stdout when omitted.")
    parser.add_argument("--compare", help="Optional expected output file path for line-by-line comparison.")
    args = parser.parse_args()

    actual = solve_warriors4_file(args.input)
    if args.output:
        Path(args.output).write_text(actual, encoding="utf-8", newline="\n")
    elif not args.compare:
        print(actual, end="")

    if args.compare:
        expected = Path(args.compare).read_text(encoding="utf-8").replace("\r\n", "\n")
        actual_normalized = actual.replace("\r\n", "\n")
        if actual_normalized == expected:
            print("MATCH")
            return
        actual_lines = actual_normalized.splitlines()
        expected_lines = expected.splitlines()
        for index in range(1, max(len(actual_lines), len(expected_lines)) + 1):
            actual_line = actual_lines[index - 1] if index <= len(actual_lines) else "<missing>"
            expected_line = expected_lines[index - 1] if index <= len(expected_lines) else "<missing>"
            if actual_line != expected_line:
                print(f"DIFF at line {index}")
                print(f"actual  : {actual_line}")
                print(f"expected: {expected_line}")
                break


if __name__ == "__main__":
    main()
