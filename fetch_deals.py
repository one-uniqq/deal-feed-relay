"""뽐뿌 핫딜 목록 → deals.json (GitHub Actions 릴레이).

사내망에서 외부 커뮤니티 접근이 제한되어, 퍼블릭 러너가 5분마다 피드를 파싱해
deals.json 으로 커밋한다. 소비자는 raw.githubusercontent.com 으로 읽는다.
표준 라이브러리만 사용.
"""

from __future__ import annotations

import base64
import json
import re
import sys
import urllib.request
from pathlib import Path

BOARD_URL = "https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu&page={page}"
VIEW_URL = "https://www.ppomppu.co.kr/zboard/view.php?id=ppomppu&no={no}"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

ROW_RE = re.compile(
    r'<a class="baseList-title[^"]*" href="view\.php\?id=ppomppu[^"]*?no=(\d+)"\s*>'
    r"(?:<span>)?(?:<em[^>]*>\[([^\]]+)\]</em>)?([^<]+)"
)
TOOLTIP_IMG_RE = re.compile(r"no=(\d+)[^>]*tooltip=P_img:(//[^> ]+)")
THUMB_IMG_RE = re.compile(r'no=(\d+)[^>]*>\s*<img src="(//cdn[^"]+_thumb[^"]+)"')
REDIRECT_RE = re.compile(r"s\.ppomppu\.co\.kr\?idno=[^\"&]+&target=([A-Za-z0-9+/=]+)")
ENDED_RE = re.compile(r"종료|품절|아쉬워요")
PRICE_RE = re.compile(r"\(([^()]*?(?:원|달러|\$|무료|무배)[^()]*)\)\s*$")

OUT = Path("deals.json")


def get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=20).read().decode("euc-kr", errors="ignore")


def resolve_product_url(no: int) -> str | None:
    try:
        html = get(VIEW_URL.format(no=no))
        m = REDIRECT_RE.search(html)
        if m:
            url = base64.b64decode(m.group(1) + "==").decode("utf-8", errors="ignore")
            if url.startswith("http"):
                return url
    except Exception as e:  # noqa: BLE001
        print(f"resolve failed no={no}: {e}", file=sys.stderr)
    return None


def main() -> None:
    prev: dict[str, str | None] = {}
    if OUT.exists():
        for d in json.loads(OUT.read_text(encoding="utf-8"))["deals"]:
            prev[str(d["no"])] = d.get("product_url")

    deals: list[dict] = []
    for page in (1, 2):
        html = get(BOARD_URL.format(page=page))
        thumbs: dict[int, str] = {}
        for no, url in THUMB_IMG_RE.findall(html):
            thumbs.setdefault(int(no), "https:" + url)
        for no, url in TOOLTIP_IMG_RE.findall(html):
            thumbs[int(no)] = "https:" + url
        for no, shop, title in ROW_RE.findall(html):
            title = title.strip()
            if not shop or ENDED_RE.search(title):
                continue
            m = PRICE_RE.search(title)
            deals.append({
                "no": int(no),
                "shop": shop,
                "title": PRICE_RE.sub("", title).strip(),
                "price": m.group(1) if m else "",
                "post_url": VIEW_URL.format(no=no),
                "thumb_url": thumbs.get(int(no), ""),
                "product_url": prev.get(no),
            })

    # 신규 딜만 상품 URL 해석 (기존 값은 carry-over)
    resolved = 0
    for d in deals:
        if d["product_url"] is None and str(d["no"]) not in prev:
            d["product_url"] = resolve_product_url(d["no"])
            resolved += 1
            if resolved >= 20:  # 러너 시간 보호
                break

    from datetime import datetime, timezone
    OUT.write_text(
        json.dumps(
            {"updated_at": datetime.now(timezone.utc).isoformat(), "deals": deals},
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    print(f"deals={len(deals)} newly_resolved={resolved}")


if __name__ == "__main__":
    main()
