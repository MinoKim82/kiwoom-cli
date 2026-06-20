# Kiwoom CLI 입출력 명세서 (CLI I/O Specifications)

이 명세서는 **Kiwoom CLI**의 모든 입력 케이스에 따른 명령어 사용법, 터미널 출력 형식(Text), 그리고 JSON 형식으로 출력될 때 각 데이터 필드와 값이 나타내는 비즈니스적 의미 및 상세 스키마 정의를 포함합니다.

---

## 1. 전역 옵션 (Global Options)

CLI의 동작 모드를 제어하거나 입력 매개변수를 처리하기 위한 공통 옵션 목록입니다.

| 옵션명 | 단축형 | 필수 여부 | 기본값 | 설명 및 비즈니스적 의미 |
| :--- | :--- | :--- | :--- | :--- |
| `--config-dir` | 없음 | 선택 | `~/.kiwoom` | `config.json` (계좌 설정) 및 `tokens.json` (인증 토큰) 파일이 위치하는 파일시스템 디렉토리 경로 지정. 격리된 테스트 환경이나 다중 계정 프로필 관리에 유용합니다. |
| `--account` | `-a` | 선택 | 없음 | 조회 대상이 될 **계좌의 별칭(alias)**을 지정합니다. (예: `mh_default`, `mh_sub`).<br>**미지정 시**: `config.json`에 정의된 **모든 계좌를 순회 조회**하며, 에러가 발생한 계좌는 격리 처리하고 정상 계좌의 결과만 출력 목록에 유지합니다. |
| `--format` | `-f` | 선택 | `text` | 출력의 포맷 형식을 정의합니다. (`text` 또는 `json`).<br>- `text`: 사람이 읽기 편하도록 서식이 지정된 표(table) 및 통화 포맷 기호(`,`, `원`, `%`)가 붙은 형태로 터미널에 출력됩니다.<br>- `json`: 자동화 스크립트나 외부 언어 바인딩에서 파싱하기 쉽도록 정형화된 JSON 배열 또는 객체 구조로 반환합니다. |

> [!NOTE]
> `--format / -f` 옵션은 전역 옵션(명령어 앞)으로 지정할 수도 있고, 개별 하위 명령어 뒤에 지정하여 적용(Override)할 수도 있습니다.
> 
> **예시**:
> - `kiwoom -f json accounts` (전역 옵션으로 처리)
> - `kiwoom accounts -f json` (하위 명령어 뒤에서 덮어쓰기로 처리)
> 
> 두 명령어 방식 모두 내부적으로 동일하게 작동합니다.

---

## 2. 명령어별 입력 케이스 & 출력 결과 명세

### 2.1. `accounts` 명령어
설정 파일(`config.json`)에 등록된 계좌들의 **사용자 정의 별칭(Alias)**과, 이에 대응되어 매핑된 **가공된 8자리 실제 계좌 번호**의 리스트를 조회합니다.

#### 입력 케이스 (Input Cases)
1. **모든 등록 계좌 조회 (텍스트 포맷)**
   ```bash
   kiwoom accounts
   ```
2. **모든 등록 계좌 조회 (JSON 포맷)**
   ```bash
   kiwoom accounts -f json
   ```
3. **특정 단일 계좌의 매핑 정보 조회 (텍스트 포맷)**
   ```bash
   kiwoom -a mh_default accounts
   ```
4. **특정 단일 계좌의 매핑 정보 조회 (JSON 포맷)**
   ```bash
   kiwoom -a mh_default accounts -f json
   ```

#### 출력 결과 (Output Examples)
##### A. 텍스트 형식 (`--format text`)
```text
=== 등록된 계좌 목록 ===
 1. 별칭: mh_default   | 계좌번호: 12345678
 2. 별칭: mh_sub       | 계좌번호: 98765432
```

##### B. JSON 형식 (`--format json`)
* **다중 계좌 조회 시 (기본 동작)**:
  ```json
  [
    {
      "account_alias": "mh_default",
      "acct_no": "12345678"
    },
    {
      "account_alias": "mh_sub",
      "acct_no": "98765432"
    }
  ]
  ```
* **단일 계좌 조회 시 (`-a mh_default` 지정 시)**:
  ```json
  {
    "account_alias": "mh_default",
    "acct_no": "12345678"
  }
  ```

