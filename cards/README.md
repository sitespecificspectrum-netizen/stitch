# 소드코스트 캐릭터 카드 십자수 도안 (100 × 180칸)

종족 + 직업, 또는 몬스터 이름을 넣으면 카드 도안을 만들어 주는 생성기입니다.
모든 색은 `../dmc.js` 의 DMC 실 색만 씁니다.

```
python3 cards/make_card.py 티플링 바드
python3 cards/make_card.py half-orc paladin
python3 cards/make_card.py 아울베어
python3 cards/make_card.py elf wizard --hair 321 --skin 3064 --bg forest
python3 cards/make_card.py --list     # 쓸 수 있는 이름
python3 cards/make_card.py --all      # 전부 생성 + gallery_*.png
```

- 종족: human, elf, half-elf, dwarf, halfling, gnome, half-orc, tiefling, drow, dragonborn, goblin
- 직업: fighter, wizard, rogue, cleric, bard, ranger, paladin, barbarian, druid, monk, sorcerer, warlock
- 몬스터: owlbear, gelatinous cube, red dragon, mind flayer, skeleton, goblin
- 배경(`--bg`): forest, dungeon, city, coast, snow, mountain, arcane

결과는 `cards/out/` 에 저장됩니다.

- `<이름>.png` — 1칸 = 1픽셀 원본. 앱의 "새 작품 → 이미지 고르기"로 불러옵니다.
- `<이름>_x8.png`, `<이름>_colors.txt` — 이름을 지정해 한 장만 만들 때 함께 생성되는 미리보기와 DMC 번호별 땀 수.

`gallery_<직업>.png` 는 직업별로 모든 종족을 한 줄에 모은 미리보기입니다.

필요: Python 3, Pillow, numpy.
