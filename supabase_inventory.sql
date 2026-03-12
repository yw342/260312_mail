-- Supabase 대시보드 → SQL Editor에서 실행
-- 재고 품목 테이블 (Vercel 등에서 Excel 대신 사용, 거래처 이메일 포함)

create table if not exists inventory (
  id uuid primary key default gen_random_uuid(),
  row_order int not null default 0,
  item_code text not null default '',
  item_name text not null default '',
  spec text not null default '',
  unit text not null default '',
  current_stock numeric not null default 0,
  safety_stock numeric not null default 0,
  supplier_email text not null default ''
);

create index if not exists idx_inventory_row_order on inventory (row_order);

comment on column inventory.item_code is '품목코드';
comment on column inventory.item_name is '재료명';
comment on column inventory.spec is '규격';
comment on column inventory.unit is '단위';
comment on column inventory.current_stock is '현재재고';
comment on column inventory.safety_stock is '안전재고';
comment on column inventory.supplier_email is '거래처이메일';

-- 기존 엑셀 데이터를 옮길 때는 아래 형식으로 INSERT (예시)
-- insert into inventory (row_order, item_code, item_name, spec, unit, current_stock, safety_stock, supplier_email)
-- values (1, 'ING001', '도우볼', '220g', '개', 120, 180, 'ibk6895@gmail.com');
