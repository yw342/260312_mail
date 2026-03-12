-- Supabase 대시보드 → SQL Editor에서 실행
-- 이메일 발송 이력 테이블 (Vercel 등 서버리스에서 발송 이력 영구 저장)

create table if not exists email_send_history (
  id uuid primary key default gen_random_uuid(),
  sent_at timestamptz not null default now(),
  to_email text not null,
  item_codes jsonb not null default '[]',
  item_names jsonb not null default '[]'
);

-- 최근 발송 조회용 인덱스
create index if not exists idx_email_send_history_sent_at
  on email_send_history (sent_at desc);

-- RLS 사용 시 서비스 역할로 삽입/조회 가능하도록 (필요 시)
-- alter table email_send_history enable row level security;
-- create policy "Allow service role" on email_send_history for all using (true);
