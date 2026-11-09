# -*- coding: utf-8 -*-
"""주보 워드 파일(.docx) → data/bulletins.js 에 이번 주 블록 추가.

  python -I tools/docx_to_bulletin.py 주보.docx          바로 추가
  python -I tools/docx_to_bulletin.py 주보.docx --dry    추가 안 하고 결과만 보기

워드 양식이 주마다 조금씩 달라도 돌아가도록 '찾을 수 있는 건 찾고,
못 찾은 건 TODO 로 남기는' 방식입니다. 끝나면 무엇을 못 찾았는지 알려주니
data/bulletins.js 에서 그 부분만 고치면 됩니다.

고치기 전 data/bulletins.backup.js 로 백업을 남깁니다.
"""
import io, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from docx_read import docx_lines  # noqa: E402

BULLETINS = os.path.join(ROOT, 'data', 'bulletins.js')
BIBLE_INDEX = os.path.join(ROOT, 'data', 'bible', '_index.js')

TODO = 'TODO: 확인'

# 이 교회 주보에 나오는 예배 순서 이름들 (없는 건 그냥 안 잡힙니다)
PARTS = [
    '묵상의 시간', '묵도', '공동체 인사', '예배의 부름', '찬양', '찬송', '사도신경',
    '공동기도문', '대표기도', '기도', '성경봉독', '말씀 나눔', '말씀', '설교',
    '침묵의 기도', '응답찬양', '봉헌', '봉헌기도', '헌금', '교회소식', '공동체 소식',
    '광고', '축복기도', '축도', '파송찬송', '주기도문',
]
PARTS = sorted(set(PARTS), key=len, reverse=True)

WHO = re.compile(r'(다\s*같\s*이|회\s*중|인\s*도\s*자?|찬\s*양\s*대|[가-힣]{2,4}\s*(?:목사|전도사|강도사|장로|권사|집사|사모|청년))')

# 챌린지 기본 4단계 (교회 고정 양식)
DEFAULT_STEPS = [
    {'k': '말씀', 'v': '성경 한 구절 천천히 읽어보기'},
    {'k': '묵상', 'v': '질문 1개 & 한 문장 답하기'},
    {'k': '기도', 'v': '짧은 한 문장이라도 기도하기'},
    {'k': '실천', 'v': '이번 주 실천 과제 하루 1가지'},
]
DEFAULT_MEMO = '설교에서 마음에 남는 표현을 적고, 하나님이 주시는 메시지를 듣고, 실천할 한 가지를 정해 보세요.'


def bible_names():
    try:
        s = io.open(BIBLE_INDEX, encoding='utf-8').read()
        s = s.strip()
        s = s[s.index('{'):s.rindex('}') + 1]
        return sorted(json.loads(s).keys(), key=len, reverse=True)
    except Exception:
        return []


def find_ref(text, names):
    """'골로새서 3:15-17' 같은 장절 표기를 찾습니다."""
    if not names:
        return None
    pat = re.compile(
        '(' + '|'.join(re.escape(n) for n in names) + r')\s*(\d+)\s*(?::|장|편)\s*(\d+)'
        r'\s*절?(?:\s*[-~–]\s*(\d+)\s*절?)?')
    m = pat.search(text)
    if not m:
        return None
    ref = '%s %s:%s' % (m.group(1), m.group(2), m.group(3))
    if m.group(4):
        ref += '-' + m.group(4)
    return ref


def quoted(text):
    for pat in (r'[“"]([^”"]{2,40})[”"]', r'[‘\']([^’\']{2,40})[’\']'):
        m = re.search(pat, text)
        if m:
            return m.group(1).strip()
    return None


