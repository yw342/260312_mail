# -*- coding: utf-8 -*-
"""
재고 웹 입력·확인 및 부족 시 메일 발송
- 보내는 사람: byw004422@gmail.com
- 받는 사람: HTML 페이지 담당자 이메일 입력란
"""
import os
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import Flask, render_template, request, jsonify, redirect, url_for

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

import inventory_alert as alert

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
EXCEL_PATH = Path(os.environ.get("INVENTORY_EXCEL_PATH", str(BASE_DIR / "domino_inventory_training.xlsx")))
# 이메일 발송 이력: Supabase 사용 시 DB, 미설정 시 파일
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", os.environ.get("SUPABASE_KEY", "")).strip()
USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY)

if not USE_SUPABASE:
    if os.environ.get("VERCEL"):
        EMAIL_HISTORY_PATH = Path("/tmp/email_history.json")
    else:
        EMAIL_HISTORY_PATH = BASE_DIR / "email_history.json"
EMAIL_THRESHOLD_HOURS = 1

_supabase_client = None

def _get_supabase():
    if not USE_SUPABASE:
        return None
    global _supabase_client
    if _supabase_client is None:
        from supabase import create_client
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client


def _load_email_history_file():
    if USE_SUPABASE:
        return []
    path = EMAIL_HISTORY_PATH
    if not path.is_file():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_email_history_file(records):
    if USE_SUPABASE:
        return
    with open(EMAIL_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(records[-500:], f, ensure_ascii=False, indent=2)


def load_email_history():
    """이메일 발송 이력 로드 (Supabase 또는 파일)."""
    if USE_SUPABASE:
        try:
            sb = _get_supabase()
            r = sb.table("email_send_history").select("sent_at,to_email,item_codes,item_names").order("sent_at", desc=True).limit(500).execute()
            rows = r.data or []
            return [
                {"sent_at": x.get("sent_at"), "to": x.get("to_email"), "item_codes": x.get("item_codes") or [], "item_names": x.get("item_names") or []}
                for x in rows
            ]
        except Exception:
            return []
    return _load_email_history_file()


def get_item_codes_sent_within_hours(hours=1):
    """지정 시간(기본 1시간) 내 발송된 품목의 품목코드 set 반환."""
    records = load_email_history()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    codes = set()
    for r in records:
        try:
            sent_at = datetime.fromisoformat(r.get("sent_at", "").replace("Z", "+00:00"))
            if sent_at.tzinfo is None:
                sent_at = sent_at.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        if sent_at >= cutoff:
            for code in r.get("item_codes") or []:
                if code:
                    codes.add(str(code).strip())
    return codes


def append_email_record(to_email, items):
    """발송 이력에 한 건 추가 (Supabase 또는 파일)."""
    item_codes = [str(i.get("품목코드") or "").strip() for i in items if i.get("품목코드")]
    item_names = [str(i.get("재료명") or "").strip() for i in items]
    sent_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    if USE_SUPABASE:
        try:
            sb = _get_supabase()
            sb.table("email_send_history").insert({
                "sent_at": sent_at,
                "to_email": to_email,
                "item_codes": item_codes,
                "item_names": item_names,
            }).execute()
        except Exception:
            pass
        return
    records = _load_email_history_file()
    records.append({"sent_at": sent_at, "to": to_email, "item_codes": item_codes, "item_names": item_names})
    _save_email_history_file(records)


def get_email_history_for_display(limit=50):
    """하단 이력 표시용. 최근 limit건."""
    records = load_email_history()
    out = []
    for r in (records[:limit] if USE_SUPABASE else reversed(records[-limit:])):
        try:
            sent_at = r.get("sent_at", "")
            if sent_at:
                dt = datetime.fromisoformat(sent_at.replace("Z", "+00:00"))
                sent_at = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            pass
        out.append({
            "sent_at": sent_at,
            "to": r.get("to") or r.get("to_email", ""),
            "item_names": r.get("item_names") or [],
        })
    return out


def _num_display(val):
    """소수 부분이 0이면 정수로, 아니면 그대로 반환 (화면 표시용)."""
    if val is None or val == "":
        return val
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        try:
            if val == int(val):
                return int(val)
        except (ValueError, OverflowError):
            pass
        return val
    return val


def get_inventory_list():
    """엑셀에서 재고 목록을 읽어 웹용 리스트로 반환 (row_idx는 엑셀 1-based 행)."""
    data_rows, col = alert.load_inventory(EXCEL_PATH)
    if not col:
        return []
    idx_code = col.get("품목코드", -1)
    idx_name = col.get("재료명", -1)
    idx_spec = col.get("규격", -1)
    idx_unit = col.get("단위", -1)
    idx_current = col.get("현재재고", col.get("현재 재고", -1))
    idx_safety = col.get("안전재고", col.get("안전 재고", -1))
    idx_status = col.get("상태", -1)
    idx_email = col.get("거래처이메일", col.get("이메일", -1))

    def v(row, i):
        if i < 0 or i >= len(row):
            return ""
        x = row[i]
        if x is None:
            return ""
        return str(x).strip() if not isinstance(x, (int, float)) else x

    sent_within_hour = get_item_codes_sent_within_hours(EMAIL_THRESHOLD_HOURS)
    result = []
    for i, row in enumerate(data_rows):
        excel_row = i + 2  # 1-based, row 1 = header
        raw_spec = v(row, idx_spec)
        raw_current = v(row, idx_current)
        raw_safety = v(row, idx_safety)
        code = v(row, idx_code)
        result.append({
            "row": excel_row,
            "품목코드": code,
            "재료명": v(row, idx_name),
            "규격": _num_display(raw_spec) if isinstance(raw_spec, (int, float)) else raw_spec,
            "단위": v(row, idx_unit),
            "현재재고": _num_display(raw_current) if isinstance(raw_current, (int, float)) else raw_current,
            "안전재고": _num_display(raw_safety) if isinstance(raw_safety, (int, float)) else raw_safety,
            "상태": v(row, idx_status),
            "거래처이메일": v(row, idx_email),
            "이메일_발송여부": "1시간 내 발송" if (code and str(code).strip() in sent_within_hour) else "-",
        })
    return result


def update_excel_current_stock(updates):
    """updates: [ {"row": 2, "현재재고": 120}, ... ] → 엑셀 해당 행의 현재재고 컬럼 수정."""
    import openpyxl
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=False)
    if "Inventory" not in wb.sheetnames:
        wb.close()
        return False
    ws = wb["Inventory"]
    header = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
    col_current = None
    for i, h in enumerate(header):
        if h and ("현재재고" in str(h) or "현재 재고" in str(h)):
            col_current = i + 1
            break
    if col_current is None:
        wb.close()
        return False
    for u in updates:
        row = u.get("row")
        val = u.get("현재재고")
        if row is not None and val is not None:
            try:
                n = float(val)
                ws.cell(row=int(row), column=col_current, value=n)
            except (TypeError, ValueError):
                ws.cell(row=int(row), column=col_current, value=val)
    wb.save(EXCEL_PATH)
    wb.close()
    return True


