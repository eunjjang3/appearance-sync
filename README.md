# System Theme Switcher 0.2.0

Blender에서 **이미 설치된 테마 두 개**를 macOS의 라이트·다크 모드에 맞춰 자동 전환하는 첫 버전입니다.

## 대상 환경

- Blender 5.0 이상, macOS. 실제 검증: Blender 5.0.1 / macOS Sequoia 15.7.4 / Apple Silicon.
- Intel Mac은 패키지 대상에 포함되지만 실기기 검증은 하지 않았습니다.
- Windows / Linux 자동 감지는 이번 버전에 포함하지 않습니다.

## 설치

1. `system_theme_switcher-0.2.0.zip`을 압축 해제하지 않고 준비합니다.
2. Blender → **Edit → Preferences → Add-ons**의 우측 상단 메뉴에서 **Install from Disk…**를 선택합니다.
3. ZIP을 선택해 설치하고 **System Theme Switcher**를 활성화합니다.
4. 애드온 항목을 펼쳐 **Follow macOS Appearance**를 켭니다. 기본값은 켜짐입니다.
5. **Light theme / Dark theme**에서 각 모드의 테마를 고릅니다. 기본값은 Blender Light / Blender Dark입니다.

Blender 설정 자동 저장을 꺼둔 경우 Preferences의 **Save Preferences**로 애드온 활성화와 선택한 테마를 저장하세요. 이 애드온은 전체 환경설정 저장을 직접 호출하지 않습니다.

## 부드러운 색상 전환

- 색상 전환은 항상 **0.35초**로 동작합니다. 별도의 효과 토글이나 시간 설정은 없습니다.
- 색상과 알파 값을 보간하며 시작과 끝을 천천히 잇습니다. 전환 중 다른 테마를 요청하면 현재 보이는 색에서 이어집니다.
- 애니메이션 중에만 최대 약 60Hz로 갱신을 요청합니다. 실제 프레임 속도는 Blender 작업 부하에 따라 달라집니다.
- 글꼴·크기·옵션 등 색이 아닌 설정은 마지막에 적용하며, 마지막 프레임은 원본 테마와 정확히 일치합니다.
- 전환 중 일시 정지·애드온 비활성화·파일 열기를 하면 목표 테마로 마무리합니다. Restore는 전환을 취소하고 기존 테마로 복원합니다.
- macOS 네이티브 애니메이션 API를 호출하는 기능은 아니며, Blender 테마 색상에 유사한 부드러운 전환을 구현합니다.

## 동작

- Blender 실행 중 약 2초마다 macOS의 현재 모드를 확인하고 바뀌면 전환합니다. 무한 루프가 아니라 Blender 타이머 기반 폴링입니다. 타이머 콜백은 0.25초 간격으로 돌아오지만 OS 조회는 약 2초 간격으로만 실행합니다. 2초는 초기 구현에서 선택한 반응 속도와 조회 빈도의 절충값이며, macOS의 요구사항은 아닙니다.
- macOS의 자동 모드도 실제 화면 모드가 바뀌면 따라갑니다. 별도 시간표는 없습니다.
- 기본 제공 테마, 기존 XML 프리셋, 로컬에 설치된 테마 확장을 선택할 수 있습니다. 새 테마 설치는 Blender의 기존 Themes / Get Extensions 기능을 사용하세요.
- **Sync Now**: 시스템 모드를 다시 읽고 선택한 테마를 다시 적용합니다.
- **Follow macOS Appearance** 끄기: 현재 테마를 유지하며 자동 전환을 멈춥니다. 진행 중인 전환은 목표 테마로 마무리합니다.
- **Restore Previous Theme**: 이번 애드온 실행에서 첫 전환 직전의 테마와 폰트 스타일로 복원하고 자동 전환을 멈춥니다.
- 상태가 같으면 테마를 반복 적용하지 않습니다. 수동 색 수정은 다음 모드 변경·테마 선택 변경·Sync Now까지 유지됩니다.
- 테마가 삭제되었거나 시스템 감지에 실패하면 현재 테마를 유지하고 애드온 설정에 오류를 표시합니다. 실패 후 약 5초 간격으로 재시도합니다.
- 애드온을 비활성화하면 감지를 종료하고 현재 테마는 유지합니다.

## 이번 버전의 범위

- **기존 테마 전체를 적용합니다.** 선택한 테마가 뷰포트·축·선택 색·폰트 스타일을 정의하면 그것도 바뀝니다. UI 색만 따로 적용하는 기능과 세 색으로 만드는 팔레트는 후속 범위입니다.
- 복원 스냅샷은 메모리에만 있고 Blender 종료 / 애드온 비활성화 시 사라집니다. 재시작을 넘기는 영구 백업이 필요하면 Blender Themes에서 현재 테마를 먼저 저장하세요.
- 사용자 지정 테마는 로컬 XML의 절대 경로를 저장합니다. 다른 PC로 설정을 옮기거나 파일을 이동하면 다시 선택해야 합니다.
- 테마 파일 자체의 내용 변경은 자동 감시하지 않습니다. **Sync Now**를 누르면 다시 읽습니다.
- 시스템 변경은 실제 UI 이벤트를 강제하지 않고, macOS 감지와 Blender 내부 양방향 전환을 각각 검증했습니다. macOS 설정을 실제로 토글하는 종단 테스트는 미실시입니다.

## 개발 및 검증

소스: `system_theme_switcher/`, 테스트: `tests/`.

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
blender --background --factory-startup --python-exit-code 1 --python tests/blender_integration.py
blender --background --factory-startup --python-exit-code 1 --python tests/blender_transition.py
blender --background --factory-startup --command extension validate system_theme_switcher
blender --background --factory-startup --command extension build --source-dir system_theme_switcher --output-dir ..
```

Blender 실행 파일이 PATH에 없다면 실제 설치 경로로 대체하세요. 테스트는 공장 초기 설정으로 별도 프로세스에서 실행하며 사용자 환경설정을 저장하지 않습니다. 의도적으로 불완전한 XML을 적용하는 롤백 테스트는 예상된 Blender 오류 로그를 발생시킵니다.

구현은 Blender의 기존 [테마 프리셋 적용 경로](https://github.com/blender/blender/blob/blender-v5.0-release/scripts/startup/bl_operators/presets.py)와 [Themes 설정 정의](https://github.com/blender/blender/blob/blender-v5.0-release/scripts/startup/bl_ui/space_userpref.py)를 사용합니다. OS 감지는 Python 표준 라이브러리와 macOS 내장 `defaults` 명령으로 처리하며 추가 라이브러리나 네트워크 연결은 필요하지 않습니다.

라이선스: GPL-3.0-or-later.
