-- PoC demo content for local/Supabase validation.

insert into contents (
  id,
  product_type,
  channel,
  target_customer,
  language,
  original_text
) values (
  '00000000-0000-0000-0000-000000000101',
  '투자상품',
  '앱 푸시',
  '30대 직장인',
  'ko',
  '지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요.'
) on conflict (id) do nothing;
