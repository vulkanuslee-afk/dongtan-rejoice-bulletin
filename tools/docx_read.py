# -*- coding: utf-8 -*-
"""워드 파일(.docx)에서 글자만 뽑아냅니다. 추가 설치 없이 돌아갑니다.

  python -I tools/docx_read.py 주보.docx           화면에 출력
  python -I tools/docx_read.py 주보.docx out.txt   파일로 저장

표 안의 글자도 같이 나옵니다. (.doc 옛날 형식은 안 되니 워드에서
'다른 이름으로 저장 → .docx' 로 한 번 바꿔 주세요)
"""
import io, os, sys, zipfile
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def docx_lines(path):
    """문단과 표 칸을 줄 단위로 돌려줍니다."""
    if not os.path.exists(path):
        raise SystemExit('파일이 없습니다: %s' % path)
    if path.lower().endswith('.doc'):
        raise SystemExit('.doc 는 못 읽습니다. 워드에서 .docx 로 저장한 뒤 다시 해 주세요.')
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read('word/document.xml')
    except zipfile.BadZipFile:
        raise SystemExit('워드 파일이 아니거나 깨졌습니다: %s' % path)

    root = ET.fromstring(xml)
    lines = []
    for p in root.iter(W + 'p'):
        buf = []
        for node in p.iter():
            tag = node.tag
            if tag == W + 't':
                buf.append(node.text or '')
            elif tag in (W + 'tab',):
                buf.append('\t')
            elif tag in (W + 'br', W + 'cr'):
                buf.append('\n')
        text = ''.join(buf)
        for piece in text.split('\n'):
            piece = piece.replace('\t', ' ').strip()
            piece = ' '.join(piece.split())
            if piece:
                lines.append(piece)
    return lines


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    lines = docx_lines(sys.argv[1])
    out = '\n'.join(lines)
    if len(sys.argv) > 2:
        with io.open(sys.argv[2], 'w', encoding='utf-8') as f:
            f.write(out + '\n')
        print('%d 줄 저장: %s' % (len(lines), sys.argv[2]))
    else:
        sys.stdout.reconfigure(encoding='utf-8')
        print(out)
