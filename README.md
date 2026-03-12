# 재고 부족 시 담당자 메일 발송 자동화

엑셀 재고 시트를 읽어 **현재재고 < 안전재고** 인 품목을 찾고, 담당자(ibk6895@gmail.com)에게 발주 요청 메일을 보내는 웹·스크립트입니다.

- **발신**: `byw004422@gmail.com` · **수신**: `ibk6895@gmail.com` (환경변수로 변경 가능)
- **엑셀**: `domino_inventory_training.xlsx` → **Inventory** 시트
- **웹**: 재고 입력·대시보드·저장 시 재고 부족이면 자동 메일 발송

---

## 보안 (필수)

- **`.env` 파일은 절대 GitHub 등 저장소에 올리지 마세요.** 비밀번호가 포함됩니다.
- 배포(Vercel 등) 시에는 **환경 변수**로 `INVENTORY_SENDER_PASSWORD`, `INVENTORY_RECIPIENT_EMAIL` 등을 설정하세요.

---

## 사용 방법

### 1. Python 설치

[python.org](https://www.python.org/downloads/)에서 Python 3.8 이상 설치 후, 터미널에서 다음 실행:

```bash
pip install -r requirements.txt
```

(선택) `.env` 파일로 비밀번호를 관리하려면:

```bash
pip install python-dotenv
```

### 2. Gmail 앱 비밀번호 설정

Gmail로 발송하려면 **앱 비밀번호**가 필요합니다.

1. Google 계정 → **보안** → **2단계 인증** 활성화
2. **보안** → **앱 비밀번호**에서 새 앱 비밀번호 생성
3. 생성된 16자리 비밀번호를 복사

### 3. 비밀번호 넣기

**방법 A – 환경변수 (권장)**

- Windows PowerShell (한 번만):
  ```powershell
  $env:INVENTORY_SENDER_PASSWORD = "여기에_앱_비밀번호_16자"
  ```
- 그 다음 같은 터미널에서:
  ```powershell
  python inventory_alert.py
  ```

**방법 B – .env 파일**

1. `.env.example`을 복사해 `.env` 생성
2. `.env`에서 `INVENTORY_SENDER_PASSWORD=여기에_앱_비밀번호` 로 수정
3. `pip install python-dotenv` 후 `python inventory_alert.py` 실행

### 4. 실행

```bash
cd c:\Users\SD2-18\Downloads\0312
python inventory_alert.py
```

- 재고 부족 품목이 있으면 → 거래처이메일별로 묶어서 메일 발송
- 재고 부족 품목이 없으면 → 메일은 보내지 않고 종료

---

## 엑셀 구조 (Inventory 시트)

| 컬럼 예시       | 설명           |
|----------------|----------------|
| 현재재고       | 현재 재고 수량 |
| 안전재고       | 안전 재고 기준 |
| 상태           | "발주 필요"면 부족로 간주 |
| 거래처이메일   | 메일 수신 주소 |
| 담당자알림메시지 | 메일 본문에 들어갈 문구 |

스크립트는 **상태**가 `발주 필요`인 행을 재고 부족으로 보고, 해당 행의 **거래처이메일**로 발송합니다.

---

## 외부 전송 시 유의사항

- 발신 주소 `byw004422@gmail.com`로 **외부** 수신자에게 메일이 전송됩니다.
- Gmail 일일 발송 한도가 있으므로, 수신자가 많으면 배치로 나누어 실행하는 것이 좋습니다.
- `.env` 파일과 앱 비밀번호는 외부에 공유하거나 저장소에 올리지 마세요.

---

## 정기 실행 (선택)

- **Windows 작업 스케줄러**: 매일 특정 시간에 `python inventory_alert.py` 실행
- **외부 서버**에 올려서 cron 등으로 주기 실행 가능

엑셀 경로를 바꾸려면 환경변수 `INVENTORY_EXCEL_PATH`에 전체 경로를 설정하면 됩니다.

---

## GitHub / 배포

- 저장소: [https://github.com/yw342/260312_mail](https://github.com/yw342/260312_mail)
- Vercel 등에 배포할 때는 환경 변수에 `INVENTORY_SENDER_EMAIL`, `INVENTORY_SENDER_PASSWORD`, `INVENTORY_RECIPIENT_EMAIL`을 설정한 뒤 배포하세요.
