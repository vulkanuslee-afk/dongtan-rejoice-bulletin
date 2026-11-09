# -*- coding: utf-8 -*-
"""ko_krv.json (개역한글) → data/bible/<abbrev>.js 로 쪼개 저장.

사용법:  python -I tools/build_bible.py _bibleraw/ko_krv.json
책 하나당 파일 하나라, 본문을 볼 때 그 책만 내려받습니다.
"""
import io, json, os, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else '_bibleraw/ko_krv.json'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'bible')
os.makedirs(OUT, exist_ok=True)

books = json.load(io.open(SRC, encoding='utf-8-sig'))

# 한글 책 이름 → 흔히 쓰는 약칭들
ALIAS = {
    '창세기': ['창'], '출애굽기': ['출'], '레위기': ['레'], '민수기': ['민'], '신명기': ['신'],
    '여호수아': ['수'], '사사기': ['삿'], '룻기': ['룻'],
    '사무엘상': ['삼상'], '사무엘하': ['삼하'], '열왕기상': ['왕상'], '열왕기하': ['왕하'],
    '역대상': ['대상'], '역대하': ['대하'], '에스라': ['스'], '느헤미야': ['느'], '에스더': ['에'],
    '욥기': ['욥'], '시편': ['시'], '잠언': ['잠'], '전도서': ['전'], '아가': ['아'],
    '이사야': ['사'], '예레미야': ['렘'], '예레미야애가': ['애'], '에스겔': ['겔'], '다니엘': ['단'],
    '호세아': ['호'], '요엘': ['욜'], '아모스': ['암'], '오바댜': ['옵'], '요나': ['욘'],
    '미가': ['미'], '나훔': ['나'], '하박국': ['합'], '스바냐': ['습'], '학개': ['학'],
    '스가랴': ['슥'], '말라기': ['말'],
    '마태복음': ['마'], '마가복음': ['막'], '누가복음': ['눅'], '요한복음': ['요'],
    '사도행전': ['행'], '로마서': ['롬'], '고린도전서': ['고전'], '고린도후서': ['고후'],
    '갈라디아서': ['갈'], '에베소서': ['엡'], '빌립보서': ['빌'], '골로새서': ['골'],
    '데살로니가전서': ['살전'], '데살로니가후서': ['살후'],
    '디모데전서': ['딤전'], '디모데후서': ['딤후'], '디도서': ['딛'], '빌레몬서': ['몬'],
    '히브리서': ['히'], '야고보서': ['약'], '베드로전서': ['벧전'], '베드로후서': ['벧후'],
    '요한일서': ['요일'], '요한이서': ['요이'], '요한삼서': ['요삼'], '유다서': ['유'],
    '요한계시록': ['계', '계시록'],
}

index = {}
total = 0
for b in books:
    ab, name = b['abbrev'], b['name']
    payload = {'abbrev': ab, 'name': name, 'ch': b['chapters']}
    path = os.path.join(OUT, ab + '.js')
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write('window.BIBLE_PUT(' + json.dumps(payload, ensure_ascii=False) + ');\n')
    total += os.path.getsize(path)
    index[name] = ab
    for a in ALIAS.get(name, []):
        index[a] = ab

with io.open(os.path.join(OUT, '_index.js'), 'w', encoding='utf-8') as f:
    f.write('window.BIBLE_INDEX = ' + json.dumps(index, ensure_ascii=False) + ';\n')

print('books:', len(books), 'names+aliases:', len(index), 'total KB:', round(total / 1024))
print('sample: col ->', index.get('골로새서'), '| 살전 ->', index.get('살전'))
