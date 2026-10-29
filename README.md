Диагностика проблем со сроками доставки

* * *

* * *

* * *

* * *

* * *

* * *

* * *

* * *

* * *

* * *

* * *

* * *

* * *

* * *

* * *

* * *

* * *

[

](https://wiki.wb.ru/space/211/seara/page/2029/Diagnostika-problem-so-srokami-dostavki#stranica-prednaznachena-dlya-pervichnoy-diagnostiki-voprosov-po-srokam-dostavki.-cel----samostoyatelno-opredelit)Страница предназначена для первичной диагностики вопросов по срокам доставки. Цель — самостоятельно определить:
==========================================================================================================================================================================================================================================================================================================================

*   есть ли проблема в прогнозе;
    
*   на каком этапе и где она возникает;
    
*   можно ли объяснить большой срок фактическим движением заказа;
    
*   нужно ли передавать кейс команде сроков.
    

[

](https://wiki.wb.ru/space/211/seara/page/2029/Diagnostika-problem-so-srokami-dostavki#kak-provodit-diagnostiku)**Как проводить диагностику**
------------------------------------------------------------------------------------------------------------------------------------------------

Идём от общего к частному:

**1\. Временной ряд WH / FBS** → есть ли проблема, когда и на каком этапе она появилась.  
**2\. Дашборд по офисам** → какой офис / delivery type создаёт проблему.  
**3\. Детальный дашборд** → почему возникло отклонение: duration, base\_duration, calc\_type, route history.

**Важно:** большой срок ≠ ошибка прогноза. Если прогноз соответствует фактическому движению заказа, проблема может отсутствовать.

* * *

[

](https://wiki.wb.ru/space/211/seara/page/2029/Diagnostika-problem-so-srokami-dostavki#1.-vremennye-ryady-wh-i-fbs)**1\. Временные ряды WH и FBS**
=====================================================================================================================================================

**WH:** [https://bi.wb.ru/env/all/queries/145586](https://bi.wb.ru/env/all/queries/145586)  
**FBS:** [https://bi.wb.ru/env/all/queries/141024](https://bi.wb.ru/env/all/queries/141024)

Дашборды используются одинаково, но разделены из-за разного характерного времени T1.

Показывают по дням фактические и прогнозные **T1, T2, T3**, а также кумулятивные ошибки. Используются, чтобы понять:

*   действительно ли есть отклонение;
    
*   когда оно появилось;
    
*   на каком этапе;
    
*   разовая это аномалия или устойчивое изменение.
    

### [

](https://wiki.wb.ru/space/211/seara/page/2029/Diagnostika-problem-so-srokami-dostavki#kumulyativnye-oshibki)**Кумулятивные ошибки**

`T1 error = t1 - timestamp_src`  
`T2 error = t2 - timestamp_lm`  
`T3 error = t3 - timestamp_dst`

**Ошибка небольшая** → прогноз в целом соответствует фактическому движению заказа. Тогда нужно понять, почему сам факт большой.

**Ошибка большая** → смотрим, на каком этапе она впервые появляется. Например, ошибка может возникнуть на T1 и затем сохраняться до T3 — особенно это характерно для FBS.

### [

](https://wiki.wb.ru/space/211/seara/page/2029/Diagnostika-problem-so-srokami-dostavki#ne-zabyvaem-pro-cnt)**Не забываем про cnt**

T1/T2/T3 рассчитываются независимо. Поэтому всегда проверяйте `t1_cnt / t2_cnt / t3_cnt`, особенно на последних датах.

Например, если `orders_cnt = 100`, а `t3_cnt = 20`, T3 рассчитан только по 20 заказам, для которых уже существуют необходимые фактические и прогнозные значения.

Дни с ≤5 заказами сейчас не выводятся.

* * *

[

](https://wiki.wb.ru/space/211/seara/page/2029/Diagnostika-problem-so-srokami-dostavki#2.-oshibka-malenkaya-no-srok-bolshoy)**2\. Ошибка маленькая, но срок большой**
========================================================================================================================================================================

Это не обязательно проблема прогноза.

### [

](https://wiki.wb.ru/space/211/seara/page/2029/Diagnostika-problem-so-srokami-dostavki#bolshoy-t1)**Большой T1**

Для FBS продавец может действительно долго передавать товар — встречаются значения вплоть до ~100 часов.

Также проверьте выходные: дополнительные 24/48 часов могут реально присутствовать и в фактическом сроке.

### [

](https://wiki.wb.ru/space/211/seara/page/2029/Diagnostika-problem-so-srokami-dostavki#bolshoy-t2)**Большой T2**

Проверьте фактический маршрут.

Например, товар доставляется во Владивосток, но вместо ожидаемого локального склада фактически едет из Москвы. Тогда большой T2 объясняется маршрутом, а не ошибкой расчёта его длительности.

Если селлер утверждает, что товар есть на локальном складе:

1.  проверьте WH через `nminfo`;
    
2.  проверьте наличие в дашборде складов;
    
3.  если товар действительно есть, но локальный склад не выбирается, кейс относится к выбору склада / маршрутизации и его стоит передать дальше.
    

* * *

[

](https://wiki.wb.ru/space/211/seara/page/2029/Diagnostika-problem-so-srokami-dostavki#3.-oshibka-bolshaya)**3\. Ошибка большая**
====================================================================================================================================

Сначала посмотрите на прогнозные времена.

**Ровно 60 / 128 часов**, а также подозрительно одинаковые и округлённые значения часто указывают на заглушку.

Если причина не очевидна, переходим к разрезу по офисам.

* * *

[

](https://wiki.wb.ru/space/211/seara/page/2029/Diagnostika-problem-so-srokami-dostavki#4.-dashbord-po-ofisam)**4\. Дашборд по офисам**
=========================================================================================================================================

[https://bi.wb.ru/env/all/queries/145810](https://bi.wb.ru/env/all/queries/145810)

Показывает основные показатели в разрезе:

**delivery type × office**

Нужен, чтобы понять, является ли проблема общей или её создаёт конкретный офис / группа офисов.

Например:

*   один офис сильно портит общую картину;
    
*   WH работает нормально, а на FBS большие ошибки;
    
*   проблема возникает только у нескольких офисов.
    

После этого в детальный дашборд лучше передавать **конкретные проблемные офисы**, а не всю выборку.

`orders_cnt` содержит все прошедшие фильтры заказы, а T1/T2/T3 каждый рассчитывается на своей доступной подвыборке.

Название офиса берётся из `office_location` по `order_src_office_id = id`.

* * *

[

](https://wiki.wb.ru/space/211/seara/page/2029/Diagnostika-problem-so-srokami-dostavki#5.-detalnyy-dashbord)**5\. Детальный дашборд**
========================================================================================================================================

[https://bi.wb.ru/env/all/queries/139978](https://bi.wb.ru/env/all/queries/139978)

Загрузка 3–4 минуты — нормальное поведение.

Дашборд позволяет перейти к конкретным:

**nm\_id × supplier × office × delivery type × src → LM → dst**

Основное, что здесь проверяем:

*   фактические и прогнозные длительности;
    
*   `duration`;
    
*   `base_duration`;
    
*   `calc_type`;
    
*   `fact_cnt / pred_cnt / error_cnt`;
    
*   наличие route history.
    

### [

](https://wiki.wb.ru/space/211/seara/page/2029/Diagnostika-problem-so-srokami-dostavki#duration-i-base_duration)**Duration и base\_duration**

`base_duration` — базовая рассчитанная длительность.  
`duration` — длительность, используемая в итоговом прогнозе.

Если `base_duration` адекватен, а `duration` — нет, смотрим, что изменило значение.

Характерные случаи:

*   разница **24/48 часов** → проверить выходные дни;
    
*   слишком большой коэффициент;
    
*   заглушка.
    

### [

](https://wiki.wb.ru/space/211/seara/page/2029/Diagnostika-problem-so-srokami-dostavki#calc-type)**Calc type**

Для `calc_type` существует отдельная таблица расшифровки.

Для **T1** `**calc_type != 1**` **требует дополнительной проверки**. Для T2, например, `calc_type = 4` может быть нормой.

Также стоит обратить внимание, если `calc_type` резко меняется во времени.

Если `calc_type` отсутствует, это **не обязательно ошибка**. Возможные причины:

*   нет истории;
    
*   не совпала маршрутная пара или время;
    
*   изменился маршрут;
    
*   длительность не была рассчитана / записана;
    
*   заказ ещё не доехал.
    

Можно ориентироваться на преобладающий `calc_type` для аналогичных заказов данного продавца / NM.

* * *

[

](https://wiki.wb.ru/space/211/seara/page/2029/Diagnostika-problem-so-srokami-dostavki#6.-tipovye-scenarii)**6\. Типовые сценарии**
======================================================================================================================================

|   **Что видим**     |   **Возможная причина**     |   **Что делать**     |
| --- | --- | --- |
|   Большой срок, ошибка маленькая     |   Срок действительно большой     |   Проверить T1, маршрут, выходные     |
|   Большой T1 на FBS     |   Долгая передача селлером / выходные     |   Сверить с фактом     |
|   Большой T2     |   Длинный фактический маршрут     |   Проверить источник товара     |
|   Товар едет не с ожидаемого склада     |   Выбор склада / маршрутизация     |   Проверить наличие товара     |
|   Ошибка появляется на T1/T2/T3     |   Проблема конкретного этапа     |   Локализовать по офису и детальному дашу     |
|   60 / 128 ч. или одинаковые значения     |   Возможная заглушка     |   Проверить calc\_type и передать кейс     |
|   base\_duration нормальный, duration нет     |   Выходные / коэффициент / другой модификатор     |   Проверить преобразование     |
|   calc\_type скачет     |   Изменился способ расчёта     |   Проверить момент изменения     |
|   Факт изменился, прогноз нет     |   Прогноз не успел адаптироваться     |   Передать кейс     |
|   Мало заказов / заказ ещё не доехал     |   Недостаточно данных     |   Не делать вывод преждевременно     |

* * *

[

](https://wiki.wb.ru/space/211/seara/page/2029/Diagnostika-problem-so-srokami-dostavki#7.-kogda-peredavat-keys-dalshe)**7\. Когда передавать кейс дальше**
=============================================================================================================================================================

**Не требуется эскалация**, если большой срок объясняется фактом: длинным маршрутом, передачей товара продавцом, реальными выходными или недостаточным количеством данных.

**Передаём кейс**, если видно устойчивое расхождение прогноза и факта и удалось локализовать источник: этап, офис, маршрут, duration, calc\_type и т. п.

При передаче приложите:

*   supplier и NM;
    
*   delivery type;
    
*   период;
    
*   проблемный офис;
    
*   T1 / T2 / T3;
    
*   несколько характерных SRID;
    
*   fact и prediction;
    
*   duration / base\_duration;
    
*   calc\_type;
    
*   что уже было проверено.
    

**Хороший пример постановки:**

FBS, supplier X, NM Y, офис Z. С 12.10 вырос T2 error примерно до N часов. На остальных офисах изменения нет. На проблемных заказах duration = …, base\_duration = …, calc\_type = …. Примеры SRID: ….

* * *

[

](https://wiki.wb.ru/space/211/seara/page/2029/Diagnostika-problem-so-srokami-dostavki#tehnicheskie-nyuansy)**Технические нюансы**
=====================================================================================================================================

**Детальный дашборд.** Данные берутся из `srids_dist` и обогащаются историями `route1/2/3`. История подбирается на час создания заказа (`toStartOfHour(timestamp_created)`) и по соответствующей OSM-паре. Если история не найдена → `NO_HISTORY`.

Дашборд сохраняет в выборке SRID, даже если часть информации по ним отсутствует. Fact и prediction могут рассчитываться по разному числу заказов, поэтому учитывайте `fact_cnt / pred_cnt / error_cnt`.

**LM.** Сейчас в дашбордах используется фактический LM. Он может отличаться от LM, который алгоритм предполагал в момент создания заказа. Это ограничение текущей реализации, которое стоит учитывать в нетипичных случаях.

**Фильтры.** `-1` означает «использовать всё». В поле NM можно передать несколько значений через запятую с пробелом:

`123456, 234567, 345678`


WITH
    arrayFilter(
        x -> x != 0,
        arrayMap(x -> toInt64OrZero(trimBoth(x)), splitByRegexp('[,;\\s]+', '{{nm_id}}'))
    ) AS nm_ids_filter,

region_map AS (
    SELECT
        z4.osm_id AS order_dst_osm_id,
        z2.osm_id AS region_osm_id
    FROM wbx_data_mart.osm_zones AS z4
    ANY LEFT JOIN wbx_data_mart.osm_zones AS z3
        ON z4.parent_id = z3.osm_id AND z3.level = 3
    ANY LEFT JOIN wbx_data_mart.osm_zones AS z2
        ON z3.parent_id = z2.osm_id AND z2.level = 2
    WHERE z4.level = 4
),

raw AS (
    SELECT
        s.delivery_type,
        s.order_src_office_id,
        s.order_dst_osm_id,
        s.timestamp_created,
        s.timestamp_src,
        s.timestamp_lm,
        s.timestamp_dst,
        s.t1,
        s.t2,
        s.t3
    FROM wbx_data_mart.srids_dist AS s
    PREWHERE
        toDate(s.timestamp_created, 'Europe/Moscow') BETWEEN toDate('{{date_range.start}}') AND toDate('{{date_range.end}}')
    WHERE
        (has([{{supplier_id}}], -1) OR s.supplier_id IN ({{supplier_id}}))
        AND (has([{{order_src_office_id}}], -1) OR s.order_src_office_id IN ({{order_src_office_id}}))
        AND (has([{{order_dst_office_id}}], -1) OR s.order_dst_office_id IN ({{order_dst_office_id}}))
        AND (empty(nm_ids_filter) OR has(nm_ids_filter, -1) OR has(nm_ids_filter, toInt64(s.nm_id)))
),

filtered AS (
    SELECT
        r.delivery_type,
        r.order_src_office_id,
        r.timestamp_created,
        r.timestamp_src,
        r.timestamp_lm,
        r.timestamp_dst,
        r.t1,
        r.t2,
        r.t3
    FROM raw AS r
    ANY LEFT JOIN region_map AS reg
        ON r.order_dst_osm_id = reg.order_dst_osm_id
    WHERE 0 IN ({{Регион доставки}}) OR reg.region_osm_id IN ({{Регион доставки}})
),

prepared AS (
    SELECT
        f.delivery_type,
        f.order_src_office_id,
        f.timestamp_created,
        f.timestamp_src,
        f.timestamp_lm,
        f.timestamp_dst,
        f.t1,
        f.t2,
        f.t3,
        f.timestamp_src >= f.timestamp_created AND f.timestamp_src > toDateTime(0) AND f.t1 >= f.timestamp_created AND f.t1 > toDateTime(0) AS t1_ok,
        f.timestamp_lm >= f.timestamp_created AND f.timestamp_lm > toDateTime(0) AND f.t2 >= f.timestamp_created AND f.t2 > toDateTime(0) AS t2_ok,
        f.timestamp_dst >= f.timestamp_created AND f.timestamp_dst > toDateTime(0) AND f.t3 >= f.timestamp_created AND f.t3 > toDateTime(0) AS t3_ok
    FROM filtered AS f
),

office_agg AS (
    SELECT
        p.delivery_type,
        p.order_src_office_id,

        round(sumIf(dateDiff('second', p.timestamp_created, p.timestamp_src), p.t1_ok) / nullIf(countIf(p.t1_ok), 0) / 3600, 2) AS t1_fact,
        round(sumIf(dateDiff('second', p.timestamp_created, p.t1), p.t1_ok) / nullIf(countIf(p.t1_ok), 0) / 3600, 2) AS t1_pred,
        round(sumIf(dateDiff('second', p.timestamp_src, p.t1), p.t1_ok) / nullIf(countIf(p.t1_ok), 0) / 3600, 2) AS t1_error,

        round(sumIf(dateDiff('second', p.timestamp_created, p.timestamp_lm), p.t2_ok) / nullIf(countIf(p.t2_ok), 0) / 3600, 2) AS t2_fact,
        round(sumIf(dateDiff('second', p.timestamp_created, p.t2), p.t2_ok) / nullIf(countIf(p.t2_ok), 0) / 3600, 2) AS t2_pred,
        round(sumIf(dateDiff('second', p.timestamp_lm, p.t2), p.t2_ok) / nullIf(countIf(p.t2_ok), 0) / 3600, 2) AS t2_error,

        round(sumIf(dateDiff('second', p.timestamp_created, p.timestamp_dst), p.t3_ok) / nullIf(countIf(p.t3_ok), 0) / 3600, 2) AS t3_fact,
        round(sumIf(dateDiff('second', p.timestamp_created, p.t3), p.t3_ok) / nullIf(countIf(p.t3_ok), 0) / 3600, 2) AS t3_pred,
        round(sumIf(dateDiff('second', p.timestamp_dst, p.t3), p.t3_ok) / nullIf(countIf(p.t3_ok), 0) / 3600, 2) AS t3_error,

        count() AS orders_cnt,
        countIf(p.t1_ok) AS t1_cnt,
        countIf(p.t2_ok) AS t2_cnt,
        countIf(p.t3_ok) AS t3_cnt

    FROM prepared AS p
    GROUP BY p.delivery_type, p.order_src_office_id
)

SELECT
    a.delivery_type,
    a.order_src_office_id,
    ol.office_name,
    a.t1_fact,
    a.t1_pred,
    a.t1_error,
    a.t2_fact,
    a.t2_pred,
    a.t2_error,
    a.t3_fact,
    a.t3_pred,
    a.t3_error,
    a.orders_cnt,
    a.t1_cnt,
    a.t2_cnt,
    a.t3_cnt

FROM office_agg AS a
ANY LEFT JOIN wbx_data_mart.office_location AS ol
    ON a.order_src_office_id = ol.id

ORDER BY a.delivery_type, a.orders_cnt DESC
WITH
    arrayFilter(
        x -> x != 0,
        arrayMap(x -> toInt64OrZero(trimBoth(x)), splitByRegexp('[,;\\s]+', '{{nm_id}}'))
    ) AS nm_ids_filter,

region_map AS (
    SELECT
        z4.osm_id AS order_dst_osm_id,
        z2.osm_id AS region_osm_id
    FROM wbx_data_mart.osm_zones AS z4
    ANY LEFT JOIN wbx_data_mart.osm_zones AS z3
        ON z4.parent_id = z3.osm_id AND z3.level = 3
    ANY LEFT JOIN wbx_data_mart.osm_zones AS z2
        ON z3.parent_id = z2.osm_id AND z2.level = 2
    WHERE z4.level = 4
),

base AS (
    SELECT
        toDate(timestamp_created, 'Europe/Moscow') AS report_date,
        order_dst_osm_id,
        timestamp_created,
        timestamp_src,
        timestamp_lm,
        timestamp_dst,
        t1,
        t2,
        t3
    FROM wbx_data_mart.srids_dist
    PREWHERE
        delivery_type = 'FBS'
        AND toDate(timestamp_created, 'Europe/Moscow') BETWEEN toDate('{{date_range.start}}') AND toDate('{{date_range.end}}')
    WHERE
        (has([{{supplier_id}}], -1) OR supplier_id IN ({{supplier_id}}))
        AND (has([{{order_src_office_id}}], -1) OR order_src_office_id IN ({{order_src_office_id}}))
        AND (has([{{order_dst_office_id}}], -1) OR order_dst_office_id IN ({{order_dst_office_id}}))
        AND (empty(nm_ids_filter) OR has(nm_ids_filter, -1) OR has(nm_ids_filter, toInt64(nm_id)))
),

filtered AS (
    SELECT b.*
    FROM base AS b
    ANY LEFT JOIN region_map AS reg
        ON b.order_dst_osm_id = reg.order_dst_osm_id
    WHERE 0 IN ({{Регион доставки}}) OR reg.region_osm_id IN ({{Регион доставки}})
),

prepared AS (
    SELECT
        *,
        timestamp_src >= timestamp_created
            AND timestamp_src > toDateTime(0)
            AND t1 >= timestamp_created
            AND t1 > toDateTime(0) AS t1_ok,
        timestamp_lm >= timestamp_created
            AND timestamp_lm > toDateTime(0)
            AND t2 >= timestamp_created
            AND t2 > toDateTime(0) AS t2_ok,
        timestamp_dst >= timestamp_created
            AND timestamp_dst > toDateTime(0)
            AND t3 >= timestamp_created
            AND t3 > toDateTime(0) AS t3_ok
    FROM filtered
)

SELECT
    report_date,

    round(sumIf(dateDiff('second', timestamp_created, timestamp_src), t1_ok) / nullIf(countIf(t1_ok), 0) / 3600, 2) AS t1_fact,
    round(sumIf(dateDiff('second', timestamp_created, t1), t1_ok) / nullIf(countIf(t1_ok), 0) / 3600, 2) AS t1_pred,
    round(sumIf(dateDiff('second', timestamp_src, t1), t1_ok) / nullIf(countIf(t1_ok), 0) / 3600, 2) AS t1_error,

    round(sumIf(dateDiff('second', timestamp_created, timestamp_lm), t2_ok) / nullIf(countIf(t2_ok), 0) / 3600, 2) AS t2_fact,
    round(sumIf(dateDiff('second', timestamp_created, t2), t2_ok) / nullIf(countIf(t2_ok), 0) / 3600, 2) AS t2_pred,
    round(sumIf(dateDiff('second', timestamp_lm, t2), t2_ok) / nullIf(countIf(t2_ok), 0) / 3600, 2) AS t2_error,

    round(sumIf(dateDiff('second', timestamp_created, timestamp_dst), t3_ok) / nullIf(countIf(t3_ok), 0) / 3600, 2) AS t3_fact,
    round(sumIf(dateDiff('second', timestamp_created, t3), t3_ok) / nullIf(countIf(t3_ok), 0) / 3600, 2) AS t3_pred,
    round(sumIf(dateDiff('second', timestamp_dst, t3), t3_ok) / nullIf(countIf(t3_ok), 0) / 3600, 2) AS t3_error,

    count() AS orders_cnt,
    countIf(t1_ok) AS t1_cnt,
    countIf(t2_ok) AS t2_cnt,
    countIf(t3_ok) AS t3_cnt

FROM prepared
GROUP BY report_date
HAVING count() > 5
ORDER BY report_dateWITH
    arrayFilter(x -> x != 0, arrayMap(x -> toInt64OrZero(trimBoth(x)), splitByRegexp('[,;\\s]+', '{{nm_id}}'))) AS nm_ids_filter,

region_map AS (
    SELECT z4.osm_id AS order_dst_osm_id, z2.osm_id AS region_osm_id
    FROM wbx_data_mart.osm_zones AS z4
    ANY LEFT JOIN wbx_data_mart.osm_zones AS z3
        ON z4.parent_id = z3.osm_id AND z3.level = 3
    ANY LEFT JOIN wbx_data_mart.osm_zones AS z2
        ON z3.parent_id = z2.osm_id AND z2.level = 2
    WHERE z4.level = 4
),

raw AS (
    SELECT
        toDate(s.timestamp_created, 'Europe/Moscow') AS report_date,
        s.order_dst_osm_id,
        s.timestamp_created,
        s.timestamp_src,
        s.timestamp_lm,
        s.timestamp_dst,
        s.t1,
        s.t2,
        s.t3
    FROM wbx_data_mart.srids_dist AS s
    PREWHERE
        s.delivery_type = 'WH'
        AND toDate(s.timestamp_created, 'Europe/Moscow') BETWEEN toDate('{{date_range.start}}') AND toDate('{{date_range.end}}')
    WHERE
        (has([{{supplier_id}}], -1) OR s.supplier_id IN ({{supplier_id}}))
        AND (has([{{order_src_office_id}}], -1) OR s.order_src_office_id IN ({{order_src_office_id}}))
        AND (has([{{order_dst_office_id}}], -1) OR s.order_dst_office_id IN ({{order_dst_office_id}}))
        AND (empty(nm_ids_filter) OR has(nm_ids_filter, -1) OR has(nm_ids_filter, toInt64(s.nm_id)))
),

filtered AS (
    SELECT
        r.report_date,
        r.timestamp_created,
        r.timestamp_src,
        r.timestamp_lm,
        r.timestamp_dst,
        r.t1,
        r.t2,
        r.t3
    FROM raw AS r
    ANY LEFT JOIN region_map AS reg
        ON r.order_dst_osm_id = reg.order_dst_osm_id
    WHERE 0 IN ({{Регион доставки}}) OR reg.region_osm_id IN ({{Регион доставки}})
),

prepared AS (
    SELECT
        *,
        timestamp_src >= timestamp_created
            AND timestamp_src > toDateTime(0)
            AND t1 >= timestamp_created
            AND t1 > toDateTime(0) AS t1_ok,

        timestamp_lm >= timestamp_created
            AND timestamp_lm > toDateTime(0)
            AND t2 >= timestamp_created
            AND t2 > toDateTime(0) AS t2_ok,

        timestamp_dst >= timestamp_created
            AND timestamp_dst > toDateTime(0)
            AND t3 >= timestamp_created
            AND t3 > toDateTime(0) AS t3_ok,

        timestamp_src >= timestamp_created
            AND timestamp_src > toDateTime(0)
            AND timestamp_lm >= timestamp_src
            AND timestamp_lm > toDateTime(0)
            AND t1 >= timestamp_created
            AND t1 > toDateTime(0)
            AND t2 >= t1
            AND t2 > toDateTime(0) AS route2_ok,

        timestamp_lm >= timestamp_created
            AND timestamp_lm > toDateTime(0)
            AND timestamp_dst >= timestamp_lm
            AND timestamp_dst > toDateTime(0)
            AND t2 >= timestamp_created
            AND t2 > toDateTime(0)
            AND t3 >= t2
            AND t3 > toDateTime(0) AS route3_ok

    FROM filtered
)

SELECT
    report_date,

    round(sumIf(dateDiff('second', timestamp_created, timestamp_src), t1_ok) / nullIf(countIf(t1_ok), 0) / 3600, 2) AS t1_fact,
    round(sumIf(dateDiff('second', timestamp_created, t1), t1_ok) / nullIf(countIf(t1_ok), 0) / 3600, 2) AS t1_pred,
    round(sumIf(dateDiff('second', timestamp_src, t1), t1_ok) / nullIf(countIf(t1_ok), 0) / 3600, 2) AS route1_error,
    round(sumIf(dateDiff('second', timestamp_src, t1), t1_ok) / nullIf(countIf(t1_ok), 0) / 3600, 2) AS cum_error_t1,

    round(sumIf(dateDiff('second', timestamp_created, timestamp_lm), t2_ok) / nullIf(countIf(t2_ok), 0) / 3600, 2) AS t2_fact,
    round(sumIf(dateDiff('second', timestamp_created, t2), t2_ok) / nullIf(countIf(t2_ok), 0) / 3600, 2) AS t2_pred,
    round(
        sumIf(
            dateDiff('second', t1, t2) - dateDiff('second', timestamp_src, timestamp_lm),
            route2_ok
        ) / nullIf(countIf(route2_ok), 0) / 3600,
        2
    ) AS route2_error,
    round(sumIf(dateDiff('second', timestamp_lm, t2), t2_ok) / nullIf(countIf(t2_ok), 0) / 3600, 2) AS cum_error_t2,

    round(sumIf(dateDiff('second', timestamp_created, timestamp_dst), t3_ok) / nullIf(countIf(t3_ok), 0) / 3600, 2) AS t3_fact,
    round(sumIf(dateDiff('second', timestamp_created, t3), t3_ok) / nullIf(countIf(t3_ok), 0) / 3600, 2) AS t3_pred,
    round(
        sumIf(
            dateDiff('second', t2, t3) - dateDiff('second', timestamp_lm, timestamp_dst),
            route3_ok
        ) / nullIf(countIf(route3_ok), 0) / 3600,
        2
    ) AS route3_error,
    round(sumIf(dateDiff('second', timestamp_dst, t3), t3_ok) / nullIf(countIf(t3_ok), 0) / 3600, 2) AS cum_error_t3,

    count() AS orders_cnt,
    countIf(t1_ok) AS t1_cnt,
    countIf(t2_ok) AS t2_cnt,
    countIf(t3_ok) AS t3_cnt

FROM prepared
GROUP BY report_date
HAVING count() > 5
ORDER BY report_dateWITH
    arrayFilter(
        x -> x != 0,
        arrayMap(
            x -> toInt64OrZero(trimBoth(x)),
            splitByChar(',', replaceAll('{{nm_id}}', ' ', ''))
        )
    ) AS nm_ids_filter,

region_map AS (
    SELECT
        z4.osm_id AS order_dst_osm_id,
        z2.osm_id AS region_osm_id,
        z2.osm_name AS region_name
    FROM wbx_data_mart.osm_zones AS z4
    ANY LEFT JOIN wbx_data_mart.osm_zones AS z3
        ON z4.parent_id = z3.osm_id
        AND z3.level = 3
    ANY LEFT JOIN wbx_data_mart.osm_zones AS z2
        ON z3.parent_id = z2.osm_id
        AND z2.level = 2
    WHERE z4.level = 4
),

raw AS (
    SELECT
        s.nm_id,
        s.supplier_id,
        s.delivery_type,
        s.order_src_office_id,
        s.order_dst_office_id,
        s.src_osm_id,
        s.lm_osm_id,
        s.dst_osm_id,
        s.timestamp_created,
        s.timestamp_src,
        s.timestamp_lm,
        s.timestamp_dst,
        s.t1,
        s.t2,
        s.t3,
        s.srid
    FROM wbx_data_mart.srids_dist AS s

    PREWHERE
        s.delivery_type = 'FBS'
        AND toDate(s.timestamp_created, 'Europe/Moscow')
            BETWEEN toDate('{{date_range.start}}')
                AND toDate('{{date_range.end}}')

    WHERE
        (
            has([{{supplier_id}}], -1)
            OR s.supplier_id IN ({{supplier_id}})
        )

        AND (
            has([{{order_src_office_id}}], -1)
            OR s.order_src_office_id IN ({{order_src_office_id}})
        )

        AND (
            has([{{order_dst_office_id}}], -1)
            OR s.order_dst_office_id IN ({{order_dst_office_id}})
        )

        AND (
            empty(nm_ids_filter)
            OR has(nm_ids_filter, -1)
            OR has(nm_ids_filter, toInt64(s.nm_id))
        )
),

filtered AS (
    SELECT s.*
    FROM raw AS s

    ANY LEFT JOIN region_map AS reg
        ON s.order_dst_office_id = reg.order_dst_osm_id

    WHERE
        0 IN ({{Регион доставки}})
        OR reg.region_osm_id IN ({{Регион доставки}})
),

base AS (
    SELECT
        nm_id,
        supplier_id,
        delivery_type,
        order_src_office_id,

        src_osm_id AS base_src_osm_id,
        lm_osm_id AS base_lm_osm_id,
        dst_osm_id AS base_dst_osm_id,

        toStartOfHour(timestamp_created) AS created_hour,

        count() AS n,
        uniqExactState(srid) AS srid_state,

        sumIf(
            dateDiff('second', timestamp_created, timestamp_src),
            timestamp_src >= timestamp_created
            AND timestamp_src > toDateTime(0)
        ) AS t1_fact_sum_raw,

        countIf(
            timestamp_src >= timestamp_created
            AND timestamp_src > toDateTime(0)
        ) AS t1_fact_n,

        sumIf(
            dateDiff('second', timestamp_created, t1),
            t1 >= timestamp_created
            AND t1 > toDateTime(0)
        ) AS t1_pred_sum_raw,

        countIf(
            t1 >= timestamp_created
            AND t1 > toDateTime(0)
        ) AS t1_pred_n,

        sumIf(
            dateDiff('second', timestamp_src, t1),
            timestamp_src >= timestamp_created
            AND t1 >= timestamp_created
            AND timestamp_src > toDateTime(0)
            AND t1 > toDateTime(0)
        ) AS t1_error_sum_raw,

        sumIf(
            abs(dateDiff('second', timestamp_src, t1)),
            timestamp_src >= timestamp_created
            AND t1 >= timestamp_created
            AND timestamp_src > toDateTime(0)
            AND t1 > toDateTime(0)
        ) AS t1_ae_sum_raw,

        countIf(
            timestamp_src >= timestamp_created
            AND t1 >= timestamp_created
            AND timestamp_src > toDateTime(0)
            AND t1 > toDateTime(0)
        ) AS t1_err_n,

        sumIf(
            dateDiff('second', timestamp_created, timestamp_lm),
            timestamp_lm >= timestamp_created
            AND timestamp_lm > toDateTime(0)
        ) AS t2_fact_sum_raw,

        countIf(
            timestamp_lm >= timestamp_created
            AND timestamp_lm > toDateTime(0)
        ) AS t2_fact_n,

        sumIf(
            dateDiff('second', timestamp_created, t2),
            t2 >= timestamp_created
            AND t2 > toDateTime(0)
        ) AS t2_pred_sum_raw,

        countIf(
            t2 >= timestamp_created
            AND t2 > toDateTime(0)
        ) AS t2_pred_n,

        sumIf(
            dateDiff('second', timestamp_lm, t2),
            timestamp_lm >= timestamp_created
            AND t2 >= timestamp_created
            AND timestamp_lm > toDateTime(0)
            AND t2 > toDateTime(0)
        ) AS t2_error_sum_raw,

        sumIf(
            abs(dateDiff('second', timestamp_lm, t2)),
            timestamp_lm >= timestamp_created
            AND t2 >= timestamp_created
            AND timestamp_lm > toDateTime(0)
            AND t2 > toDateTime(0)
        ) AS t2_ae_sum_raw,

        countIf(
            timestamp_lm >= timestamp_created
            AND t2 >= timestamp_created
            AND timestamp_lm > toDateTime(0)
            AND t2 > toDateTime(0)
        ) AS t2_err_n,

        sumIf(
            dateDiff('second', timestamp_created, timestamp_dst),
            timestamp_dst >= timestamp_created
            AND timestamp_dst > toDateTime(0)
        ) AS t3_fact_sum_raw,

        countIf(
            timestamp_dst >= timestamp_created
            AND timestamp_dst > toDateTime(0)
        ) AS t3_fact_n,

        sumIf(
            dateDiff('second', timestamp_created, t3),
            t3 >= timestamp_created
            AND t3 > toDateTime(0)
        ) AS t3_pred_sum_raw,

        countIf(
            t3 >= timestamp_created
            AND t3 > toDateTime(0)
        ) AS t3_pred_n,

        sumIf(
            dateDiff('second', timestamp_dst, t3),
            timestamp_dst >= timestamp_created
            AND t3 >= timestamp_created
            AND timestamp_dst > toDateTime(0)
            AND t3 > toDateTime(0)
        ) AS t3_error_sum_raw,

        sumIf(
            abs(dateDiff('second', timestamp_dst, t3)),
            timestamp_dst >= timestamp_created
            AND t3 >= timestamp_created
            AND timestamp_dst > toDateTime(0)
            AND t3 > toDateTime(0)
        ) AS t3_ae_sum_raw,

        countIf(
            timestamp_dst >= timestamp_created
            AND t3 >= timestamp_created
            AND timestamp_dst > toDateTime(0)
            AND t3 > toDateTime(0)
        ) AS t3_err_n

    FROM filtered

    GROUP BY
        nm_id,
        supplier_id,
        delivery_type,
        order_src_office_id,
        base_src_osm_id,
        base_lm_osm_id,
        base_dst_osm_id,
        created_hour
),

enriched AS (
    SELECT
        b.*,

        z_lm.osm_name AS lm_osm_name,
        z_dst.osm_name AS dst_osm_name,

        if(
            isNull(r1.matched),
            'NO_HISTORY',
            ifNull(toString(r1.duration_calc_type_id), 'NULL')
        ) AS calc_type1,

        if(
            isNull(r2.matched),
            'NO_HISTORY',
            ifNull(toString(r2.duration_calc_type_id), 'NULL')
        ) AS calc_type2,

        if(
            isNull(r3.matched),
            'NO_HISTORY',
            ifNull(toString(r3.duration_calc_type_id), 'NULL')
        ) AS calc_type3,

        r1.duration AS route1_duration,
        r1.base_duration AS route1_base_duration,

        r2.duration AS route2_duration,
        r2.base_duration AS route2_base_duration,

        r3.duration AS route3_duration,
        r3.base_duration AS route3_base_duration

    FROM base AS b

    ANY LEFT JOIN (
        SELECT
            wh_office_id,
            supplier_id,
            toStartOfHour(date_time) AS route_hour,
            duration,
            base_duration,
            duration_calc_type_id,
            toNullable(toUInt8(1)) AS matched
        FROM wbx_data_mart.route1_mp_history_hour
        WHERE date_time >= '{{date_range.start}} 00:00:00'
          AND date_time <= '{{date_range.end}} 23:59:59'
    ) AS r1
        ON b.order_src_office_id = r1.wh_office_id
        AND b.supplier_id = r1.supplier_id
        AND b.created_hour = r1.route_hour

    ANY LEFT JOIN (
        SELECT
            wh_osm_id,
            lm_osm_id,
            toStartOfHour(date_time) AS route_hour,
            duration,
            base_duration,
            duration_calc_type_id,
            toNullable(toUInt8(1)) AS matched
        FROM wbx_data_mart.route2_history_hour
        WHERE date_time >= '{{date_range.start}} 00:00:00'
          AND date_time <= '{{date_range.end}} 23:59:59'
    ) AS r2
        ON b.base_src_osm_id = r2.wh_osm_id
        AND b.base_lm_osm_id = r2.lm_osm_id
        AND b.created_hour = r2.route_hour

    ANY LEFT JOIN (
        SELECT
            lm_osm_id,
            dst_osm_id,
            toStartOfHour(date_time) AS route_hour,
            duration,
            base_duration,
            duration_calc_type_id,
            toNullable(toUInt8(1)) AS matched
        FROM wbx_data_mart.route3_history_hour
        WHERE date_time >= '{{date_range.start}} 00:00:00'
          AND date_time <= '{{date_range.end}} 23:59:59'
    ) AS r3
        ON b.base_lm_osm_id = r3.lm_osm_id
        AND b.base_dst_osm_id = r3.dst_osm_id
        AND b.created_hour = r3.route_hour

    ANY LEFT JOIN wbx_data_mart.osm_zones AS z_lm
        ON b.base_lm_osm_id = z_lm.osm_id

    ANY LEFT JOIN wbx_data_mart.osm_zones AS z_dst
        ON b.base_dst_osm_id = z_dst.osm_id
)

SELECT
    nm_id,

    order_src_office_id,

    base_src_osm_id AS src_osm_id,

    base_lm_osm_id AS lm_osm_id,
    lm_osm_name,

    base_dst_osm_id AS dst_osm_id,
    dst_osm_name,

    route1_duration,
    route1_base_duration,
    calc_type1,

    route2_duration,
    route2_base_duration,
    calc_type2,

    route3_duration,
    route3_base_duration,
    calc_type3,

    delivery_type,

    sum(n) AS orders_cnt,
    uniqExactMerge(srid_state) AS srids_cnt,

    round(
        sum(t1_fact_sum_raw)
        / nullIf(sum(t1_fact_n), 0)
        / 3600,
        2
    ) AS t1_fact,

    round(
        sum(t1_pred_sum_raw)
        / nullIf(sum(t1_pred_n), 0)
        / 3600,
        2
    ) AS t1_pred,

    round(
        sum(t1_error_sum_raw)
        / nullIf(sum(t1_err_n), 0)
        / 3600,
        2
    ) AS t1_error,

    round(
        sum(t1_ae_sum_raw)
        / nullIf(sum(t1_err_n), 0)
        / 3600,
        2
    ) AS t1_mae,

    sum(t1_fact_n) AS t1_fact_cnt,
    sum(t1_pred_n) AS t1_pred_cnt,
    sum(t1_err_n) AS t1_cnt,

    round(
        sum(t2_fact_sum_raw)
        / nullIf(sum(t2_fact_n), 0)
        / 3600,
        2
    ) AS t2_fact,

    round(
        sum(t2_pred_sum_raw)
        / nullIf(sum(t2_pred_n), 0)
        / 3600,
        2
    ) AS t2_pred,

    round(
        sum(t2_error_sum_raw)
        / nullIf(sum(t2_err_n), 0)
        / 3600,
        2
    ) AS t2_error,

    round(
        sum(t2_ae_sum_raw)
        / nullIf(sum(t2_err_n), 0)
        / 3600,
        2
    ) AS t2_mae,

    sum(t2_fact_n) AS t2_fact_cnt,
    sum(t2_pred_n) AS t2_pred_cnt,
    sum(t2_err_n) AS t2_cnt,

    round(
        sum(t3_fact_sum_raw)
        / nullIf(sum(t3_fact_n), 0)
        / 3600,
        2
    ) AS t3_fact,

    round(
        sum(t3_pred_sum_raw)
        / nullIf(sum(t3_pred_n), 0)
        / 3600,
        2
    ) AS t3_pred,

    round(
        sum(t3_error_sum_raw)
        / nullIf(sum(t3_err_n), 0)
        / 3600,
        2
    ) AS t3_error,

    round(
        sum(t3_ae_sum_raw)
        / nullIf(sum(t3_err_n), 0)
        / 3600,
        2
    ) AS t3_mae,

    sum(t3_fact_n) AS t3_fact_cnt,
    sum(t3_pred_n) AS t3_pred_cnt,
    sum(t3_err_n) AS t3_cnt

FROM enriched

GROUP BY
    nm_id,
    order_src_office_id,

    base_src_osm_id,

    base_lm_osm_id,
    lm_osm_name,

    base_dst_osm_id,
    dst_osm_name,

    route1_duration,
    route1_base_duration,
    calc_type1,

    route2_duration,
    route2_base_duration,
    calc_type2,

    route3_duration,
    route3_base_duration,
    calc_type3,

    delivery_type

ORDER BY
    nm_id,
    order_src_office_id,
    orders_cnt DESC
