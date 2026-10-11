#!/usr/bin/env bash
# CV PDF 빌드: cv/cv.yml -> assets/cv.pdf (프로젝트 .venv 사용, 없으면 자동 생성)
#   scripts/build_cv.sh                     # 기본
#   scripts/build_cv.sh -o my.pdf --html    # build_cv.py 옵션을 그대로 넘길 수 있음
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -x .venv/bin/python ]; then
  echo ".venv가 없어서 새로 만듭니다..."
  python3 -m venv .venv
fi
# requirements가 바뀌었을 수 있으니 매번 확인 (이미 설치돼 있으면 금방 끝남)
.venv/bin/pip install -q -r cv/requirements.txt --disable-pip-version-check

exec .venv/bin/python cv/build_cv.py "$@"
