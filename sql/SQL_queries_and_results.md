# SQL Queries & Results

Engine: SQLite 3 (database built from the cleaned dataset; `City` nulls labelled `Unknown`).

## Q1. Top 5 products by revenue in the last 6 months
```sql
SELECT p.product, p.category, ROUND(SUM(o.total_sales),2) AS revenue, SUM(o.quantity) AS units, COUNT(*) AS orders
FROM orders o JOIN dim_product p ON p.product_id = o.product_id
WHERE o.order_date >= DATE('2026-01-01','-6 months')
GROUP BY p.product, p.category ORDER BY revenue DESC LIMIT 5;
```
**Result**

| product   | category    |       revenue |   units |   orders |
|:----------|:------------|--------------:|--------:|---------:|
| Laptop    | Electronics | 13,009,494.74 |     501 |       88 |
| Book      | Education   | 12,739,832.53 |     542 |       92 |
| Chair     | Furniture   | 11,560,952.45 |     467 |       87 |
| Shoes     | Fashion     | 11,149,392.03 |     453 |       81 |
| Rice      | Grocery     | 10,215,563.97 |     394 |       75 |

## Q2. Monthly revenue trend with month-over-month growth (Jan-2026 is a 1-day stub, excluded)
```sql
WITH m AS (
  SELECT STRFTIME('%Y-%m', order_date) AS month, SUM(total_sales) AS revenue, COUNT(*) AS orders
  FROM orders WHERE order_date < '2026-01-01' GROUP BY 1)
SELECT month, ROUND(revenue,2) AS revenue, orders,
       ROUND(100.0*(revenue - LAG(revenue) OVER (ORDER BY month)) / LAG(revenue) OVER (ORDER BY month),1) AS mom_growth_pct
FROM m ORDER BY month;
```
**Result**

| month   |       revenue |   orders |   mom_growth_pct |
|:--------|--------------:|---------:|-----------------:|
| 2025-01 | 10,096,190.73 |       76 |           nan    |
| 2025-02 | 11,511,181.46 |       86 |            14.00 |
| 2025-03 | 13,059,899.94 |       89 |            13.50 |
| 2025-04 | 12,222,700.17 |       80 |            -6.40 |
| 2025-05 | 10,984,689.25 |       85 |           -10.10 |
| 2025-06 | 12,912,332.64 |       83 |            17.50 |
| 2025-07 | 11,746,226.80 |       83 |            -9.00 |
| 2025-08 |  9,448,471.22 |       75 |           -19.60 |
| 2025-09 |  9,179,896.29 |       79 |            -2.80 |
| 2025-10 | 12,500,936.50 |       84 |            36.20 |
| 2025-11 | 12,627,620.22 |       77 |             1.00 |
| 2025-12 | 12,299,904.44 |       98 |            -2.60 |

## Q3. Revenue share by category (window function)
```sql
SELECT p.category, ROUND(SUM(o.total_sales),2) AS revenue,
       ROUND(100.0*SUM(o.total_sales)/SUM(SUM(o.total_sales)) OVER (),1) AS pct_of_total,
       ROUND(AVG(o.total_sales),2) AS avg_order_value
FROM orders o JOIN dim_product p ON p.product_id = o.product_id
GROUP BY p.category ORDER BY revenue DESC;
```
**Result**

| category    |       revenue |   pct_of_total |   avg_order_value |
|:------------|--------------:|---------------:|------------------:|
| Electronics | 50,778,581.70 |          36.40 |        143,442.32 |
| Education   | 25,031,689.40 |          18.00 |        140,627.47 |
| Grocery     | 22,231,711.28 |          15.90 |        145,305.30 |
| Furniture   | 21,521,561.48 |          15.40 |        135,355.73 |
| Fashion     | 19,835,895.79 |          14.20 |        127,153.18 |

## Q4. Best city for each category (3-way join + rank)
```sql
WITH x AS (
  SELECT p.category, c.city, SUM(o.total_sales) AS revenue,
         RANK() OVER (PARTITION BY p.category ORDER BY SUM(o.total_sales) DESC) AS rnk
  FROM orders o JOIN dim_product p ON p.product_id=o.product_id JOIN dim_city c ON c.city_id=o.city_id
  GROUP BY p.category, c.city)
SELECT category, city, ROUND(revenue,2) AS revenue FROM x WHERE rnk=1 ORDER BY revenue DESC;
```
**Result**

