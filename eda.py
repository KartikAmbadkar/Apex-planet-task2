import pandas as pd, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, seaborn as sns, json
from matplotlib.ticker import FuncFormatter
d=pd.read_excel("data/sales_cleaned.xlsx"); d['Order_Date']=pd.to_datetime(d.Order_Date); d['City']=d.City.fillna('Unknown')
BLUE="#2f6fa8"; INK="#1f2933"; MUT="#6b7785"; GRID="#e4e8ec"
plt.rcParams.update({"font.family":"DejaVu Sans","axes.edgecolor":GRID,"axes.labelcolor":MUT,"xtick.color":MUT,"ytick.color":MUT,"axes.spines.top":False,"axes.spines.right":False,"axes.grid":True,"grid.color":GRID,"axes.axisbelow":True,"axes.titleweight":"bold","axes.titlecolor":INK,"axes.titlesize":12,"axes.titlelocation":"left","figure.dpi":150})
fm=FuncFormatter(lambda x,_: f"{x/1e6:.1f}M" if abs(x)>=1e6 else f"{x/1e3:.0f}K" if abs(x)>=1e3 else f"{x:.0f}")
def save(n): plt.tight_layout(); plt.savefig(f"charts/{n}.png"); plt.close()
num=['Age','Quantity','Unit_Price','Total_Sales']
d.groupby('Category').size()  # noqa
# summary stats
s=d[num].describe().T; s['skew']=d[num].skew(); s['missing']=d[num].isna().sum(); s.round(2).to_csv("data/numeric_summary.csv")
cat=d[['Gender','City','Product','Category']].describe().T; cat.to_csv("data/categorical_summary.csv")
# 1 histograms
fig,ax=plt.subplots(2,2,figsize=(10,6))
for a,(c,b) in zip(ax.ravel(),[('Age',16),('Quantity',10),('Unit_Price',25),('Total_Sales',30)]):
    a.hist(d[c].dropna(),bins=b,color=BLUE,edgecolor="white",linewidth=.8); a.set_title(f"Distribution of {c}"); 
    if c in('Unit_Price','Total_Sales'): a.xaxis.set_major_formatter(fm)
    a.axvline(d[c].median(),color=INK,ls="--",lw=1); a.text(.97,.9,f"median {d[c].median():,.0f}",transform=a.transAxes,ha="right",color=INK,fontsize=9)
save("01_histograms")
# 2 categorical bars (orders count)
fig,ax=plt.subplots(2,2,figsize=(10,6))
for a,c in zip(ax.ravel(),['Category','Product','City','Gender']):
    v=d[c].value_counts(); a.barh(v.index[::-1],v.values[::-1],color=BLUE,height=.65)
    for i,x in enumerate(v.values[::-1]): a.text(x+2,i,str(x),va="center",color=INK,fontsize=9)
    a.set_title(f"Orders by {c}"); a.grid(axis="y",visible=False); a.set_xlim(0,v.max()*1.15)
save("02_categorical_counts")
# 3 revenue by category / product / city
fig,ax=plt.subplots(1,3,figsize=(13,4))
for a,c in zip(ax,['Category','Product','City']):
    v=d.groupby(c).Total_Sales.sum().sort_values(); a.barh(v.index,v.values,color=BLUE,height=.65)
    for i,x in enumerate(v.values): a.text(x+v.max()*.01,i,f"{x/1e6:.1f}M",va="center",color=INK,fontsize=9)
    a.set_title(f"Revenue by {c}"); a.xaxis.set_major_formatter(fm); a.grid(axis="y",visible=False); a.set_xlim(0,v.max()*1.17)
