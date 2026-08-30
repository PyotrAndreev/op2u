updated: 2026-05-03

# к Среде

## Серёга, Андрей
- прочитать [файл о конкурентах](./docs/agent_analysis/op2u_competitor_analysis.pdf)
- запустить OPPORTUNITY RADAR на ваших данных
    1. `git switch petr`
    2. добавить в [usr файл](./usr/profile.md) информацию о вас: био, цели, увлечения, выжимка по вам с вашей LLM web формы
    3. запустить в codex: `Learn all the project and follow instractions in op2u/docs/agent_prompts/find_opps.md`
    4. просмотреть возможности найденные под вас в [файле](./docs/agent_analysis/opps_report.md)
    5. улыбнуться и начать действовать

## Серёга
- накидать архитектуру приложения (в Ср обсудим)

## Petr
- найти 3 простых, 3 средних, 3 сложных site-формы примера для тестов


# к Сб/Вс
## Все
- протестировать простые __PlayWrite__ сценарии (нет аунтификации):  
    - на входе URL
    - под каждый URL сегенерить JS код по заполнению форм
    - заполняет данные согласно пользователю
    - отправляет формы

## Petr
- улучшить `find_opps.md` prompts (критерии улучшения?)
- осуществить pipeline обработки usr data:
    - опрос + загрузка файлов
    - prompt парсинга файлов
    - сохранение в BD (?применить [AgentWiki](https://agentwiki.org/))
- убрать генерацию излишних файлов в `docs/agent_analysis`


# Good to do:
- сравнить потраченные токены: zeroshot (codex) vs. PlayWrite shot
