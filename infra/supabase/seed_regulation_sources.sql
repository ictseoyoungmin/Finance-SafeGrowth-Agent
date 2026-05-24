insert into regulation_sources (id, name, source_type, product_type, default_risk_categories, active)
values
  ('11111111-1111-4111-8111-111111111111', '운영자 업로드', 'admin_upload', '공통', '{}', true),
  ('22222222-2222-4222-8222-222222222222', '데모 규정 seed', 'manual_seed', '투자상품', '{"확정 수익 오인","안정성 오인","원금 보장 오인","과장 표현"}', true)
on conflict (id) do nothing;

insert into regulation_sources (name, source_type, url, product_type, default_risk_categories, active)
values (
  '금감원 보도자료 RSS placeholder',
  'rss',
  'https://www.fss.or.kr/fss/bbs/B0000188/list.do?menuNo=200218',
  '공통',
  '{}',
  false
);
