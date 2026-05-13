-- PoC seed data for JB SafeGrowth Agent MVP.
-- These examples are demo guidance snippets, not verified legal advice.

insert into regulation_docs (
  id,
  title,
  version,
  product_type,
  risk_categories,
  body,
  snippet,
  guideline_snippet
) values
(
  'doc-demo-001',
  '금융상품 광고 심사 가이드라인',
  'demo-v1',
  '투자상품',
  array['확정 수익 오인', '안정성 오인'],
  '투자성 상품 광고에서는 수익률을 확정적으로 표현하지 않아야 하며, 시장 상황에 따라 수익 또는 손실이 발생할 수 있음을 함께 안내해야 한다.',
  '투자성 상품 광고에서는 수익률을 확정적으로 표현하지 않아야 하며 손실 가능성을 함께 안내해야 합니다.',
  '수익률 확정 표현 금지'
),
(
  'doc-demo-002',
  '금융소비자 보호 가이드라인',
  'demo-v1',
  '투자상품',
  array['원금 보장 오인'],
  '원금 손실 가능성이 있는 상품은 원금 보장, 원금 걱정 없음, 손실 없음 등으로 오인될 수 있는 표현을 사용하지 않아야 한다.',
  '원금 손실 가능성이 있는 상품은 원금 보장 또는 원금 걱정이 없다는 취지로 안내하지 않아야 합니다.',
  '원금 손실 가능성 고지 필요'
),
(
  'doc-demo-003',
  '내부 통제 규정',
  'demo-v1',
  '공통',
  array['과장 표현'],
  '마케팅 커뮤니케이션은 보편적 혜택, 확정적 결과, 심의 누락으로 오인될 수 있는 표현을 사전에 점검하고 준법 심의 절차를 거쳐야 한다.',
  '마케팅 커뮤니케이션은 보편적 혜택, 확정적 결과, 심의 누락으로 오인되는 표현을 사전 점검해야 합니다.',
  '마케팅 문구 배포 전 준법 심의 필요'
)
on conflict (id) do update set
  title = excluded.title,
  version = excluded.version,
  product_type = excluded.product_type,
  risk_categories = excluded.risk_categories,
  body = excluded.body,
  snippet = excluded.snippet,
  guideline_snippet = excluded.guideline_snippet;
