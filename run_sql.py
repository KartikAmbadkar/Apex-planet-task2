import pandas as pd, sqlite3, re, json
d=pd.read_excel("data/sales_cleaned.xlsx"); d['Order_Date']=pd.to_datetime(d.Order_Date).dt.strftime('%Y-%m-%d')
d['City']=d.City.fillna('Unknown')
con=sqlite3.connect("data/sales.db")
dp=d[['Product','Category']].drop_duplicates().reset_index(drop=True); dp.insert(0,'product_id',range(1,len(dp)+1)); dp.columns=['product_id','product','category']
dc=pd.DataFrame({'city':sorted(d.City.unique())}); dc.insert(0,'city_id',range(1,len(dc)+1))
o=d.merge(dp,left_on=['Product','Category'],right_on=['product','category']).merge(dc,left_on='City',right_on='city').sort_index() if False else d.copy()
o=o.merge(dp.rename(columns={'product':'Product','category':'Category'}),on=['Product','Category']).merge(dc.rename(columns={'city':'City'}),on='City')
o=o.sort_values(['Order_Date','Order_ID']).reset_index(drop=True); o.insert(0,'order_key',range(1,len(o)+1))
o=o.rename(columns=str.lower)[['order_key','order_id','order_date','customer_id','customer_name','age','gender','city_id','product_id','quantity','unit_price','total_sales']]
o.to_sql('orders',con,if_exists='replace',index=False); dp.to_sql('dim_product',con,if_exists='replace',index=False); dc.to_sql('dim_city',con,if_exists='replace',index=False)
src=open("sql/queries.sql").read()
blocks=re.split(r'\n(?=-- Q\d)',src)[1:]
md=["# SQL Queries & Results\n","Engine: SQLite 3 (database built from the cleaned dataset; `City` nulls labelled `Unknown`).\n"]
res={}
for b in blocks:
    title=b.splitlines()[0][3:]; q="\n".join(l for l in b.splitlines()[1:])
    r=pd.read_sql(q,con); res[title[:2]]=r.to_dict('records'); r.to_csv(f"sql/{title[:2].lower()}_result.csv",index=False)
    md.append(f"## {title}\n```sql\n{q.strip()}\n```\n**Result**\n\n{r.to_markdown(index=False,floatfmt=",.2f")}\n")
open("sql/SQL_queries_and_results.md","w").write("\n".join(md)); json.dump(res,open("data/sql_results.json","w"),default=str)
print("\n".join(md)[:6000])
