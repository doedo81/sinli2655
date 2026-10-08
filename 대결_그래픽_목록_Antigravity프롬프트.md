# 🏟️ 대결 그래픽 목록 (Antigravity용)

지금 대결 배경은 클로드가 코드로 그린 단순한 실루엣이라, 장비 그림(음영 있는 일러스트)과 그림체가 안 맞아요.
아래 그림을 만들어 넣으면 **자동으로 그림으로 바뀌어요.** (앱은 이미 준비 완료 — `assets/battle/list.json`에 등록되면 적용)

## Antigravity에게 붙여넣을 지시
```
아래 목록대로 그림을 만들어 sinli2655/assets/battle/ 폴더에 파일명 그대로 PNG로 저장해줘.
1. 배경 4장은 가로 1536x1024(3:2), 배경 있음(투명 아님).
2. 효과 8장은 정사각형 512x512, 배경을 지워서 투명 PNG.
3. 장비 그림(assets/gear)과 같은 그림체(외곽선 굵기·색감·귀여운 정도)로 맞춰줘.
4. index.html 은 절대 고치지 말고, git commit/push 도 하지 마. list.json도 건드리지 마. (등록·배포는 클로드가 해)
```

## 1단계 — 배경 4장 (가장 효과 큼)
**구도 규칙(중요)**: 화면 **아래 45%는 캐릭터가 설 평평한 바닥**이고, 그 바닥은 **원근감 있는 바둑판(체크무늬) 타일 전투장**으로 그려 주세요. 지평선은 위에서 55% 높이. 가운데는 비워 두기(캐릭터 2명이 좌우에 섬). 위쪽 양 끝 15%는 이름·체력 칸이 덮으니 중요한 것 두지 않기.

| 파일명 | 장면 | 프롬프트 |
|---|---|---|
| `bg_forest.png` | 🌳 숲 | cute chibi fantasy game battle stage background for a children's classroom RPG, same art style as soft cel-shaded chibi item icons, bright friendly colors, thick clean outlines, painterly but simple, no characters, no animals, no text, no UI, a sunny forest clearing with rounded green hills and cute pine trees in the distance, blue sky with soft clouds. Lower 45% of the image is a flat open battle arena floor made of perspective checkerboard tiles (two alternating tones that fit the scene), horizon at 55% height, center left empty for two characters, wide 3:2 |
| `bg_castle.png` | 🏰 성 | cute chibi fantasy game battle stage background for a children's classroom RPG, same art style as soft cel-shaded chibi item icons, bright friendly colors, thick clean outlines, painterly but simple, no characters, no animals, no text, no UI, in front of a small fairytale castle with towers and a red flag at warm sunset, orange-pink sky. Lower 45% of the image is a flat open battle arena floor made of perspective checkerboard tiles (two alternating tones that fit the scene), horizon at 55% height, center left empty for two characters, wide 3:2 |
| `bg_desert.png` | 🏜️ 사막 | cute chibi fantasy game battle stage background for a children's classroom RPG, same art style as soft cel-shaded chibi item icons, bright friendly colors, thick clean outlines, painterly but simple, no characters, no animals, no text, no UI, a bright desert with soft sand dunes, a small pyramid and a cactus far away, clear blue sky. Lower 45% of the image is a flat open battle arena floor made of perspective checkerboard tiles (two alternating tones that fit the scene), horizon at 55% height, center left empty for two characters, wide 3:2 |
| `bg_night.png` | 🌙 밤 | cute chibi fantasy game battle stage background for a children's classroom RPG, same art style as soft cel-shaded chibi item icons, bright friendly colors, thick clean outlines, painterly but simple, no characters, no animals, no text, no UI, a calm night valley with a big moon, twinkling stars and dark blue mountains. Lower 45% of the image is a flat open battle arena floor made of perspective checkerboard tiles (two alternating tones that fit the scene), horizon at 55% height, center left empty for two characters, wide 3:2 |

## 2단계 — 기술 효과 8장 (배경 다음에)

| 파일명 | 효과 | 프롬프트 |
|---|---|---|
| `fx_slash.png` | ⚔️ 베기 궤적 | cute chibi fantasy game skill effect sprite, a bright white curved sword slash arc, soft cel shading, bright colors, single effect centered, transparent background, no characters, no text, square 1:1 |
| `fx_fire.png` | 🔥 불꽃 | cute chibi fantasy game skill effect sprite, a burst of orange and yellow fire flames, soft cel shading, bright colors, single effect centered, transparent background, no characters, no text, square 1:1 |
| `fx_ice.png` | ❄️ 얼음 | cute chibi fantasy game skill effect sprite, a burst of light blue ice crystals and snowflakes, soft cel shading, bright colors, single effect centered, transparent background, no characters, no text, square 1:1 |
| `fx_thunder.png` | ⚡ 번개 | cute chibi fantasy game skill effect sprite, a yellow lightning bolt strike with sparks, soft cel shading, bright colors, single effect centered, transparent background, no characters, no text, square 1:1 |
| `fx_holy.png` | ✨ 빛 | cute chibi fantasy game skill effect sprite, a radiant golden light burst with sparkles, soft cel shading, bright colors, single effect centered, transparent background, no characters, no text, square 1:1 |
| `fx_heal.png` | 💚 회복 | cute chibi fantasy game skill effect sprite, soft green healing sparkles and plus signs rising, soft cel shading, bright colors, single effect centered, transparent background, no characters, no text, square 1:1 |
| `fx_shield.png` | 🛡️ 보호막 | cute chibi fantasy game skill effect sprite, a round translucent light blue magic shield bubble, soft cel shading, bright colors, single effect centered, transparent background, no characters, no text, square 1:1 |
| `fx_crit.png` | 💫 치명타 | cute chibi fantasy game skill effect sprite, a big yellow star impact burst, soft cel shading, bright colors, single effect centered, transparent background, no characters, no text, square 1:1 |

## 3단계 — (나중에) 옷이 몸에 입혀지는 모습
갑옷·옷을 사면 캐릭터 몸이 바뀌게 하려면, 같은 자세의 캐릭터를 옷마다 다시 그려야 해서 그림이 아주 많이 필요해요(직업 5 × 남녀 2 × 옷 13). 1·2단계가 끝난 뒤에 필요하면 따로 정리할게요.

---
다 만들면 클로드에게 **"대결 그림 넣었어"** 라고 말하면, 크기·용량을 줄이고 등록해서 배포해요.