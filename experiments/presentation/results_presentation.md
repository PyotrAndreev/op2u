# op2u Opportunity Discovery
## Eval-driven auto-research

**Как превратить поиск возможностей из убедительного текста в воспроизводимый pipeline**

21 research run · 4 blinded comparisons · 180 model calls

---

# Цель эксперимента

> Максимизировать вероятность meaningful first action в течение 7 дней, а не количество релевантных ссылок.

Сильная рекомендация соединяет:

- устойчивые факты профиля;
- активную траекторию и текущий контекст;
- переиспользуемый актив;
- живую возможность;
- выполнимый следующий шаг.

Главный приоритет профиля: превратить **peermux / portable P2P development environments** в публичный технический проект с внешней валидацией.

---

# Что было построено

1. Dynamic profile interpretation
2. Trigger synthesis
3. Search planning
4. Broad discovery
5. Primary-source verification
6. Actionability analysis
7. Ranking and weekly allocation
8. Report and external judges

Каждый run сохранял prompts, inputs, web trace, candidates, verification, ranking, report, costs и judge outputs.

---

# Масштаб

| Показатель | Результат |
|---|---:|
| Research runs | 21 |
| Blinded comparisons | 4 |
| Persisted model calls | 180 |
| Subprocess time | 7 067.8 s |
| Provider-reported cost | $2.388421 |
| Controlled G2 repeats | 3 |
| Genuine hidden holdout | нет |

Исполнители и judges: **OpenAI Codex Luna / Terra**.

---

# Лестница вариантов

| Вариант | Добавленная способность |
|---|---|
| V0 | неизменённый baseline |
| V1 | dynamic profile state |
| V2 | trigger synthesis |
| V3 | bridge + actionability gate |
| V4 | persisted staged pipeline |
| V5 | pairwise ranking |
| V6 | evidence-grounded judges |
| V7 | constrained serendipity |
| G1–G3 | targeted failure-driven mutations |

Поздний вариант не считался автоматически лучшим.

---

# Baseline: убедительно, но небезопасно

V0 рекомендовал **NLnet как ACT_NOW**, хотя официальный call ещё не был открыт.

Также отсутствовали:

- точные source quotes;
- retrieval timestamps;
- надёжное разделение verified fact и inference;
- консервативный расчёт effort.

Все три judge-роли отклонили baseline.

**Finding:** качество прозы может скрывать hard factual failure.

---

# Что действительно помогло

- Явное разделение durable facts, current state, assets и unknowns.
- Trigger hypotheses до web search.
- Отдельная primary-source verification stage.
- Строгий `ACT_NOW` gate: live status + why now + low-friction action.
- Persisted intermediate artifacts.
- Blinded A/B в обоих порядках.

Но улучшение было **немонотонным**: V3 и V5 местами регрессировали относительно V2/V4.

---

# Главный failure mode: effort accounting

Ранние варианты смешивали три разных величины:

1. `first_action_minutes`;
2. `scheduled_this_week_minutes`;
3. `total_completion_effort_hours`.

В отчёте могло быть написано «2 часа первого шага», хотя выбранный portfolio фактически требовал 7–11 часов.

Исправление G2:

- суммировать верхние границы всех действий, назначенных на неделю;
- максимум 360 минут;
- deferred и MONITOR не должны незаметно потреблять attention budget.

---

# Search luck ≠ улучшение ranker

Полные повторы одного prompt находили совершенно разные opportunities:

- CFP;
- гранты;
- standards communities;
- residencies;
- open-source contribution paths.

Поэтому G2 сначала выглядел нестабильно.

Затем эксперимент был исправлен: один и тот же immutable candidate pool переиспользовался до `actionability`, а повторно запускались только `ranking` и `report`.

**Finding:** ranking mutation нельзя оценивать на новом случайном discovery pool.

---

# Оптимизационные поколения

## Generation 1

- Budget allocator убрал часть effort failures.
- Prompt-only claim ledger не был надёжно выполнен.
- Strict ACT_NOW улучшил liveness, но не недельный budget.

## Generation 2

Strict ACT_NOW + conservative weekly allocation.

- 3/3 controlled repeats без hard failures;
- upper-bound budgets: **150, 150, 165 минут**.