#### JSON 출력 필드 설명 및 의미 (JSON Schema Meanings)
| 필드명 | 데이터 타입 | 예시값 | 비즈니스적 의미 및 규칙 |
| :--- | :--- | :--- | :--- |
| `account_alias` | String | `"mh_default"` | 사용자가 로컬 `config.json` 설정 파일에 등록한 계좌의 고유 식별자용 별칭(Alias)입니다. |
| `acct_no` | String | `"12345678"` | 키움증권 서버에서 발급한 **10자리 전체 계좌번호 중 앞 8자리**입니다. 계좌 뒤 2자리의 구분 코드가 모호하여 혼선을 주는 것을 피하기 위해, 실제 고유 계좌 식별용인 앞 8자리 문자열만 가공하여 노출합니다. |
| `error` | String | `"..."` | 개별 계좌 조회에 실패했거나 토큰 발급에 실패하는 등 예외 발생 시, 정상 필드 대신 들어가는 에러 원인 메시지입니다. (오류 발생 시에만 제한적으로 포함) |

---

### 2.2. `balance` 명령어
계좌의 자산 평가 상태(총 매입액, 총 평가액, 총 손익, 전체 수익률, 추정예탁자산) 및 실시간 보유 주식 개별 현황(종목코드, 종목명, 보유수량, 매입단가, 현재가, 개별 평가손익 및 수익률)을 조회합니다.

#### 입력 케이스 (Input Cases)
1. **모든 등록 계좌의 잔고 현황 순회 조회 (텍스트 포맷)**
   ```bash
   kiwoom balance
   ```
2. **모든 등록 계좌의 잔고 현황 순회 조회 (JSON 포맷)**
   ```bash
   kiwoom balance -f json
   ```
3. **특정 계좌의 잔고 현황 단일 조회 (텍스트 포맷)**
   ```bash
   kiwoom -a mh_default balance
   ```
4. **특정 계좌의 잔고 현황 단일 조회 (JSON 포맷)**
   ```bash
   kiwoom -a mh_default balance -f json
   ```
5. **특정 실제 계좌번호를 지정하여 필터링 조회**
   ```bash
   kiwoom -a mh_default balance --acct 9876543204
   ```

#### 출력 결과 (Output Examples)
##### A. 텍스트 형식 (`--format text`)
```text
==================================================
  [12345678] 계좌 평가 현황
==================================================
계좌 번호   : 12345678
추정예탁자산 : 15,230,000 원
총 매입금액  : 10,000,000 원
총 평가금액  : 12,500,000 원
총 평가손익  : +2,500,000 원
총 수익률    : +25.00%
==================================================

==========================================================================================
  [12345678] 보유 종목 현황
==========================================================================================
종목코드     | 종목명             | 보유수량     | 매입단가     | 현재가      | 평가손익     | 수익률  
------------------------------------------------------------------------------------------
005930   | 삼성전자           | 100 주    | 70,000 원 | 75,000 원 |   +500,000 |  +7.14%
==========================================================================================
```

##### B. JSON 형식 (`--format json`)
* **다중 계좌 조회 시 (기본 동작)**:
  ```json
  [
    {
      "account": "mh_default",
      "acct_no": "1234567810",
      "balance": {
        "tot_pur_amt": "10000000",
        "tot_evlt_amt": "12500000",
        "tot_evlt_pl": "2500000",
        "tot_prft_rt": "25.00",
        "prsm_dpst_aset_amt": "15230000",
        "acnt_evlt_remn_indv_tot": [
          {
            "stk_cd": "A005930",
            "stk_nm": "삼성전자",
            "rmnd_qty": "100",
            "pur_pric": "70000",
            "cur_prc": "75000",
            "evltv_prft": "500000",
            "prft_rt": "7.14"
          }
        ]
      }
    }
  ]
  ```
* **단일 계좌 조회 시 (`-a mh_default` 지정 시)**:
  ```json
  {
    "account": "mh_default",
    "acct_no": "1234567810",
    "balance": {
      "tot_pur_amt": "10000000",
      "tot_evlt_amt": "12500000",
      "tot_evlt_pl": "2500000",
      "tot_prft_rt": "25.00",
      "prsm_dpst_aset_amt": "15230000",
      "acnt_evlt_remn_indv_tot": [
        {
          "stk_cd": "A005930",
          "stk_nm": "삼성전자",
          "rmnd_qty": "100",
          "pur_pric": "70000",
          "cur_prc": "75000",
          "evltv_prft": "500000",
          "prft_rt": "7.14"
        }
      ]
    }
  }
  ```