save("03_revenue_by_dimension")
# 4 monthly trend
m=d[d.Order_Date<'2026-01-01'].groupby(d.Order_Date.dt.to_period('M')).Total_Sales.sum()
fig,a=plt.subplots(figsize=(10,4)); a.plot(m.index.astype(str),m.values,color=BLUE,lw=2,marker="o",ms=6,mfc=BLUE,mec="white",mew=1.5)
a.yaxis.set_major_formatter(fm); a.set_title("Monthly revenue, 2025 (Jan-2026 stub excluded)"); a.set_ylim(0,m.max()*1.15)
a.annotate(f"Peak {m.idxmax()}\n{m.max()/1e6:.1f}M",(str(m.idxmax()),m.max()),xytext=(0,10),textcoords="offset points",ha="center",color=INK,fontsize=9)
a.annotate(f"Low {m.idxmin()}\n{m.min()/1e6:.1f}M",(str(m.idxmin()),m.min()),xytext=(0,-30),textcoords="offset points",ha="center",color=INK,fontsize=9)
plt.xticks(rotation=45); save("04_monthly_revenue")
# 5 corr heatmap (diverging, grey mid)
from matplotlib.colors import LinearSegmentedColormap
dv=LinearSegmentedColormap.from_list("dv",["#b5483a","#eceff1","#2f6fa8"])
c=d[num].corr(); fig,a=plt.subplots(figsize=(5.5,4.5)); sns.heatmap(c,annot=True,fmt=".2f",cmap=dv,vmin=-1,vmax=1,ax=a,linewidths=2,linecolor="white",cbar_kws={"shrink":.8}); a.set_title("Correlation matrix (Pearson)"); a.grid(False); save("05_correlation_heatmap")
# 6 scatter
fig,ax=plt.subplots(1,2,figsize=(11,4.2))
ax[0].scatter(d.Unit_Price,d.Total_Sales,s=14,color=BLUE,alpha=.45,edgecolor="none"); ax[0].set_title("Unit price vs total sales (r=%.2f)"%c.loc['Unit_Price','Total_Sales']); ax[0].set_xlabel("Unit_Price"); ax[0].set_ylabel("Total_Sales")
j=d.copy(); j['Quantity']=j.Quantity+np.random.default_rng(1).uniform(-.2,.2,len(j))
ax[1].scatter(j.Quantity,j.Total_Sales,s=14,color=BLUE,alpha=.45,edgecolor="none"); ax[1].set_title("Quantity vs total sales (r=%.2f)"%c.loc['Quantity','Total_Sales']); ax[1].set_xlabel("Quantity (jittered)")
for a in ax: a.xaxis.set_major_formatter(fm); a.yaxis.set_major_formatter(fm)
ax[1].xaxis.set_major_formatter(FuncFormatter(lambda x,_:f"{x:.0f}"))
save("06_scatter_price_quantity")
# 7 heatmaps
sq=LinearSegmentedColormap.from_list("sq",["#eaf2f9","#2f6fa8","#12385c"])
p=d.pivot_table(index='City',columns='Category',values='Total_Sales',aggfunc='sum')/1e6
fig,a=plt.subplots(figsize=(8,5)); sns.heatmap(p,annot=True,fmt=".1f",cmap=sq,ax=a,linewidths=2,linecolor="white",cbar_kws={"label":"Revenue (M)"}); a.set_title("Revenue (M) by city and category"); a.grid(False); save("07_heatmap_city_category")
d['Age_Group']=pd.cut(d.Age,[17,24,34,44,54,65],labels=['18-24','25-34','35-44','45-54','55-65'])
p=d.pivot_table(index='Age_Group',columns='Category',values='Total_Sales',aggfunc='sum',observed=True)/1e6
fig,a=plt.subplots(figsize=(8,4)); sns.heatmap(p,annot=True,fmt=".1f",cmap=sq,ax=a,linewidths=2,linecolor="white",cbar_kws={"label":"Revenue (M)"}); a.set_title("Revenue (M) by age group and category"); a.grid(False); save("08_heatmap_age_category")
# 9 pairplot
g=sns.pairplot(d[num+['Gender']].dropna(),hue='Gender',palette={"Male":BLUE,"Female":"#d98a2b"},plot_kws=dict(s=10,alpha=.5,edgecolor="none"),diag_kind="hist",height=2); g.figure.suptitle("Pair plot of numeric fields by gender",y=1.02,x=.02,ha="left",fontweight="bold"); g.savefig("charts/09_pairplot.png",dpi=130); plt.close('all')
# 10 boxplot by category
fig,a=plt.subplots(figsize=(8,4)); o=d.groupby('Category').Total_Sales.median().sort_values().index
sns.boxplot(data=d,y='Category',x='Total_Sales',order=o,color="#9dc0de",linecolor=BLUE,fliersize=3,ax=a); a.xaxis.set_major_formatter(fm); a.set_title("Order value by category"); a.grid(axis="y",visible=False); save("10_box_order_value_category")
# stats for report
K=dict(rev=d.Total_Sales.sum(),orders=len(d),aov=d.Total_Sales.mean(),units=int(d.Quantity.sum()),cust=d.Customer_ID.nunique(),
 repeat=int((d.Customer_ID.value_counts()>1).sum()),
 gender=d.groupby('Gender').Total_Sales.sum().to_dict(), cat=d.groupby('Category').Total_Sales.sum().sort_values(ascending=False).to_dict(),
 city=d.groupby('City').Total_Sales.sum().sort_values(ascending=False).to_dict(), prod=d.groupby('Product').Total_Sales.sum().sort_values(ascending=False).to_dict(),
 monthly={str(k):v for k,v in m.items()}, corr=c.round(2).to_dict(), skew=d[num].skew().round(2).to_dict(),
 top10=float(d.nlargest(100,'Total_Sales').Total_Sales.sum()/d.Total_Sales.sum()), aov_cat=d.groupby('Category').Total_Sales.mean().round(0).to_dict(), cust_city=d.groupby('City').Customer_ID.nunique().to_dict())
json.dump(K,open("data/kpis.json","w"),default=float,indent=1)
print(s.round(2).to_string()); print(json.dumps(K,default=float)[:2500])