## Generation 3

Не улучшил evidence; G2 сохранился против G3 с **6/6 order-stable votes**.

---

# Provisional frontier: G2_M1

| Проверка | Результат |
|---|---|
| Hard-gate eligibility | 3/3 controlled repeats |
| Parent → child pairwise | 4 child votes, 2 ties, 0 losses |
| G2 vs G3_M3 | 6/6 за G2 |
| Weekly scheduled upper bound | 150–165 min |
| Evidence regression | hard regression не обнаружен |

Статус: **best observed, profile-scoped**, не доказанная универсальная сходимость.

---

# Evidence нельзя оставлять промпту

Дважды prompt требовал exact claim ledger — и дважды модель не выполнила contract полностью.

Поэтому production runner теперь fail-closed проверяет:

- exact `quote + URL + retrieved_at`;
- official-source marker;
- verification artifact hash;
- claim references для ACT_NOW status/deadline;
- shortlist limits;
- MONITOR effort = 0;
- weekly allocation ≤ 360 минут.

**Finding:** provenance — это schema/code invariant, а не пожелание в prompt.

---

# Как читать judge results

Нельзя брать простой median всех judge scores:

- judges владели разными dimensions;
- некоторые outputs оценивали только owned dimensions;
- evidence hard failure должен перекрывать высокий personalization score;
- часть A/B результатов была order-sensitive.

Надёжная иерархия:

1. hard gates;
2. role-owned dimensions;
3. repeat variance;
4. pairwise в обоих порядках;
5. score — только вместе с ролью и coverage.

---

# Ограничения

- Нет настоящего hidden holdout.
- Нет behavioral labels: opened → first action → submitted.
- E11 causal perturbations не запускались.
- Изменяющиеся live pages ограничивают exact replay.
- Standalone production prompt производен от G2, но пока не имеет отдельного live evaluation run.
- Следующий качественный шаг — пользовательская разметка 5–10 верхних рекомендаций.

---

# Итоговый discovery
## Улучшенный G2_M1, controlled result

Snapshot verification: **2 августа 2026**

Portfolio:

1. `ACT_NOW` — CANOPIE-HPC 2026
2. `PREPARE_NEXT` — Prototype Fund
3. `MONITOR` — Kotlin Foundation Grants

Недельный budget: **105–150 минут из 360**.

---

# 1. ACT_NOW — CANOPIE-HPC 2026

**Почему сейчас**

Официальный CFP был открыт и закрывается **14 августа 2026**.

> “Submission opens: June 10, 2026; Submission closes (hard deadline - no extensions): August 14th, 2026”

**Opportunity bridge**

peermux + reproducible portable environments + опыт в orchestration/distributed systems.

**Первый шаг: 45–60 минут**

Подготовить 150-word lightning-talk abstract, связывающий peermux с воспроизводимыми переносимыми окружениями.

Источник: [canopie-hpc.org/cfp](https://canopie-hpc.org/cfp/)

---

# 2. PREPARE_NEXT — Prototype Fund

Официальное следующее окно: **1 октября — 30 ноября 2026**.

> “Applications for class 03 start from October 1st, 2026 and are possible until November 30th, 2026.”

**Первый шаг: 60–90 минут**

Сделать одностраничный project concept:

- проблема;
- bounded prototype;
- open-source plan;
- ожидаемые пользователи;
- критерий внешней валидации.

Это подготовка, а не текущая заявка. Eligibility и project traction пока неизвестны.

Источник: [prototypefund.de](https://www.prototypefund.de/en/)

---

# 3. MONITOR — Kotlin Foundation Grants

> “Grant submissions are now closed.”

- Действий на этой неделе: **0 минут**.
- Дата нового окна не подтверждена.
- Kotlin-specific bridge для peermux пока не установлен.

Источник: [kotlinfoundation.org/grants](https://kotlinfoundation.org/grants/)

## Рекомендуемый план недели

1. CANOPIE abstract — 45–60 минут.
2. Prototype Fund one-pager — 60–90 минут.
3. Остаток attention budget — не заполнять слабыми рекомендациями.

**Итого: 105–150 минут.**
