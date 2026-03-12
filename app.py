# -*- coding: utf-8 -*-
"""
재고 웹 입력·확인 및 부족 시 메일 발송
- 보내는 사람: byw004422@gmail.com
- 받는 사람: ibk6895@gmail.com
"""
import os
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

    result = []
    for i, row in enumerate(data_rows):
        excel_row = i + 2  # 1-based, row 1 = header
        raw_spec = v(row, idx_spec)
        raw_current = v(row, idx_current)
        raw_safety = v(row, idx_safety)
        result.append({
            "row": excel_row,
            "품목코드": v(row, idx_code),
            "재료명": v(row, idx_name),
            "규격": _num_display(raw_spec) if isinstance(raw_spec, (int, float)) else raw_spec,
            "단위": v(row, idx_unit),
            "현재재고": _num_display(raw_current) if isinstance(raw_current, (int, float)) else raw_current,
            "안전재고": _num_display(raw_safety) if isinstance(raw_safety, (int, float)) else raw_safety,
            "상태": v(row, idx_status),
            "거래처이메일": v(row, idx_email),
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
    return render_template("index.html", items=items, dashboard=dashboard)


def check_and_send_alert():
    """저장된 엑셀 기준으로 재고 부족 확인 후 담당자(ibk6895@gmail.com)에게 메일 자동 발송. (sent, count, error) 반환."""
    if not alert.SENDER_PASSWORD:
        return False, 0, ".env에 INVENTORY_SENDER_PASSWORD 설정 필요"
    try:
        data_rows, col = alert.load_inventory(EXCEL_PATH)
        if not col:
            return False, 0, "Inventory 시트 헤더 없음"
        low_stock = alert.get_low_stock_items(data_rows, col)
        if not low_stock:
            return False, 0, None
        subject, body = alert.build_email_body(
            alert.RECIPIENT_EMAIL, low_stock, alert.SENDER_EMAIL, all_to_one=True
        )
        alert.send_mail(
            alert.RECIPIENT_EMAIL, subject, body,
            alert.SENDER_EMAIL, alert.SENDER_PASSWORD
        )
        return True, len(low_stock), None
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
    try:
        update_excel_current_stock(updates)
        email_sent, alert_count, alert_error = check_and_send_alert()
        res = {"ok": True, "email_sent": email_sent, "alert_count": alert_count}
        if alert_error and email_sent is False and alert_count == 0:
            res["alert_error"] = alert_error
        return jsonify(res)
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500


@app.route("/send-alert", methods=["POST"])
def send_alert():
    """재고 부족 확인 후 ibk6895@gmail.com 으로 메일 발송 (발신: byw004422@gmail.com)."""
    email_sent, alert_count, error = check_and_send_alert()
    if error and not email_sent:
        return jsonify({"ok": False, "message": error}), 400
    if not email_sent:
        return jsonify({"ok": True, "sent": 0, "message": "재고 부족 품목 없음"})
    return jsonify({"ok": True, "sent": 1, "count": alert_count, "to": alert.RECIPIENT_EMAIL})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
