"""下载并整理 MARD 色表为 src/pindou/data/mard.csv。

数据源：https://github.com/maxcleme/beadcolors（raw 格式）。
运行：python scripts/fetch_palette.py
"""
import csv
import io
import pathlib
import urllib.request

SRC = "https://raw.githubusercontent.com/maxcleme/beadcolors/master/raw/mard.csv"
OUT = pathlib.Path(__file__).resolve().parents[1] / "src" / "pindou" / "data" / "mard.csv"


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    raw = urllib.request.urlopen(SRC, timeout=30).read().decode("utf-8")
    # 该 raw 文件没有表头，列依次为：code,name,r,g,b,brand
    rows = list(csv.reader(io.StringIO(raw)))
    seen = set()
    out_rows = []
    for r in rows:
        if not r:
            continue
        code = r[0].strip()
        if not code or code in seen:
            continue
        seen.add(code)
        out_rows.append({
            "reference_code": code,
            "name": r[1].strip(),
            "rgb_r": int(r[2]),
            "rgb_g": int(r[3]),
            "rgb_b": int(r[4]),
            "symbol": "",
        })
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(
            fh, fieldnames=["reference_code", "name", "rgb_r", "rgb_g", "rgb_b", "symbol"]
        )
        w.writeheader()
        w.writerows(out_rows)
    print(f"wrote {len(out_rows)} colors -> {OUT}")


if __name__ == "__main__":
    main()
