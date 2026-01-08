# 1/7/26 Newhall
# EDA of usaspending aerospace contract data

# libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# Data import
orig_df = pd.read_csv("usaspending_output/aerospace_execution_transactions.csv", parse_dates=["Action Date", "Issued Date"])

# Data clean
columns_to_drop = ["generated_internal_id", "internal_id"]
clean_df = orig_df.drop(columns=columns_to_drop)    #drop uneeded vars
clean_df["Action Date"] = pd.to_datetime(clean_df["Action Date"], errors="coerce")
clean_df["Issued Date"] = pd.to_datetime(clean_df["Issued Date"], errors="coerce")
clean_df["lead_time"] = (clean_df["Action Date"] - clean_df["Issued Date"]).dt.days
low_value_df = clean_df[(clean_df["Transaction Amount"] >= 100) & (clean_df["Transaction Amount"] <= 1000000)]     #creates df of only low dollar contracts

# Basic Analysis
#NAs
for col, count in clean_df.isna().sum().items():
    print(f"{col}: {count}")    #find nas per col
#Size
print("The number of entries captured is: ")
print(len(clean_df))
#Transaction Amount
plt.figure(figsize=(20,6))
sns.histplot(low_value_df["Transaction Amount"], bins=50, kde=True, color="skyblue")
plt.title("Distribution of Low Value Award Amounts")
plt.xlabel("Transaction Amount ($)")
plt.ylabel("Number of Awards")
plt.xlim(0, low_value_df["Transaction Amount"].quantile(0.99))  # zoom in to 99th percentile for readability
plt.show()
#Awarding sub-agency
sub_agency_spending = low_value_df.groupby("Awarding Sub Agency")["Transaction Amount"].sum()
threshold = 0.02 * sub_agency_spending.sum()
large_agencies = sub_agency_spending[sub_agency_spending >= threshold]
small_agencies_sum = sub_agency_spending[sub_agency_spending < threshold].sum()
pie_data = pd.concat([large_agencies, pd.Series({"Other": small_agencies_sum})])
plt.figure(figsize=(8,8))
pie_data.plot(kind="pie", autopct='%1.1f%%', startangle=90, colors=sns.color_palette("pastel"))
plt.ylabel("")
plt.title("Awarding Sub-Agency Share of Total Low Value Transaction Amount")
plt.show()
#Awarded by company
company_spending = clean_df.groupby("Recipient Name")["Transaction Amount"].sum().sort_values(ascending=False)
top35_companies = company_spending.head(35)
print(top35_companies)
plt.figure(figsize=(14,8))
top35_companies.plot(kind="barh", color="steelblue")
plt.xlabel("Total Award Amount ($)")
plt.ylabel("Recipient Company")
plt.title("Top 35 Companies by Total Transaction Amount")
plt.gca().invert_yaxis()
plt.show()
#NAICS distribution
naics_counts = clean_df["naics_description"].value_counts()
threshold_naics = 0.07 * naics_counts.sum()
large_naics = naics_counts[naics_counts >= threshold_naics]
small_naics_sum = naics_counts[naics_counts < threshold_naics].sum()
naics_pie_data = pd.concat([large_naics, pd.Series({"Other": small_naics_sum})]).sort_values(ascending=False)
plt.figure(figsize=(8,8))
naics_pie_data.plot(kind="pie", autopct='%1.1f%%', startangle=90, colors=sns.color_palette("pastel"))
plt.ylabel("")
plt.title("Distribution of NAICS Codes")
plt.show()
#PSC Distribution
psc_counts = clean_df["psc_description"].value_counts()
top20_psc = psc_counts.head(20)
top20_psc_df = top20_psc.reset_index()
top20_psc_df.columns = ["PSC Description", "Number of Awards"]
print(top20_psc_df)

