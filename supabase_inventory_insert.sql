-- Supabase SQL Editor에서 최초 1회 실행
-- 기존 엑셀(Inventory 시트) 재고 데이터 + supplier_email = ibk6895@gmail.com

insert into inventory (row_order, item_code, item_name, spec, unit, current_stock, safety_stock, supplier_email)
values
  (1, 'ING001', '도우볼', '220g', '개', 200, 180, 'ibk6895@gmail.com'),
  (2, 'ING002', '토마토소스', '3kg', '팩', 22, 20, 'ibk6895@gmail.com'),
  (3, 'ING003', '모짜렐라치즈', '2kg', '봉', 16, 18, 'ibk6895@gmail.com'),
  (4, 'ING004', '페퍼로니', '1kg', '팩', 15, 12, 'ibk6895@gmail.com'),
  (5, 'ING005', '베이컨', '1kg', '팩', 12, 10, 'ibk6895@gmail.com'),
  (6, 'ING006', '양파', '5kg', '봉', 14, 12, 'ibk6895@gmail.com'),
  (7, 'ING007', '피망', '5kg', '봉', 10, 8, 'ibk6895@gmail.com'),
  (8, 'ING008', '양송이버섯', '2.5kg', '캔', 9, 6, 'ibk6895@gmail.com'),
  (9, 'ING009', '블랙올리브', '3kg', '캔', 9, 8, 'ibk6895@gmail.com'),
  (10, 'ING010', '스위트콘', '3kg', '캔', 9, 5, 'ibk6895@gmail.com');
