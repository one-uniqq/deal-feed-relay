"""코코달인(cocodalin.com) API → costco.json (GitHub Actions 릴레이).

한국 코스트코 휴무일/주차 공지/카테고리 요약/카테고리별 할인상품/인기(하트) 랭킹.
표준 라이브러리만 사용. 데이터 출처: 코코달인 (www.cocodalin.com)
"""

from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://www.cocodalin.com/api/front"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
OUT = Path("costco.json")


def get_json(path: str):
    req = urllib.request.Request(
        f"{API}/{path}",
        headers={"User-Agent": UA, "Referer": "https://www.cocodalin.com/"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=20).read().decode("utf-8"))


def main() -> None:
    out: dict = {"updated_at": datetime.now(timezone.utc).isoformat(), "source": "cocodalin.com"}
    out["holiday"] = get_json("holiday")
    out["notice"] = get_json("notice")
    out["categories"] = get_json("saleSummary")
    out["best_like"] = get_json("bestLikeProducts")
    products: dict[str, list] = {}
    for cat in out["categories"]:
        cid = cat["category_id"]
        try:
            products[str(cid)] = get_json(f"productList/{cid}")
        except Exception as e:  # noqa: BLE001
            print(f"productList {cid} failed: {e}", file=sys.stderr)
    out["products"] = products
    total = sum(len(v) for v in products.values())
    OUT.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print(f"costco: categories={len(out['categories'])} products={total} best={len(out['best_like'])}")


if __name__ == "__main__":
    main()
