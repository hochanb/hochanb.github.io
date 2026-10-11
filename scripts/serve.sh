#!/usr/bin/env bash
# 로컬 미리보기 서버: conda 'jekyll' 환경에서 jekyll serve (http://localhost:4000)
#   scripts/serve.sh               # 기본
#   scripts/serve.sh --port 4001   # jekyll serve 옵션을 그대로 넘길 수 있음
# 끄기: Ctrl+C
set -euo pipefail
cd "$(dirname "$0")/.."

ENV_NAME="${JEKYLL_CONDA_ENV:-jekyll}"

# 비대화형 셸에서도 conda activate가 되도록 conda 초기화
if ! command -v conda >/dev/null 2>&1; then
  for c in /opt/homebrew/Caskroom/miniconda/base /opt/homebrew/Caskroom/miniforge/base \
           "$HOME/miniconda3" "$HOME/miniforge3" "$HOME/anaconda3" /opt/miniconda3; do
    [ -x "$c/bin/conda" ] && export PATH="$c/bin:$PATH" && break
  done
fi
command -v conda >/dev/null 2>&1 || { echo "conda를 찾을 수 없습니다." >&2; exit 1; }
set +u   # conda activate 스크립트(컴파일러 등)가 정의 안 된 변수를 참조해서 잠시 해제
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$ENV_NAME" || { echo "conda 환경 '$ENV_NAME'이 없습니다. README의 설치 방법 참고." >&2; exit 1; }
set -u

export JEKYLL_NO_BUNDLER_REQUIRE=true   # Gemfile(github-pages) 대신 설치된 jekyll 사용
exec jekyll serve --livereload "$@"