# Geographical Analysis
#State level
spending_by_state = clean_df.groupby("pop_state")["Transaction Amount"].sum().sort_values(ascending=False)
fig = px.choropleth(
    spending_by_state.reset_index(),
    locations="pop_state",
    locationmode="USA-states",
    color="Transaction Amount",
    color_continuous_scale="Blues",
    scope="usa",
    labels={"Transaction Amount":"Total Spending"}
)
fig.show()
#City level
spending_by_city = low_value_df.groupby("pop_city")["Transaction Amount"].sum().sort_values(ascending=False)
plt.figure(figsize=(12,6))
spending_by_city.head(15).plot(kind="bar", color="salmon")
plt.title("Top 15 Cities by Total Transaction Amount")
plt.ylabel("Total Spending ($)")
plt.xlabel("City")
plt.xticks(rotation=45)
plt.show()
#Difference over time in spending across states
df_2023 = low_value_df[low_value_df["Action Date"].dt.year == 2023]
df_2025 = low_value_df[low_value_df["Action Date"].dt.year == 2025]
spending_2023 = df_2023.groupby("pop_state")["Transaction Amount"].sum()
spending_2025 = df_2025.groupby("pop_state")["Transaction Amount"].sum()
state_diff = pd.DataFrame({
    "2023": spending_2023,
    "2025": spending_2025
}).fillna(0)
state_diff["Difference"] = state_diff["2025"] - state_diff["2023"]
state_diff = state_diff.reset_index()
fig = px.choropleth(
    state_diff,
    locations="pop_state",
    locationmode="USA-states",
    color="Difference",
    color_continuous_scale=px.colors.diverging.RdYlBu,  # red=decrease, blue=increase
    scope="usa",
    labels={"Difference": "2025-2023 Spending ($)"},
    title="Change in Total Low Value Spending by State (2025 vs 2023)"
)
fig.show()
#State spending for space related psc
space_psc_codes = ["1560", "1561", "1562", "1563", "1564", "1565", "1566", "1567"]
space_df = clean_df[clean_df["psc_code"].isin(space_psc_codes)]
spending_by_state = space_df.groupby("pop_state")["Transaction Amount"].sum().sort_values(ascending=False)
fig = px.choropleth(
    spending_by_state.reset_index(),
    locations="pop_state",
    locationmode="USA-states",
    color="Transaction Amount",
    color_continuous_scale="Blues",
    scope="usa",
    labels={"Transaction Amount":"Total Spending"},
    title="Total Space-Related Spending by State"
)
fig.show()
#City spending for space related psc
spending_by_city = space_df.groupby("pop_city")["Transaction Amount"].sum().sort_values(ascending=False)
plt.figure(figsize=(12,6))
spending_by_city.head(15).plot(kind="bar", color="salmon")
plt.title("Top 15 Cities by Space-Related Transaction Amount")
plt.ylabel("Total Spending ($)")
plt.xlabel("City")
plt.xticks(rotation=45)
plt.show()
#Department spending by state
navy_df = low_value_df[low_value_df["Awarding Sub Agency"] == "Department of the Navy"]
spending_by_state = navy_df.groupby("pop_state")["Transaction Amount"].sum().sort_values(ascending=False)
fig = px.choropleth(
    spending_by_state.reset_index(),
    locations="pop_state",
    locationmode="USA-states",
    color="Transaction Amount",
    color_continuous_scale="Blues",
    scope="usa",
    labels={"Transaction Amount":"Total Spending"}
)
fig.show()

# Lead time analysis
#Filter to common PSCs
psc_counts = low_value_df["psc_description"].value_counts()
psc_to_keep = psc_counts[psc_counts >= 100].index
common_psc_df = low_value_df[low_value_df["psc_description"].isin(psc_to_keep)]
#PSC Lead times
overall_avg_lead_time = common_psc_df["lead_time"].mean()
print(f"Overall average lead time: {overall_avg_lead_time:.2f} days")
psc_lead_time = common_psc_df.groupby("psc_description")["lead_time"].mean().sort_values(ascending=False)
top15_psc_lead_time = psc_lead_time.head(15)
print("\nTop 15 PSCs by average lead time:")
print(top15_psc_lead_time)
#State lead times
state_avg_lead_time = low_value_df.groupby("pop_state")["lead_time"].mean().reset_index()
fig = px.choropleth(
    state_avg_lead_time,
    locations="pop_state",
    locationmode="USA-states",
    color="lead_time",
    color_continuous_scale=["blue","white","red"],  # blue = short, red = long
    scope="usa",
    labels={"lead_time":"Average Lead Time (days)"},
    title="Average Lead Time by State for Low Value Awards"
)
fig.show()