def parse(lines):
    joined = '\n'.join(lines)
    names = bible_names()
    out = {}

    # 날짜
    m = re.search(r'(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일', joined)
    if not m:
        raise SystemExit('날짜를 못 찾았습니다. 워드에 "2026년 11월 15일" 형태가 있어야 합니다.')
    out['date'] = '%04d-%02d-%02d' % (int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # 호수
    m = re.search(r'(\d+)\s*호', joined)
    out['issue'] = (m.group(1) + '호') if m else ''

    # 절기 / 예배 이름
    out['label'] = ''
    for key in ('추수감사주일', '맥추감사주일', '종려주일', '부활주일', '성탄주일', '송구영신',
                '대림절', '사순절', '임직', '헌신예배', '주일예배'):
        if key in joined:
            out['label'] = key
            break

    # 설교 제목 · 본문 · 설교자
    title = None
    for ln in lines:
        if ('말씀' in ln or '설교' in ln) and quoted(ln):
            title = quoted(ln)
            break
    if not title:
        title = quoted(joined)
    out['theme'] = title or TODO

    ref = find_ref(joined, names)

    # ---- 예배 순서 ----
    # '예배 순서' 제목부터 다음 큰 제목 전까지만 읽습니다.
    HEADS = ('일상예배챌린지', '비전선언문', '공동체소식', '교회소식', '예배안내', '교회부설기관')
    flat = [ln.replace(' ', '') for ln in lines]
    start = None
    for i, f in enumerate(flat):
        if f == '예배순서':
            start = i + 1
            break
    end = len(lines)
    if start is not None:
        for j in range(start, len(flat)):
            if flat[j] in HEADS:
                end = j
                break
    scan = lines[start:end] if start is not None else lines

    order = []
    cur = None
    for ln in scan:
        f = ln.replace(' ', '')
        hit = None
        for p in PARTS:
            if f.startswith(p.replace(' ', '')):
                hit = p
                break
        if hit:
            rest = f[len(hit.replace(' ', '')):].strip(' :·-')
            cur = {'part': hit, 'by': ''}
            if rest:
                w = WHO.search(rest)
                if w and w.group(1).replace(' ', '') == rest.replace(' ', ''):
                    cur['by'] = rest
                else:
                    cur['note'] = rest
            order.append(cur)
            continue
        if cur is not None:
            if WHO.fullmatch(ln.strip()):
                cur['by'] = ln.strip()
            elif len(ln) <= 60 and not cur.get('note'):
                cur['note'] = ln.strip()
    for it in order:
        r = find_ref(it.get('note', ''), names)
        if r:
            it['bible'] = r
            # 본문 뒤에 붙은 설교 제목에서 따옴표만 떼어 냅니다
            q = quoted(it['note'])
            it['note'] = q if q else it['note']
    out['order'] = order

    # 설교자 = 말씀 나눔 줄의 담당
    preacher = ''
    for it in order:
        if it['part'] in ('말씀 나눔', '말씀', '설교') and '목사' in (it.get('by') or ''):
            preacher = it['by']
            break
    # 설교 본문 = 말씀 나눔 줄의 장절이 있으면 그것 우선
    for it in order:
        if it['part'] in ('말씀 나눔', '말씀', '설교') and it.get('bible'):
            ref = it['bible']
            break

    out['sermon'] = {
        'title': title or TODO,
        'text': ref or TODO,
        'preacher': preacher or TODO,
        'youtube': '',
    }

    # ---- 공동체 소식 ----
    # '공동체 소식' 제목이 있으면 그 뒤의 * 줄만 가져옵니다 (챌린지 쪽 * 와 안 섞이게)
    nstart = 0
    for i in range(len(flat) - 1, -1, -1):
        if flat[i] in ('공동체소식', '교회소식'):
            nstart = i + 1
            break
    notices = []
    for ln in lines[nstart:]:
        s = ln.strip()
        if s[:1] in ('*', '※', '·', '•') and len(s) > 6:
            notices.append({'body': s.lstrip('*※·• ').strip()})
    out['notices'] = notices

    # ---- 지난주 헌금 명단 ----
    # '지난주 헌금 명단' 다음 줄들에서 한글 이름만 골라냅니다.
    offering = []
    ostart = None
    for i, f in enumerate(flat):
        if '헌금명단' in f or '지난주헌금' in f:
            ostart = i + 1
            break
    if ostart is not None:
        for ln in lines[ostart:ostart + 6]:
            if '온라인' in ln or re.search(r'\d{3}[- ]\d{3,4}', ln) or '예금주' in ln:
                break
            for tok in re.split(r'[\s,·]+', ln.strip()):
                if re.fullmatch(r'[가-힣]{2,4}', tok):
                    offering.append(tok)
    out['offeringNames'] = offering

    # ---- 일정 (소식 중 날짜가 들어간 것) ----
    cal = []
    datepat = re.compile(r'(\d{1,2})\s*월\s*(\d{1,2})\s*일\s*(?:\(\s*(주일|[월화수목금토일])\s*\))?')
    for n in notices:
        m = datepat.search(n['body'])
        if not m:
            continue
        when = '%s/%s' % (m.group(1), m.group(2))
        if m.group(3):
            when += '(%s)' % m.group(3)
        what = n['body'][m.end():].strip(' ·-~')
        if len(what) < 4:
            what = n['body']
        cal.append({'when': when, 'what': what[:34]})
    out['calendar'] = cal

    # 일상예배 챌린지
    question = ''
    task = ''
    cend = nstart if nstart else len(lines)   # 공동체 소식 제목 앞까지가 챌린지 영역
    for ln in lines[:cend]:
        s = ln.strip().lstrip('*※·• ').strip()
        if s.rstrip().endswith('?') and len(s) > 20 and not question:
            question = s
        if re.search(r'(보십시오|해 보세요|적어|실천|나누어)', s) and len(s) > 18 \
           and not s.endswith('?') and not task:
            task = s
    out['challenge'] = {
        'verseRef': ref or TODO,
        'steps': DEFAULT_STEPS,
        'question': question or TODO,
        'task': task or TODO,
        'note': '',
    }
    out['memoPrompt'] = DEFAULT_MEMO
    return out


def js(value, indent):
    """사람이 읽기 좋은 JS 리터럴로."""
    pad = ' ' * indent
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if value is None:
        return 'null'
    if isinstance(value, list):
        if not value:
            return '[]'
        inner = (',\n' + pad + '  ').join(js(v, indent + 2) for v in value)
        return '[\n' + pad + '  ' + inner + '\n' + pad + ']'
    if isinstance(value, dict):
        items = [json.dumps(k, ensure_ascii=False).strip('"') + ': ' + js(v, indent + 2)
                 for k, v in value.items()]
        if sum(len(i) for i in items) < 70 and not any('\n' in i for i in items):
            return '{ ' + ', '.join(items) + ' }'
        return '{\n' + pad + '  ' + (',\n' + pad + '  ').join(items) + '\n' + pad + '}'
    return json.dumps(value, ensure_ascii=False)


def block(data):
    keys = ['date', 'issue', 'label', 'theme', 'sermon', 'order',
            'memoPrompt', 'challenge', 'notices', 'calendar', 'offeringNames']
    lines = ['    {']
    for k in keys:
        lines.append('      %s: %s,' % (k, js(data[k], 6)))
    lines.append('      picks: null')
    lines.append('    },')
    return '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    src = sys.argv[1]
    dry = '--dry' in sys.argv

    data = parse(docx_lines(src))
    text = block(data)

    sys.stdout.reconfigure(encoding='utf-8')
    print('=' * 56)
    print('날짜   :', data['date'], data['issue'], data['label'])
    print('설교   :', data['sermon']['title'])
    print('본문   :', data['sermon']['text'])
    print('예배순서:', len(data['order']), '줄')
    print('소식   :', len(data['notices']), '건')
    print('일정   :', len(data['calendar']), '건')
    print('헌금명단:', len(data['offeringNames']), '명',
          ('— 이름은 꼭 눈으로 확인해 주세요' if data['offeringNames'] else ''))

    missing = [k for k in ('theme',) if data[k] == TODO]
    for k, v in data['sermon'].items():
        if v == TODO:
            missing.append('sermon.' + k)
    for k, v in data['challenge'].items():
        if v == TODO:
            missing.append('challenge.' + k)
    if missing:
        print('-' * 56)
        print('못 찾은 항목 (data/bulletins.js 에서 "%s" 를 찾아 고치세요):' % TODO)
        for m in missing:
            print('  -', m)
    print('=' * 56)

    if dry:
        print(text)
        return

    cur = io.open(BULLETINS, encoding='utf-8').read()
    if ('"%s"' % data['date']) in cur or ("'%s'" % data['date']) in cur:
        print('!! %s 주보가 이미 들어 있습니다. 중복이라 넣지 않았습니다.' % data['date'])
        print('   다시 넣으려면 data/bulletins.js 에서 그 블록을 지우고 실행하세요.')
        return

    anchor = re.search(r'\n(\s*)list:\s*\[\s*\n', cur)
    if not anchor:
        raise SystemExit('data/bulletins.js 에서 list: [ 를 못 찾았습니다.')

    shutil.copyfile(BULLETINS, os.path.join(ROOT, 'data', 'bulletins.backup.js'))
    pos = anchor.end()
    new = cur[:pos] + text + '\n\n' + cur[pos:]
    io.open(BULLETINS, 'w', encoding='utf-8').write(new)
    print('data/bulletins.js 맨 위에 넣었습니다. (백업: data/bulletins.backup.js)')


if __name__ == '__main__':
    main()
