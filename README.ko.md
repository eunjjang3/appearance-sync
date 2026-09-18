# Appearance Sync 0.1.3

Blender에서 **이미 설치된 테마 두 개**를 macOS의 라이트·다크 모드에 맞춰 자동 전환하는 애드온입니다.

## 대상 환경

- Blender 5.0 이상, macOS. 실제 검증: Blender 5.0.1 / macOS Sequoia 15.7.4 / Apple Silicon.
- Intel Mac은 패키지 대상에 포함되지만 실기기 검증은 하지 않았습니다.
- Windows / Linux 자동 감지는 이번 버전에 포함하지 않습니다.

## 설치

1. `appearance-sync-0.1.3.zip`을 압축 해제하지 않고 준비합니다.
2. Blender → **Edit → Preferences → Add-ons**의 우측 상단 메뉴에서 **Install from Disk…**를 선택합니다.
3. ZIP을 선택해 설치하고 **Appearance Sync**를 활성화합니다.
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

- 시작할 때 한 번 모드를 읽고, 이후에는 macOS 화면 모드 변경 알림을 받아 전환합니다. 주기적인 OS 조회와 상시 감지 타이머는 없습니다.
- 알림은 CoreFoundation의 분산 알림 센터로 구독합니다. 알림 본문의 데이터는 신뢰하지 않고 `defaults`로 현재 모드를 한 번 읽습니다. 이 비동기 조회가 끝날 때까지만 짧은 Blender 타이머를 사용합니다.
- 연속 알림은 하나의 조회로 합칩니다. 조회 중 새 알림이 오면 오래된 결과를 버리고 최신 상태를 다시 읽습니다.
- macOS의 자동 모드도 실제 화면 모드가 바뀌면 따라갑니다. 별도 시간표는 없습니다.
- 기본 제공 테마, 기존 XML 프리셋, 로컬에 설치된 테마 확장을 선택할 수 있습니다. 새 테마 설치는 Blender의 기존 Themes / Get Extensions 기능을 사용하세요.
- **Sync Now**: 시스템 모드를 다시 읽고 선택한 테마를 다시 적용합니다.
- **Follow macOS Appearance** 끄기: 현재 테마를 유지하며 자동 전환을 멈춥니다. 진행 중인 전환은 목표 테마로 마무리합니다.
- **Restore Previous Theme**: 이번 애드온 실행에서 첫 전환 직전의 테마와 폰트 스타일로 복원하고 자동 전환을 멈춥니다.
- 상태가 같으면 테마를 반복 적용하지 않습니다. 수동 색 수정은 다음 모드 변경·테마 선택 변경·Sync Now까지 유지됩니다.
- 테마가 삭제되었거나 시스템 감지에 실패하면 현재 테마를 유지하고 애드온 설정에 오류를 표시합니다. 다음 모드 변경 알림이나 **Sync Now**로 재시도합니다.
- 애드온을 비활성화하면 알림 구독과 조회를 종료합니다. 전환 중이었다면 목표 테마로 마무리합니다.

## 이번 버전의 범위

- **기존 테마 전체를 적용합니다.** 선택한 테마가 뷰포트·축·선택 색·폰트 스타일을 정의하면 그것도 바뀝니다. UI 색만 따로 적용하는 기능과 세 색으로 만드는 팔레트는 후속 범위입니다.
- 복원 스냅샷은 메모리에만 있고 Blender 종료 / 애드온 비활성화 시 사라집니다. 재시작을 넘기는 영구 백업이 필요하면 Blender Themes에서 현재 테마를 먼저 저장하세요.
- 사용자 지정 테마는 로컬 XML의 절대 경로를 저장합니다. 다른 PC로 설정을 옮기거나 파일을 이동하면 다시 선택해야 합니다.
- 테마 파일 자체의 내용 변경은 자동 감시하지 않습니다. **Sync Now**를 누르면 다시 읽습니다.
- `AppleInterfaceThemeChangedNotification`이라는 관례적 알림 이름을 사용합니다. 분산 알림 API 자체는 공개 API지만, 이 이름은 Apple이 보장하는 공개 상수가 아닙니다. 향후 macOS 호환성을 확인해야 하며 알림 누락 시 **Sync Now**로 동기화할 수 있습니다.
- 자동화 테스트로 네이티브 알림과 Blender GUI 동작을 검증했고, 사용자가 실제 시스템 전환도 정상 동작한다고 확인했습니다. Intel Mac에서의 실제 동작은 아직 검증하지 않았습니다.

## 개발 및 검증

소스: `system_theme_switcher/`, 테스트: `tests/`.

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
blender --background --factory-startup --python-exit-code 1 --python tests/blender_integration.py
blender --background --factory-startup --python-exit-code 1 --python tests/blender_transition.py
blender --background --factory-startup --python-exit-code 1 --python tests/blender_notifications.py
blender --background --factory-startup --command extension validate system_theme_switcher
blender --background --factory-startup --command extension build --source-dir system_theme_switcher --output-dir ..
```

Blender 실행 파일이 PATH에 없다면 실제 설치 경로로 대체하세요. 테스트는 공장 초기 설정으로 별도 프로세스에서 실행하며 사용자 환경설정을 저장하지 않습니다. 의도적으로 불완전한 XML을 적용하는 롤백 테스트는 예상된 Blender 오류 로그를 발생시킵니다.

구현은 Blender의 기존 [테마 프리셋 적용 경로](https://github.com/blender/blender/blob/blender-v5.0-release/scripts/startup/bl_operators/presets.py)와 [Themes 설정 정의](https://github.com/blender/blender/blob/blender-v5.0-release/scripts/startup/bl_ui/space_userpref.py)를 사용합니다. OS 알림 구독은 Python `ctypes`와 macOS CoreFoundation으로, 알림 수신 후 상태 조회는 내장 `defaults` 명령으로 처리합니다. 추가 패키지나 네트워크 연결은 필요하지 않습니다. 알림 전달 방식은 [Apple 분산 알림 문서](https://developer.apple.com/documentation/foundation/distributednotificationcenter)를, 사용한 알림 이름은 [Electron의 공식 구독 예제](https://github.com/electron/electron/blob/main/docs/api/system-preferences.md#systempreferencessubscribenotificationevent-callback-macos)를 참고했습니다.

라이선스: GPL-3.0-or-later.
