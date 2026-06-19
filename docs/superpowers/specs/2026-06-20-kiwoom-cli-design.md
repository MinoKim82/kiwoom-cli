# Kiwoom REST API CLI Design Specification

본 문서는 키움 REST API를 기반으로 유저별 App Key와 App Secret을 관리하고, 토큰(Auth Token)을 자동으로 갱신하면서 계좌 평가 및 보유 종목의 현재가를 조회하는 CLI 도구의 설계서입니다.

---

## 1. 요구사항 및 주요 목표
1. **다중 사용자 지원**: 최대 3명의 사용자가 각자의 App Key 및 App Secret을 가지고 사용합니다.
2. **자격 증명과 세션 상태의 분리**: 수동으로 관리하는 API 키 정보(Credential)와 프로그램이 자동으로 갱신하는 토큰(Session State)을 별도의 파일로 격리하여 안전하게 관리합니다.
3. **토큰 자동 갱신(Auto-refresh)**: 
   - 토큰의 유효 기간을 체크하여 만료되었거나 만료 임박(10분 이내)한 경우 API 요청 직전에 자동으로 갱신합니다.
   - 갱신된 토큰은 캐시 파일에 자동으로 업데이트하여 쓰기 작업을 수행합니다.
4. **보유 종목의 누락 없는 조회**: 보유 종목 조회 시 데이터가 많아 연속조회(`cont-yn: "Y"`)가 활성화된 경우 자동으로 루프를 돌며 페이지네이션을 처리해 누락 없이 전체 종목을 출력합니다.
5. **CLI 기반 간결한 출력**: 터미널 환경에서 가독성이 뛰어난 표 형태로 정렬하여 계좌 현황 및 종목 정보를 출력합니다.

---

## 2. 파일 저장소 및 데이터 구조

설정과 토큰 정보는 사용자 홈 디렉토리(`~/.kiwoom/`) 하위의 두 파일로 격리합니다.

### A. 고정 설정 파일 (`~/.kiwoom/config.json`)
사용자가 최초 1회 수동으로 입력하는 정보로, 유저별 App Key와 Secret Key를 보관합니다. 이 파일은 CLI 프로그램에 의해 읽기 전용으로만 사용되어 손상 위험이 없습니다.

```json
{
  "users": {
    "user1": {
      "appkey": "user1_app_key_value",
      "secretkey": "user1_secret_key_value"
    },
    "user2": {
      "appkey": "user2_app_key_value",
      "secretkey": "user2_secret_key_value"
    },
    "user3": {
      "appkey": "user3_app_key_value",
      "secretkey": "user3_secret_key_value"
    }
  }
}
```

### B. 동적 토큰 캐시 파일 (`~/.kiwoom/tokens.json`)
CLI 프로그램이 API 호출 과정에서 토큰을 획득/갱신할 때 실시간으로 생성 및 업데이트하는 상태 저장용 파일입니다.

```json
{
  "user1": {
    "token": "bearer_access_token_value_for_user1",
    "expires_dt": "20260621123456"
  },
  "user2": {
    "token": "bearer_access_token_value_for_user2",
    "expires_dt": "20260620235959"
  }
}
```
* **만료 포맷(`expires_dt`)**: 키움 REST API가 리턴하는 `YYYYMMDDHHMMSS` (KST 기준) 문자열 형식을 따릅니다.

---

## 3. 소프트웨어 아키텍처 및 모듈 설계

프로젝트는 모듈형 파이썬 스크립트 구조로 설계합니다.

```text
kiwoom-cli/
├── config.py     # 설정 및 토큰 디렉토리/파일 입출력 관리
├── client.py     # 키움 REST API 통신 및 토큰 만료 처리 자동화
└── cli.py        # Click 라이브러리 기반 명령어 인터페이스 및 터미널 출력
```

### A. `config.py` (`ConfigManager`)
* **역할**: 설정 경로 `~/.kiwoom/` 생성 여부를 점검하고, `config.json`과 `tokens.json`을 안전하게 읽고 쓰는 책임을 집니다.
* **주요 메서드**:
  - `get_user_credentials(user_id)`: `config.json`에서 해당 유저의 `appkey`, `secretkey`를 반환합니다.
  - `get_cached_token(user_id)`: `tokens.json`에서 유저의 현재 토큰 및 만료 시각을 가져옵니다.
  - `update_token(user_id, token, expires_dt)`: 새로운 토큰 정보를 `tokens.json`에 영속화합니다.

### B. `client.py` (`KiwoomClient`)
* **역할**: 키움 REST API (`https://api.kiwoom.com`)와의 통신을 제어하며, 토큰 유효성 검사 및 자동 갱신을 숨겨진 로직(Encapsulated Logic)으로 처리합니다.
* **토큰 검증 및 자동 갱신 메커니즘**:
  - API 요청(`request_api`) 호출 시 먼저 `tokens.json`에서 가져온 `expires_dt`를 파싱하여 `datetime` 객체로 변환합니다.
  - `만료 시각(KST) - 현재 시각(KST) < 10분`일 경우, `au10001` (접근토큰 발급) API를 호출하여 새로운 토큰을 발급받습니다.
  - 발급받은 신규 토큰 정보를 `ConfigManager.update_token`을 호출해 디스크에 저장합니다.
* **주요 API 연동 메서드**:
  - `issue_token(appkey, secretkey)`: `/oauth2/token` POST 요청을 전송해 토큰을 신규 발급합니다.
  - `get_accounts()`: `/api/dostk/acnt` (`ka00001`) POST 요청을 전송해 연결된 계좌번호 리스트를 반환합니다.
  - `get_balance(acct_no)`: `/api/dostk/acnt` (`kt00018`) POST 요청을 통해 계좌 총 평가 현황 및 종목 정보를 조회합니다. 연속 데이터가 있는 경우 `cont-yn == "Y"`인 조건 동안 루프를 통해 페이지네이션 조회를 재귀/순차 처리합니다.

### C. `cli.py` (CLI interface)
* **역할**: 사용자의 명령어를 처리하고 출력 결과를 터미널에 사람이 읽기 쉬운 형태로 출력합니다.
* **CLI 옵션**:
  - `--user` 또는 `-u` (필수): 유저 식별용 ID (e.g. `user1`)
* **명령어 종류**:
  - `accounts`: 사용자 명의의 계좌 목록 출력
  - `balance`: 특정 계좌(미지정 시 기본 첫 번째 계좌)의 예수금, 평가총액, 보유 종목 상세 테이블 출력
* **포매팅**:
  - 종목 리스트 테이블 출력 시 가로폭 및 우측 정렬 포매팅 처리.
  - 손익 및 수익률에 대해 부호(`+`, `-`) 표시 적용.

---

## 4. 예외 처리 및 고려사항
1. **설정 파일 부재**: `~/.kiwoom/config.json`이 없거나 정보가 부실한 경우 "설정 파일이 없습니다. `~/.kiwoom/config.json`을 작성해 주세요"라는 안내 가이드를 출력합니다.
2. **API 호출 에러**: 키움 REST API 응답의 `return_code`가 `0`이 아닐 경우 오류 메시지(`return_msg`)를 터미널에 표시하고 비정상 종료합니다.
3. **네트워크 단절**: 네트워크 오류(`requests.RequestException`) 발생 시 오류 문구를 출력하고 안전하게 예외 처리를 수행합니다.