def get_dashboard(items):
    """재고 목록에서 대시보드용 집계 (총 품목, 정상, 부족, 부족 품목명)."""
    total = len(items)
    low_stock_names = []
    for it in items:
        try:
            current = float(it.get("현재재고") or 0)
            safety = float(it.get("안전재고") or 0)
        except (TypeError, ValueError):
            current, safety = 0, 0
        if current < safety:
            low_stock_names.append(it.get("재료명") or "-")
    low_count = len(low_stock_names)
    return {
        "total": total,
        "normal_count": total - low_count,
        "low_stock_count": low_count,
        "low_stock_names": low_stock_names,
    }


@app.route("/")
def index():
    items = get_inventory_list()
    dashboard = get_dashboard(items)
    email_history = get_email_history_for_display(50)
    return render_template("index.html", items=items, dashboard=dashboard, email_history=email_history)


def check_and_send_alert(recipient_email):
    """저장된 엑셀 기준으로 재고 부족 확인 후 담당자(recipient_email)에게 메일 발송. 1시간 내 발송한 품목은 제외."""
    if not recipient_email or "@" not in str(recipient_email).strip():
        return False, 0, "담당자 이메일을 입력하세요."
    recipient_email = str(recipient_email).strip()
    if not alert.SENDER_PASSWORD:
        return False, 0, "INVENTORY_SENDER_PASSWORD 환경 변수(또는 .env) 설정 필요"
    try:
        data_rows, col = alert.load_inventory(EXCEL_PATH)
        if not col:
            return False, 0, "Inventory 시트 헤더 없음"
        low_stock = alert.get_low_stock_items(data_rows, col)
        if not low_stock:
            return False, 0, None
        sent_recently = get_item_codes_sent_within_hours(EMAIL_THRESHOLD_HOURS)
        low_stock_to_send = [x for x in low_stock if (x.get("품목코드") or "").strip() not in sent_recently]
        if not low_stock_to_send:
            return False, 0, "1시간 내 발송된 품목만 있어 이번에는 발송하지 않았습니다."
        subject, body = alert.build_email_body(
            recipient_email, low_stock_to_send, alert.SENDER_EMAIL, all_to_one=True
        )
        alert.send_mail(
            recipient_email, subject, body,
            alert.SENDER_EMAIL, alert.SENDER_PASSWORD
        )
        append_email_record(recipient_email, low_stock_to_send)
        return True, len(low_stock_to_send), None
    except Exception as e:
        return False, 0, str(e)


@app.route("/save", methods=["POST"])
def save():
    data = request.get_json(force=True, silent=True) or request.form
    if not data:
        return jsonify({"ok": False, "message": "데이터 없음"}), 400
    updates = data.get("updates") if isinstance(data, dict) else []
    if not updates:
        return jsonify({"ok": False, "message": "updates 배열 필요"}), 400
    recipient_email = (data.get("recipient_email") or "").strip() if isinstance(data, dict) else ""
    try:
        update_excel_current_stock(updates)
        email_sent, alert_count, alert_error = check_and_send_alert(recipient_email)
        res = {"ok": True, "email_sent": email_sent, "alert_count": alert_count}
        if alert_error and email_sent is False and alert_count == 0:
            res["alert_error"] = alert_error
        if email_sent:
            res["to"] = recipient_email
        return jsonify(res)
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500


@app.route("/send-alert", methods=["POST"])
def send_alert():
    """재고 부족 확인 후 HTML에서 받은 담당자 이메일로 메일 발송."""
    data = request.get_json(force=True, silent=True) or request.form or {}
    recipient_email = (data.get("recipient_email") or "").strip()
    email_sent, alert_count, error = check_and_send_alert(recipient_email)
    if error and not email_sent:
        return jsonify({"ok": False, "message": error}), 400
    if not email_sent:
        return jsonify({"ok": True, "sent": 0, "message": "재고 부족 품목 없음"})
    return jsonify({"ok": True, "sent": 1, "count": alert_count, "to": recipient_email})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
