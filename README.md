# Researcher Homepage (Jekyll + GitHub Pages)

플러그인/테마 의존성 없는 가벼운 연구자 프로필 템플릿. GitHub Pages가 그대로 빌드합니다.

## 수정할 파일

| 파일 | 내용 |
|---|---|
| `_config.yml` | 이름, 소속, 이메일, 링크(Scholar/GitHub/CV…), 상단 메뉴 |
| `_includes/bio.md` | 자기소개 (마크다운) |
| `_data/news.yml` | 뉴스 (최신순, date는 따옴표로) |
| `_data/publications.yml` | 논문 (썸네일, 저자, venue, 링크, award) |
| `_data/experience.yml` | 학력/경력 (파일을 지우면 섹션도 사라짐) |
| `_posts/` | 블로그 글 (`YYYY-MM-DD-title.md`). 목록 썸네일은 front matter `thumbnail:` > 본문 첫 이미지 > 첫 영상 포스터 순, 요약은 `description:` > 첫 문단 |
| `assets/img/` | 프로필 사진(`profile.jpg`), 논문 썸네일(`pubs/` 폴더를 만들어 넣기) |
| `assets/cv.pdf` | CV 파일 — `cv/build_cv.py`로 생성 (아래 참고) |
| `assets/css/main.css` | 스타일 (상단 `:root` 색상 변수, 다크모드 자동) |

- 사용하지 않는 링크는 `_config.yml`에서 **주석 처리**하세요 (빈 문자열 `""`은 링크가 표시됨).
- 논문 저자 목록에서 `author.name`과 정확히 같은 문자열이 자동으로 굵게 표시됩니다.

## 배포

1. GitHub에 `<username>.github.io` 이름으로 저장소 생성
2. 이 폴더를 push
3. Settings → Pages → Source: *Deploy from a branch*, `main` / `(root)`
4. `https://<username>.github.io` 접속

## 로컬 미리보기

```bash
scripts/serve.sh        # http://localhost:4000, 끄기: Ctrl+C
```

conda `jekyll` 환경(Ruby 3.x + jekyll)을 자동으로 켜서 `jekyll serve --livereload`를 실행합니다. `--port 4001`처럼 jekyll 옵션을 덧붙일 수 있습니다.
처음 한 번은 환경을 만들어야 합니다:

```bash
conda create -y -n jekyll -c conda-forge ruby=3.3 compilers make
conda activate jekyll && gem install jekyll webrick kramdown-parser-gfm
```

> 로컬 서버(WEBrick)는 영상 여러 개가 있는 페이지에서 재생이 끊길 수 있습니다. 배포된 GitHub Pages에서는 문제없습니다.

## CV PDF 빌드

`cv/cv.yml`로 1페이지 CV를 만들어 `assets/cv.pdf`에 저장합니다 (사이트의 CV 버튼이 이 파일을 가리킴).
CV 데이터는 사이트 데이터(`_config.yml`, `_data/*.yml`)와 **별개**입니다 — 사이트를 고쳐도 CV는 그대로이니 필요하면 둘 다 수정하세요.
Chrome(headless)으로 PDF를 출력하므로 Chrome이 설치되어 있어야 합니다. 사이트와 같은 웹폰트(Inter, Noto Sans KR)를 쓰므로 빌드할 때 인터넷 연결이 필요합니다 (없으면 시스템 글꼴로 대체).

```bash
scripts/build_cv.sh                    # -> assets/cv.pdf (.venv 없으면 자동 생성·설치)
scripts/build_cv.sh -o my.pdf --html   # 다른 경로로, 중간 HTML도 저장
```

| 파일 | 내용 |
|---|---|
| `cv/cv.yml` | CV 전체 내용 (Profile, 소개, Research Interests, Publications, Education & Experience / Honors & Awards 타임라인, Projects, Skills) |
| `cv/private.yml` | 전화번호 등 비공개 값 — git에 올라가지 않음. `cv/private.example.yml`을 복사해서 사용 |
| `cv/template.html` | CV 레이아웃 (Jinja2) |
| `cv/style.css` | CV 스타일 — 사이트와 같은 색·글꼴·구성을 A4 인쇄용으로 옮김 (여백, 글꼴 크기) |

- 1페이지를 넘으면 경고가 뜹니다. `cv/style.css`의 글꼴 크기·간격을 줄이거나 내용을 덜어내세요.
- `cv/` 폴더는 `_config.yml`의 `exclude`에 들어 있어 웹사이트에는 공개되지 않습니다.

## 영상 압축 (블로그용)

블로그 글의 미디어는 글마다 폴더 하나에 모읍니다. `<post>`는 글 파일명에서 날짜를 뺀 부분입니다 (`_posts/2025-10-10-ur5_allegro.md` → `ur5_allegro`).

```
assets/post/<post>/raw/   원본 영상 — git·사이트에서 제외
assets/post/<post>/       압축본 .mp4 + 대표 이미지 .jpg (영상 poster / 블로그 목록 썸네일)
```

```bash
.venv/bin/pip install -r tools/requirements.txt     # 최초 1회 (ffmpeg 포함)
.venv/bin/python tools/compress_video.py            # 모든 글의 raw/, 이미 변환된 건 건너뜀
.venv/bin/python tools/compress_video.py ur5_allegro   # 특정 글만
.venv/bin/python tools/compress_video.py -f --ignore-rotation assets/post/ur5_allegro/raw/clip.mp4   # 옆으로 누워 나올 때
```

기본값: 높이 최대 720p, CRF 28, 최대 30fps, 소리 제거 (`--keep-audio`로 유지). 글에는 이렇게 넣습니다.

```html
<video src="{{ '/assets/post/<post>/clip.mp4' | relative_url }}" poster="{{ '/assets/post/<post>/clip.jpg' | relative_url }}" controls muted loop playsinline preload="metadata"></video>
```

세로 영상·사진 여러 개를 한 줄에 나란히 놓으려면 `<div class="media-row"> ... </div>`로 감쌉니다. 비율이 서로 달라도 높이가 자동으로 맞춰집니다 (`_layouts/post.html`의 스크립트).
2열 격자(2×2 등)는 `<div class="media-grid"> ... </div>`.

사진도 같은 구조로: 원본을 `assets/post/<post>/raw/`에 넣고 `.venv/bin/python tools/compress_image.py <post>` → 가로 최대 1280px JPG.
