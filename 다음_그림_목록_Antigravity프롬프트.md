# 🎨 다음에 만들 그림 목록 (Antigravity용) — 2026-10-14

앱은 **그림이 없어도 아이콘·하위 그림으로 대신 나오게** 되어 있어서, 아래 그림을 넣으면 **자동으로 바뀌어요.**
(일부만 넣어도 OK. 다 만들면 클로드에게 "그림 넣었어" → 용량 줄이고 확인·배포)

## Antigravity에게 붙여넣을 지시
```
아래 목록대로 그림을 만들어 표의 경로·파일명 그대로 PNG로 저장해줘.
1. 모든 그림은 배경을 지운 투명 PNG.
2. 그림체는 sinli2655/assets/avatars/knight_m.png, assets/gear/ 그림과 똑같이(치비, 굵은 외곽선, 부드러운 음영) 맞춰줘.
3. 캐릭터(아바타)는 기존 같은 직업·성별 그림(예: knight_m.png)과 얼굴·머리색·체형이 같은 아이로 보이게, 정면을 보고 서 있는 전신, 세로 3:4.
4. index.html, list.json 은 절대 고치지 말고 git commit/push 도 하지 마. (등록·배포는 클로드가 해)
```

---

## 1순위 — 펫 7마리 (대결 화면에 바로 보임)
지금은 이 펫들이 이모지로 나와요. 저장 위치: `sinli2655/assets/items/pet/` · 정사각형 512x512 투명

| 해금 | 펫 | 파일명 | 프롬프트 |
|---|---|---|---|
| Lv26 | 달토끼 | `rabbit.png` | cute chibi fantasy pet, a small white moon rabbit with a tiny crescent moon mark, sitting, soft cel shading, thick clean outline, transparent background, no text |
| Lv34 | 얼음 펭귄 | `penguin.png` | cute chibi fantasy pet, a baby penguin with icy blue crystal accents and a tiny scarf, soft cel shading, thick clean outline, transparent background, no text |
| Lv42 | 불사조 | `phoenix.png` | cute chibi fantasy pet, a small baby phoenix bird with orange and red flame feathers, soft cel shading, thick clean outline, transparent background, no text |
| Lv55 | 그리핀 | `griffin.png` | cute chibi fantasy pet, a small baby griffin with eagle head and lion body and tiny wings, soft cel shading, thick clean outline, transparent background, no text |
| Lv68 | 페가수스 | `pegasus.png` | cute chibi fantasy pet, a small white baby pegasus horse with feathered wings and pastel mane, soft cel shading, thick clean outline, transparent background, no text |
| Lv82 | 꼬마 크라켄 | `kraken.png` | cute chibi fantasy pet, a small friendly purple baby kraken octopus, soft cel shading, thick clean outline, transparent background, no text |
| Lv100 | 신룡 | `divine_dragon.png` | cute chibi fantasy pet, a small golden-white celestial baby dragon with glowing aura and clouds, soft cel shading, thick clean outline, transparent background, no text |

## 2순위 — 머리 장식 9개
지금은 이모지·간단한 도형으로 나와요. 저장 위치: `sinli2655/assets/items/head/` · 가로 3:2(예: 768x512) 투명, 캐릭터 머리 위에 얹는 모양(아래쪽이 머리에 닿게)

| 해금 | 장식 | 파일명 | 프롬프트 |
|---|---|---|---|
| Lv15 | 마법사 모자 | `magic_hat.png` | cute chibi fantasy head accessory, a purple wizard hat with stars, front view, made to sit on top of a head, soft cel shading, thick outline, transparent background, no text |
| Lv20 | 잎사귀 화관 | `leaf_circlet.png` | cute chibi fantasy head accessory, a green leaf circlet with small flowers, front view, sits on a head, soft cel shading, thick outline, transparent background |
| Lv26 | 수정 별핀 | `prism_star.png` | cute chibi fantasy hair pin, a shiny prism crystal star hairpin, front view, soft cel shading, thick outline, transparent background |
| Lv33 | 날개 머리띠 | `winged_band.png` | cute chibi fantasy headband with small white angel wings on both sides, front view, soft cel shading, thick outline, transparent background |
| Lv42 | 월계관 | `laurel_crown.png` | cute chibi golden laurel wreath crown, front view, sits on a head, soft cel shading, thick outline, transparent background |
| Lv55 | 불꽃 왕관 | `flame_crown.png` | cute chibi fantasy crown made of orange flames with a red gem, front view, soft cel shading, thick outline, transparent background |
| Lv68 | 은하 후광 | `galaxy_halo.png` | cute chibi glowing galaxy halo ring with stars, floating, front view, soft cel shading, thick outline, transparent background |
| Lv82 | 불사조 깃털 | `phoenix_feather.png` | cute chibi head accessory, a big red-orange phoenix feather hair ornament, front view, soft cel shading, thick outline, transparent background |
| Lv100 | 전설 왕관 | `legend_crown.png` | cute chibi legendary golden crown with rainbow gems and sparkles, front view, soft cel shading, thick outline, transparent background |

## 3순위 — 레벨이 오르면 바뀌는 캐릭터 48장 (가장 큰 변화, 가장 많음)
지금은 **기사 2단계**만 있고, 나머지 직업은 레벨이 올라도 기본 그림 그대로예요.
저장 위치: `sinli2655/assets/avatars/` · 세로 3:4(예: 600x800) 투명, 정면 전신

**나눠서 만들기 권장**: 먼저 **2·3단계(18장)** → 반응 보고 4~6단계(30장)

| 단계 | 바뀌는 느낌(옷·장비가 점점 화려해짐) |
|---|---|
| 2단계 | 기본 옷에 작은 장비가 붙은 견습 모습 |
| 3단계 | 제대로 된 직업 옷, 무기를 든 모습 |
| 4단계 | 망토·장식이 생긴 숙련자 |
| 5단계 | 빛나는 장식, 화려한 색 |
| 6단계 | 전설 등급, 은은한 빛·금장식 |

| 직업 | 남(m) 파일 | 여(f) 파일 | 모습 |
|---|---|---|---|
| 기사 knight | `knight_m_3`~`_6.png` (2단계 있음) | `knight_f_3`~`_6.png` (2단계 있음) | 갑옷·검·방패 |
| 마법사 mage | `mage_m_2`~`_6.png` | `mage_f_2`~`_6.png` | 로브·지팡이 |
| 성직자 priest | `priest_m_2`~`_6.png` | `priest_f_2`~`_6.png` | 흰 사제복·홀 |
| 궁수 archer | `archer_m_2`~`_6.png` | `archer_f_2`~`_6.png` | 가죽옷·활 |
| 음유시인 bard | `bard_m_2`~`_6.png` | `bard_f_2`~`_6.png` | 화려한 옷·류트 |

프롬프트 틀(직업·단계만 바꿔서):
`cute chibi fantasy RPG character, same child as the reference image <job>_<m|f>.png (same face, hair and body), full body front view standing, <job> outfit at tier <N> of 6 (<위 표의 느낌을 영어로>), soft cel shading, thick clean outline, transparent background, no text, portrait 3:4`

---
## (나중에) 옷이 몸에 입혀지는 모습
산 갑옷이 캐릭터 몸에 보이게 하려면 직업 5 × 남녀 2 × 옷 13 = 130장이 필요해요. 위 3순위가 끝난 뒤, 필요하면 방식을 다시 정해요.