#### JSON 출력 필드 설명 및 의미 (JSON Schema Meanings)
| 필드명 | 데이터 타입 | 단위/규격 | 비즈니스적 의미 및 파싱 가이드 |
| :--- | :--- | :--- | :--- |
| `account` | String | 없음 | 해당 조회를 수행한 로컬 계좌 별칭(Alias)입니다. |
| `acct_no` | String | 없음 | **10자리 전체 계좌번호** (8자리 계좌번호 + 2자리 구분코드)가 출력됩니다. 텍스트 가독성을 위한 표기에서는 8자리를 노출하지만, 외부 시스템이나 상위 자동화 스크립트에서 키움 API 통신 및 데이터 무결성 보존을 할 수 있도록 JSON 포맷에는 원본 10자리 문자열을 보존하여 반환합니다. |
| `balance` | Object | 없음 | 포트폴리오 집계 금액 정보 및 보유 주식 종목 리스트를 담은 잔고 평가 데이터 그룹입니다. |
| `balance.tot_pur_amt` | String | 원(KRW) | 계좌 내 전체 보유 종목의 **총 매입 금액** 합계입니다. (각 종목의 매입단가 $\times$ 보유수량의 총합) |
| `balance.tot_evlt_amt` | String | 원(KRW) | 계좌 내 전체 보유 종목의 **총 평가 금액** 합계입니다. (각 종목의 시장 현재가 $\times$ 보유수량의 총합) |
| `balance.tot_evlt_pl` | String | 원(KRW) | 계좌 내 전체 보유 종목의 **총 평가 손익** 합계입니다. (`총 평가 금액` - `총 매입 금액` 으로 계산되며, 미실현 손익을 뜻합니다. 플러스 값일 경우 이득, 마이너스 값일 경우 손실을 의미합니다.) |
| `balance.tot_prft_rt` | String | 퍼센트(%) | 계좌 전체 자산의 **총 수익률**입니다. 소수점 2자리 문자열 형식으로 표기됩니다. |
| `balance.prsm_dpst_aset_amt` | String | 원(KRW) | 해당 계좌의 **추정 예탁 자산 평가액**입니다. 계좌에 예수금으로 남아있는 현금 자산과 보유 주식 평가액 등을 합산하여 종합 계산된 총 자산 추정치입니다. |
| `balance.acnt_evlt_remn_indv_tot` | Array | 없음 | 현재 실시간으로 계좌 내에 보유하고 있는 **개별 보유 주식 종목 리스트**의 배열입니다. |
| `balance.acnt_evlt_remn_indv_tot[].stk_cd` | String | 없음 | **주식 종목 코드**입니다. 키움 API 규격에 따라 접두사 `"A"`가 붙은 7자리 문자열 포맷(예: `"A005930"`)을 그대로 전달하므로 파싱 시 참고가 필요합니다. |
| `balance.acnt_evlt_remn_indv_tot[].stk_nm` | String | 없음 | 한글 또는 영문으로 구성된 **주식 종목명**입니다. (예: `"삼성전자"`) |
| `balance.acnt_evlt_remn_indv_tot[].rmnd_qty` | String | 주(Shares) | 현재 잔고에 보유하고 있는 **남은 주식 수량**입니다. |
| `balance.acnt_evlt_remn_indv_tot[].pur_pric` | String | 원(KRW) | 해당 종목의 주당 **평균 매입 단가**입니다. (수수료 및 부대비용 등이 산입될 수 있습니다.) |
| `balance.acnt_evlt_remn_indv_tot[].cur_prc` | String | 원(KRW) | 해당 주식 종목의 실시간 또는 당일 종가 기준 **시장 현재가**입니다. |
| `balance.acnt_evlt_remn_indv_tot[].evltv_prft` | String | 원(KRW) | 해당 개별 종목의 **평가 손익액**입니다. (`(현재가 - 매입단가) * 보유수량` 으로 산출되는 미실현 손익입니다.) |
| `balance.acnt_evlt_remn_indv_tot[].prft_rt` | String | 퍼센트(%) | 해당 종목의 개별 매입단가 대비 현재가 등락 비율인 **개별 수익률**입니다. 소수점 2자리 형식입니다. |
| `balance.error` | String | 없음 | 계좌 순회 도중 해당 특정 계좌의 잔고 조회 처리 중 통신/API 수준의 에러가 발생한 경우의 사유입니다. (오류 발생 시에만 제한적으로 포함) |

---

## 3. 예외 및 오류 발생 입출력 명세

Kiwoom CLI는 프로그램 실행 도중 일어나는 에러 유형을 파악하여 올바른 오류 출력 메시지와 운영체제 종료 코드(Exit Code)를 전달하도록 처리합니다.

### [케이스 3-A] 설정되지 않았거나 존재하지 않는 잘못된 계좌 별칭(Alias) 지정 시
사용자가 `--account / -a` 옵션으로 전달한 별칭이 `config.json` 파일 내에 정의되어 있지 않은 경우에 해당합니다.