| category    | city      |      revenue |
|:------------|:----------|-------------:|
| Electronics | Kolkata   | 7,680,200.75 |
| Education   | Patna     | 4,567,627.61 |
| Fashion     | Bengaluru | 4,042,713.46 |
| Grocery     | Bengaluru | 3,579,387.76 |
| Furniture   | Patna     | 3,086,789.79 |

## Q5. Revenue and order value by age group and gender (age NULLs excluded)
```sql
SELECT CASE WHEN age<25 THEN '18-24' WHEN age<35 THEN '25-34' WHEN age<45 THEN '35-44'
            WHEN age<55 THEN '45-54' ELSE '55-65' END AS age_group,
       gender, COUNT(*) AS orders, ROUND(SUM(total_sales),2) AS revenue, ROUND(AVG(total_sales),2) AS avg_order_value
FROM orders WHERE age IS NOT NULL GROUP BY age_group, gender ORDER BY age_group, gender;
```
**Result**

| age_group   | gender   |   orders |       revenue |   avg_order_value |
|:------------|:---------|---------:|--------------:|------------------:|
| 18-24       | Female   |       65 | 10,674,345.02 |        164,220.69 |
| 18-24       | Male     |       82 | 10,551,139.10 |        128,672.43 |
| 25-34       | Female   |       97 | 10,570,552.13 |        108,974.76 |
| 25-34       | Male     |      113 | 16,944,315.31 |        149,949.69 |
| 35-44       | Female   |      115 | 15,652,098.31 |        136,105.20 |
| 35-44       | Male     |       90 | 13,660,018.48 |        151,777.98 |
| 45-54       | Female   |       87 | 12,399,196.96 |        142,519.51 |
| 45-54       | Male     |      108 | 14,924,889.26 |        138,193.42 |
| 55-65       | Female   |      116 | 16,161,741.43 |        139,325.36 |
| 55-65       | Male     |      107 | 14,372,547.18 |        134,322.87 |

## Q6. Top 10 customers by lifetime spend, with repeat-purchase flag
```sql
SELECT customer_id, COUNT(*) AS orders, ROUND(SUM(total_sales),2) AS lifetime_spend,
       CASE WHEN COUNT(*)>1 THEN 'Repeat' ELSE 'One-time' END AS segment
FROM orders GROUP BY customer_id ORDER BY lifetime_spend DESC LIMIT 10;
```
**Result**

| customer_id   |   orders |   lifetime_spend | segment   |
|:--------------|---------:|-----------------:|:----------|
| CUST9510      |        2 |       867,333.24 | Repeat    |
| CUST6845      |        2 |       769,479.75 | Repeat    |
| CUST6532      |        2 |       610,981.74 | Repeat    |
| CUST6082      |        2 |       548,416.39 | Repeat    |
| CUST3689      |        2 |       542,484.08 | Repeat    |
| CUST3730      |        2 |       538,633.97 | Repeat    |
| CUST4706      |        2 |       528,036.44 | Repeat    |
| CUST9693      |        2 |       511,421.86 | Repeat    |
| CUST7374      |        2 |       511,309.40 | Repeat    |
| CUST2062      |        1 |       493,677.50 | One-time  |

## Q7. Cities ranked by revenue, with orders, AOV and share (filter: cities above overall average revenue)
```sql
WITH c AS (
  SELECT ci.city, SUM(o.total_sales) AS revenue, COUNT(*) AS orders
  FROM orders o JOIN dim_city ci ON ci.city_id=o.city_id GROUP BY ci.city)
SELECT city, ROUND(revenue,2) AS revenue, orders, ROUND(revenue/orders,2) AS avg_order_value,
       ROUND(100.0*revenue/SUM(revenue) OVER (),1) AS pct_of_total
FROM c WHERE revenue > (SELECT AVG(revenue) FROM c) ORDER BY revenue DESC;
```
**Result**

| city      |       revenue |   orders |   avg_order_value |   pct_of_total |
|:----------|--------------:|---------:|------------------:|---------------:|
| Patna     | 19,285,966.89 |      135 |        142,859.01 |          17.70 |
| Kolkata   | 18,884,349.57 |      133 |        141,987.59 |          17.30 |
| Bengaluru | 18,773,574.32 |      122 |        153,881.76 |          17.20 |
| Mumbai    | 18,757,050.17 |      131 |        143,183.59 |          17.20 |
| Hyderabad | 17,166,766.87 |      125 |        137,334.13 |          15.80 |
| Delhi     | 16,097,079.00 |      125 |        128,776.63 |          14.80 |
