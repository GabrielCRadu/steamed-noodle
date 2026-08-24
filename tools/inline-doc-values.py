#!/usr/bin/env python3
"""Replace Google-Docs LaTeX image placeholders in the architecture doc with plain text.

The doc was exported from Google Docs, which rendered every numeric/mathematical
value as a base64 PNG. That left the markdown unreadable as text: "tactat pana la
![][image5]" instead of "tactat pana la 2.84 GHz". Values were recovered by
decoding each PNG and reading it; the mapping below is the result.

Usage:  python tools/inline-doc-values.py "Gaming Mainline OnePlus 8.md"
"""
import re
import sys

VALUES = {
    "image1": "I²C",              "image2": "1024 KB",
    "image3": "8 W",              "image4": "11 W",
    "image5": "2.84 GHz",         "image6": "512 KB L2 cache",
    "image7": "2.42 GHz",         "image8": "256 KB L2 cache",
    "image9": "1.80 GHz",         "image10": "128 KB L2 cache",
    "image11": "587 MHz",         "image12": "670 MHz",
    "image13": "70-75 °C",        "image14": "1.40 GHz",
    "image15": "305 MHz",         "image16": "10-12 W",
    "image17": "45-52 °C",        "image18": "587-670 MHz",
    "image19": "< 2 ms",          "image20": "75-90 FPS",
    "image21": "60 FPS",          "image22": "≈ 5.5 W",
    "image23": "50-60 FPS",       "image24": "42 FPS",
    "image25": "≈ 6.8 W",         "image26": "→",
    "image27": "40-52 FPS",       "image28": "30 FPS",
    "image29": "≈ 8.5 W",         "image30": "32-45 FPS",
    "image31": "24 FPS",          "image32": "≈ 9.2 W",
}


def main(path):
    text = open(path, encoding="utf-8").read()

    missing = sorted(set(re.findall(r"!\[\]\[(image\d+)\]", text)) - VALUES.keys())
    if missing:
        sys.exit(f"no recovered value for: {', '.join(missing)}")

    subbed = 0
    for name, value in VALUES.items():
        text, n = re.subn(rf"!\[\]\[{name}\]", value, text)
        subbed += n

    # Drop the now-unreferenced base64 definitions at the foot of the file.
    text, dropped = re.subn(
        r"^\[image\d+\]: <data:image/png;base64,[A-Za-z0-9+/=]+>\n?", "", text, flags=re.M
    )
    text = re.sub(r"\n{3,}", "\n\n", text)

    open(path, "w", encoding="utf-8", newline="\n").write(text)
    print(f"inlined {subbed} values, dropped {dropped} base64 definitions")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "Gaming Mainline OnePlus 8.md")
