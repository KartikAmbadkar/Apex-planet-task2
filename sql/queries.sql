-- ApexPlanet Task 2: Business questions (SQLite dialect)
-- Schema: orders(order_key, order_id, order_date, customer_id, customer_name, age, gender,
--                city_id, product_id, quantity, unit_price, total_sales)
--         dim_product(product_id, product, category)   dim_city(city_id, city)
-- NOTE: Order_ID is NOT unique in the dataset (each ID appears up to 9 times), so order_key is the true row key.

-- Q1. Top 5 products by revenue in the last 6 months
SELECT p.product, p.category, ROUND(SUM(o.total_sales),2) AS revenue, SUM(o.quantity) AS units, COUNT(*) AS orders
FROM orders o JOIN dim_product p ON p.product_id = o.product_id
WHERE o.order_date >= DATE('2026-01-01','-6 months')
GROUP BY p.product, p.category ORDER BY revenue DESC LIMIT 5;

-- Q2. Monthly revenue trend with month-over-month growth (Jan-2026 is a 1-day stub, excluded)
WITH m AS (
  SELECT STRFTIME('%Y-%m', order_date) AS month, SUM(total_sales) AS revenue, COUNT(*) AS orders
  FROM orders WHERE order_date < '2026-01-01' GROUP BY 1)
SELECT month, ROUND(revenue,2) AS revenue, orders,
       ROUND(100.0*(revenue - LAG(revenue) OVER (ORDER BY month)) / LAG(revenue) OVER (ORDER BY month),1) AS mom_growth_pct
FROM m ORDER BY month;

-- Q3. Revenue share by category (window function)
SELECT p.category, ROUND(SUM(o.total_sales),2) AS revenue,
       ROUND(100.0*SUM(o.total_sales)/SUM(SUM(o.total_sales)) OVER (),1) AS pct_of_total,
       ROUND(AVG(o.total_sales),2) AS avg_order_value
FROM orders o JOIN dim_product p ON p.product_id = o.product_id
GROUP BY p.category ORDER BY revenue DESC;

-- Q4. Best city for each category (3-way join + rank)
WITH x AS (
  SELECT p.category, c.city, SUM(o.total_sales) AS revenue,
         RANK() OVER (PARTITION BY p.category ORDER BY SUM(o.total_sales) DESC) AS rnk
  FROM orders o JOIN dim_product p ON p.product_id=o.product_id JOIN dim_city c ON c.city_id=o.city_id
  GROUP BY p.category, c.city)
SELECT category, city, ROUND(revenue,2) AS revenue FROM x WHERE rnk=1 ORDER BY revenue DESC;

-- Q5. Revenue and order value by age group and gender (age NULLs excluded)
SELECT CASE WHEN age<25 THEN '18-24' WHEN age<35 THEN '25-34' WHEN age<45 THEN '35-44'
            WHEN age<55 THEN '45-54' ELSE '55-65' END AS age_group,
       gender, COUNT(*) AS orders, ROUND(SUM(total_sales),2) AS revenue, ROUND(AVG(total_sales),2) AS avg_order_value
FROM orders WHERE age IS NOT NULL GROUP BY age_group, gender ORDER BY age_group, gender;

-- Q6. Top 10 customers by lifetime spend, with repeat-purchase flag
SELECT customer_id, COUNT(*) AS orders, ROUND(SUM(total_sales),2) AS lifetime_spend,
       CASE WHEN COUNT(*)>1 THEN 'Repeat' ELSE 'One-time' END AS segment
FROM orders GROUP BY customer_id ORDER BY lifetime_spend DESC LIMIT 10;

-- Q7. Cities ranked by revenue, with orders, AOV and share (filter: cities above overall average revenue)
WITH c AS (
  SELECT ci.city, SUM(o.total_sales) AS revenue, COUNT(*) AS orders
  FROM orders o JOIN dim_city ci ON ci.city_id=o.city_id GROUP BY ci.city)
SELECT city, ROUND(revenue,2) AS revenue, orders, ROUND(revenue/orders,2) AS avg_order_value,
       ROUND(100.0*revenue/SUM(revenue) OVER (),1) AS pct_of_total
FROM c WHERE revenue > (SELECT AVG(revenue) FROM c) ORDER BY revenue DESC;