* **입력 명령어 (Text 포맷)**:
  ```bash
  kiwoom -a invalid_alias balance
  ```
* **출력 결과 (Text 포맷)**: *(종료 코드: 1)*
  ```text
  Error: Account invalid_alias not found in configuration.
  ```
* **입력 명령어 (JSON 포맷)**:
  ```bash
  kiwoom -a invalid_alias balance -f json
  ```
* **출력 결과 (JSON 포맷)**: *(종료 코드: 1)*
  ```json
  {"error": "Account invalid_alias not found in configuration."}
  ```

---

### [케이스 3-B] 환경 설정 파일 (`config.json`)을 전혀 찾을 수 없거나 읽을 수 없을 때
CLI를 처음 구동하였거나 지정된 `--config-dir` 경로 내에 유효한 설정 파일이 누락된 경우에 발생합니다.

* **입력 명령어 (Text 포맷)**:
  ```bash
  kiwoom balance
  ```
* **출력 결과 (Text 포맷)**: *(종료 코드: 1)*
  ```text
  Error: 설정된 계좌 별칭이 없거나 config.json을 찾을 수 없습니다.
  ```
* **입력 명령어 (JSON 포맷)**:
  ```bash
  kiwoom balance -f json
  ```
* **출력 결과 (JSON 포맷)**: *(종료 코드: 1)*
  ```json
  {"error": "설정된 계좌 별칭이 없거나 config.json을 찾을 수 없습니다."}
  ```

---

### [케이스 3-C] 계좌는 정의되어 있으나 API 서버 및 통신 과정에서 오류가 발생했을 때 (단일 계좌 조회 시)
인증 토큰 갱신 실패, 인터넷 연결 단절, 또는 키움증권 OpenAPI 서버 측의 장애(예: 500 Server Error) 발생 시의 상황입니다.

* **입력 명령어 (Text 포맷)**:
  ```bash
  kiwoom -a mh_default balance
  ```
* **출력 결과 (Text 포맷)**: *(종료 코드: 1)*
  ```text
  Error: 500 Server Error: Internal Server Error for url: https://api.kiwoom.com/api/dostk/acnt
  ```
* **입력 명령어 (JSON 포맷)**:
  ```bash
  kiwoom -a mh_default balance -f json
  ```
* **출력 결과 (JSON 포맷)**: *(종료 코드: 1)*
  ```json
  {"error": "500 Server Error: Internal Server Error for url: https://api.kiwoom.com/api/dostk/acnt"}
  ```

---

### [케이스 3-D] 다중 계좌 순회 조회 중 일부 계좌에서만 통신 오류가 발생했을 때
특정 별칭을 한정하지 않고 **전체 계좌 목록을 조회(`kiwoom balance`)**하는 중에, 일부 계좌만 토큰 오류나 500 에러 등의 장애가 발생한 케이스입니다.

* **동작 특징**:
  Kiwoom CLI는 다중 조회 시 **개별 에러 격리** 원칙을 고수합니다. 특정 계좌에서 에러가 발생하더라도 프로그램 전체를 즉시 중단(Crash)하지 않고, 해당 계좌의 출력 값에만 에러 속성을 채운 뒤 **정상 계좌들의 결과를 종합하여 온전히 결과를 출력**합니다. 최종 프로세스의 종료 코드는 정상 수행을 뜻하는 `0`으로 처리됩니다.
* **입력 명령어 (JSON 포맷)**:
  ```bash
  kiwoom balance -f json
  ```
* **출력 결과 (JSON 포맷)**: *(종료 코드: 0)*
  ```json
  [
    {
      "account": "mh_default",
      "acct_no": "1234567810",
      "balance": {
        "tot_pur_amt": "10000000",
        "tot_evlt_amt": "12500000",
        "tot_evlt_pl": "2500000",
        "tot_prft_rt": "25.00",
        "prsm_dpst_aset_amt": "15230000",
        "acnt_evlt_remn_indv_tot": [
          {
            "stk_cd": "A005930",
            "stk_nm": "삼성전자",
            "rmnd_qty": "100",
            "pur_pric": "70000",
            "cur_prc": "75000",
            "evltv_prft": "500000",
            "prft_rt": "7.14"
          }
        ]
      }
    },
    {
      "account": "mh_sub",
      "acct_no": "mh_sub",
      "balance": {
        "error": "500 Server Error: Internal Server Error for url: https://api.kiwoom.com/api/dostk/acnt"
      }
    }
  ]
  ```

