# Vercel Environment Variables 설정 가이드

재고·메일 서비스를 Vercel에 배포할 때 **Environment Variables**에 아래 변수를 입력하는 방법입니다.

---

## 1. Vercel에서 환경 변수 입력 위치

1. [Vercel](https://vercel.com) 로그인 후 해당 프로젝트 선택
2. 상단 **Settings** 클릭
3. 왼쪽 메뉴에서 **Environment Variables** 클릭
4. **Key**와 **Value**를 입력한 뒤 **Save** (아래 표 참고)

---

## 2. 입력할 변수 목록

| Key (변수명) | Value (입력값) | 필수 | 비고 |
|--------------|----------------|------|------|
| `INVENTORY_SENDER_EMAIL` | 발신용 Gmail 주소 | ✅ | 그대로 입력 |
| `INVENTORY_SENDER_PASSWORD` | Gmail 앱 비밀번호 16자 | ✅ | 공백 없이 붙여서 입력 |
| `SUPABASE_URL` | Supabase 프로젝트 URL | (권장) | 이메일 발송 이력 저장용 |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Service Role Key | (권장) | 위와 함께 설정 시 발송 이력이 DB에 저장됨 |

**담당자 이메일(수신 주소)**은 환경 변수가 아니라 **웹 페이지 상단의 "담당자 이메일" 입력란**에서 입력합니다.

**Supabase (Vercel 배포 시 권장)**  
Vercel은 파일 시스템이 읽기 전용이라 (1) 재고 저장·(2) 발송 이력 저장이 불가합니다. **SUPABASE_URL**과 **SUPABASE_SERVICE_ROLE_KEY**를 설정하면 둘 다 Supabase에 저장됩니다.  
1. `supabase_email_history.sql` → SQL Editor에서 실행 (발송 이력 테이블)  
2. `supabase_inventory.sql` → SQL Editor에서 실행 (재고 테이블)  
3. 로컬에서 한 번만 `python seed_inventory_from_excel.py` 실행 → 엑셀 재고 데이터를 Supabase로 넣기 (선택)

---

## 3. 각 변수별 입력 방법

### INVENTORY_SENDER_EMAIL

- **입력 예**: `byw004422@gmail.com`
- **설명**: 재고 부족 알림 메일을 **보내는** Gmail 주소
- **입력 방법**: 사용하는 Gmail 주소를 그대로 입력 (따옴표 없이)

---

### INVENTORY_SENDER_PASSWORD

- **입력 예**: `abcdefghijklmnop` (16자, 공백 없음)
- **설명**: 위 Gmail 계정의 **앱 비밀번호**. 일반 로그인 비밀번호가 아님.
- **입력 방법**:
  1. [Google 계정](https://myaccount.google.com) → **보안**
  2. **2단계 인증**이 켜져 있어야 함 (없으면 먼저 활성화)
  3. **앱 비밀번호** 메뉴 → 앱 선택(예: 메일), 기기 선택 → **생성**
  4. 표시되는 **16자리 비밀번호**를 복사
  5. Vercel의 Value 란에 **공백 없이** 붙여넣기 (예: `abcd efgh ijkl mnop` → `abcdefghijklmnop`)

---

## 4. 입력 예시 (한눈에)

| Key | Value |
|-----|--------|
| `INVENTORY_SENDER_EMAIL` | `byw004422@gmail.com` |
| `INVENTORY_SENDER_PASSWORD` | `여기에_앱비밀번호_16자_공백없이` |

- **Environment**는 **Production**, **Preview**, **Development** 중 필요한 것에 체크 (보통 Production만 체크해도 됨)
- 저장 후 재배포하면 새 환경 변수가 적용됩니다.
- 수신 이메일(담당자 이메일)은 **HTML 페이지 상단 입력란**에서 설정하므로 Vercel 환경 변수에 넣지 않습니다.

---

## 5. 주의사항

- **INVENTORY_SENDER_PASSWORD**는 GitHub/코드에 절대 올리지 마세요. Vercel 화면에서만 입력합니다.
- 앱 비밀번호는 16자이며, Google이 표시할 때 공백으로 나눠 주는 경우가 있으니 **Vercel에는 공백 없이** 입력하세요.
- 값을 수정한 뒤에는 **Redeploy** 해야 반영됩니다.
