# ===============================
# Generic WordCloud Generator
# Row-level unique frequency
# ===============================

import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Generate a WordCloud from a CSV column (row-level unique counting)"
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to input CSV file"
    )

    parser.add_argument(
        "--column",
        required=True,
        help="Column name containing values (comma-separated)"
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Path to output PNG file"
    )

    parser.add_argument(
        "--delimiter",
        default=",",
        help="Delimiter used in the column (default: ,)"
    )

    parser.add_argument(
        "--colormap",
        default="viridis",
        help="Matplotlib colormap (default: viridis)"
    )

    args = parser.parse_args()

    # -------- Load CSV --------
    try:
        df = pd.read_csv(args.input)
    except Exception as e:
        sys.exit(f"Error reading CSV: {e}")

    if args.column not in df.columns:
        sys.exit(f"Column '{args.column}' not found in CSV")

    # -------- Count (row-level unique) --------
    counter = Counter()

    for row in df[args.column].dropna():
        values = [
            v.strip()
            for v in str(row).split(args.delimiter)
            if v.strip()
        ]

        # Count each term only once per row
        counter.update(set(values))

    if not counter:
        sys.exit("No valid values found to generate wordcloud")

    # -------- Generate WordCloud --------
    wordcloud = WordCloud(
        width=900,
        height=450,
        background_color="white",
        colormap=args.colormap
    ).generate_from_frequencies(counter)

    # -------- Save --------
    wordcloud.to_file(args.output)

    # -------- Display --------
    plt.figure(figsize=(12, 6))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.show()

    print(f"✔ WordCloud saved at: {args.output}")


if __name__ == "__main__":
    main()
