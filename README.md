# deal-feed-relay

사내망(egress 제한)에서 소비할 커뮤니티 핫딜/코스트코 데이터를 GitHub Actions가
5분 주기로 수집해 JSON으로 커밋하는 릴레이.

- `deals.json` — 뽐뿌 핫딜 (상품 원본 URL 해석 포함)
- `costco.json` — 코스트코 휴무일/주차공지/할인상품/인기랭킹 (출처: cocodalin.com)

소비: `https://raw.githubusercontent.com/one-uniqq/deal-feed-relay/main/{deals,costco}.json`
