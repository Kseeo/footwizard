# 발 추출 마법사 (Foot Extract Wizard)

3D 발 스캔(GLB) 파일을 업로드하면, 발 부위만 자동으로 잘라내고 방향을
맞춘 다음 발목 위치를 사람이 직접 골라 절단·정리까지 마쳐주는 로컬 웹
마법사입니다. Windows용 단일 exe로 패키징해서 씁니다.

## 사용 흐름

브라우저 화면(`webapp/templates/wizard.html`)에서 4단계로 진행됩니다.

1. **업로드**: GLB 파일 선택
2. **방향 선택**: 발을 자동으로 크롭하고, 발바닥 방향 후보 여러 개를
   보여주면 사람이 그중 맞는 걸 고릅니다
3. **절단 위치**: 고른 방향으로 정렬된 메쉬를 3D로 보면서 발목을 자를
   높이를 직접 고릅니다
4. **완료**: 자르기 + 스케일 맞춤 + 표면 정리(스무딩)까지 마친 결과를
   내려받습니다

## 개발 모드로 실행

```powershell
<파이썬 실행 환경>\python.exe webapp/launcher.py
```

브라우저가 자동으로 `http://127.0.0.1:5050`을 엽니다. 필요한 패키지는
`requirements.txt`(직접 만들어야 함 -- 아래 "패키지 설치" 참고)를 미리
설치해둔 파이썬 환경이어야 합니다.

## 폴더 구조

- `webapp/launcher.py` -- exe 진입점. Flask 서버를 띄우고 브라우저를 연다.
- `webapp/app.py` -- 마법사 화면이 호출하는 API 라우트.
- `webapp/stage1_orientation_worker.py` -- 발 크롭 + 방향 후보 계산을
  전담하는 워커(3D 렌더링이 서버 프로세스를 불안정하게 만들 수 있어 매
  요청마다 별도 프로세스로 띄운다).
- `webapp/templates/wizard.html` -- 마법사 화면 전체(HTML/CSS/JS 한 파일).
- `src/foot_engine/` -- 실제 메쉬 처리 로직. `pipeline.py`가 진입점(크롭 →
  정렬 → 절단 → 정리), 나머지 모듈은 그게 갖다 쓰는 유틸(자세한 역할은
  `src/foot_engine/__init__.py` 참고).
- `data/models/` -- 피부 분류에 쓰는 MediaPipe 모델 파일.
- `build.ps1` -- PyInstaller 빌드 스크립트(실행하면 `FootExtractWizard.spec`을
  이 폴더에 새로 만든다 -- 그 파일은 개인 PC 경로가 담겨 git엔 안 올림).

## 패키지 설치

이 폴더엔 파이썬 실행 환경(venv)이 들어있지 않습니다. 새로 만들려면:

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

exe 빌드까지 하려면 `pyinstaller`도 추가로 설치할 것(`requirements.txt`엔
빌드 도구는 안 들어있음, 실행에 필요한 패키지만).

## exe 빌드

```powershell
powershell -File build.ps1
```

`dist\FootExtractWizard\` 폴더가 산출물입니다 -- `FootExtractWizard.exe`
파일 하나가 아니라 `_internal\` 폴더까지 **폴더 전체**를 같이 옮겨야
실행됩니다.

## 알려진 제약

- 인터넷 연결이 필요합니다(3D 뷰어 라이브러리·폰트를 CDN에서 매번 불러옴).
- 발바닥 방향이 자동으로 애매하게 잡히는 스캔은 2단계에서 사람이 후보
  중 직접 골라야 합니다.
