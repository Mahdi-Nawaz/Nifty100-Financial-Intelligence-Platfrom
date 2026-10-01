import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import nbformat as nbf
import os
import shap
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error

base_dir = r"C:\Users\eFuture\Desktop\Bengaluru-Ola-Analytics"
data_path = os.path.join(base_dir, "1_data", "ola_bangalore_100k.csv")
exports_dir = os.path.join(base_dir, "5_exports")

# Load and clean column names
df = pd.read_csv(data_path)
df.columns = [col.replace(' ', '_') for col in df.columns]
if 'Avg_VTAT' in df.columns:
    df = df.rename(columns={'Avg_VTAT': 'VTAT'})

# Save back to CSV so SQL and PowerBI work as expected with underscores
df.to_csv(data_path, index=False)

# ---------------- EDA ----------------
# 2. Peak Hours
plt.figure(figsize=(10,5))
df['Hour'] = pd.to_datetime(df['Time'], errors='coerce').dt.hour
df['Hour'].value_counts().sort_index().plot(kind='bar')
plt.title('Rides by Hour (Peak Hours)')
plt.savefig(os.path.join(exports_dir, 'peak_hours.png'))
plt.close()

# 3. Top 10 Pickup Locations
plt.figure(figsize=(10,6))
df['Pickup_Location'].value_counts().head(10).plot(kind='barh')
plt.title('Top 10 Pickup Locations')
plt.savefig(os.path.join(exports_dir, 'top_pickup_locations.png'))
plt.close()

# 4. Success vs Cancelled
plt.figure(figsize=(8,8))
df['Booking_Status'].value_counts().plot(kind='pie', autopct='%1.1f%%')
plt.title('Booking Status: Success vs Cancelled')
plt.savefig(os.path.join(exports_dir, 'booking_status.png'))
plt.close()

# 5. Cancellation Reasons
plt.figure(figsize=(10,6))
cancel_reasons = pd.concat([df['Reason_for_Cancelling_by_Customer'], df['Reason_for_Cancelling_by_Driver']]).dropna()
cancel_reasons.value_counts().head(10).plot(kind='barh')
plt.title('Top Cancellation Reasons')
plt.savefig(os.path.join(exports_dir, 'cancellation_reasons.png'))
plt.close()

# 6. Vehicle Type Demand
plt.figure(figsize=(8,5))
df['Vehicle_Type'].value_counts().plot(kind='bar')
plt.title('Vehicle Type Demand')
plt.savefig(os.path.join(exports_dir, 'vehicle_type_demand.png'))
plt.close()

# 7. Avg Ride Distance by Vehicle
plt.figure(figsize=(8,5))
df.groupby('Vehicle_Type')['Ride_Distance'].mean().plot(kind='bar')
plt.title('Avg Ride Distance by Vehicle')
plt.savefig(os.path.join(exports_dir, 'avg_distance_vehicle.png'))
plt.close()

# 8. Revenue by Payment Method
plt.figure(figsize=(8,5))
df.groupby('Payment_Method')['Booking_Value'].sum().plot(kind='bar')
plt.title('Revenue by Payment Method')
plt.savefig(os.path.join(exports_dir, 'revenue_by_payment.png'))
plt.close()

# 9. Driver vs Customer Ratings
plt.figure(figsize=(8,5))
df[['Driver_Ratings', 'Customer_Rating']].mean().plot(kind='bar')
plt.title('Average Ratings')
plt.savefig(os.path.join(exports_dir, 'ratings.png'))
plt.close()

# 10. Weekend vs Weekday
plt.figure(figsize=(8,5))
df['Weekday'] = pd.to_datetime(df['Date']).dt.day_name()
df.groupby('Weekday')['Booking_Value'].sum().sort_values().plot(kind='bar')
plt.title('Revenue by Day of Week')
plt.savefig(os.path.join(exports_dir, 'weekend_vs_weekday.png'))
plt.close()


# ---------------- ML Model ----------------

df['Is_Weekend'] = pd.to_datetime(df['Date']).dt.dayofweek >= 5
df['Is_Peak'] = df['Hour'].isin([8,9,10,18,19,20]) # Bangalore peak

cat_cols = ['Vehicle_Type', 'Pickup_Location', 'Drop_Location']
num_cols = ['Ride_Distance', 'Hour', 'Is_Weekend', 'Is_Peak']

# Drop rows with NaNs in targets/features
df_ml = df.dropna(subset=cat_cols + num_cols + ['Booking_Value']).copy()
X = pd.get_dummies(df_ml[cat_cols + num_cols], drop_first=True)
y = df_ml['Booking_Value']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = XGBRegressor(n_estimators=150, max_depth=6, learning_rate=0.1, random_state=42)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

print(f"R2 Score: {r2_score(y_test, y_pred):.2f}")
print(f"MAE: {mean_absolute_error(y_test, y_pred):.2f}")

try:
    explainer = shap.TreeExplainer(model)
except Exception:
    explainer = shap.Explainer(model, X_train)
shap_values = explainer(X_test)
shap.summary_plot(shap_values, X_test, show=False)
plt.savefig(os.path.join(exports_dir, 'Screenshots', 'shap_plot.png'), bbox_inches='tight')
plt.close()

results = pd.DataFrame({'Actual': y_test, 'Predicted': y_pred})
results.to_csv(os.path.join(base_dir, '1_data', 'predictions_for_pbi.csv'), index=False)


# ---------------- Generate Notebooks ----------------
def create_eda_notebook():
    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell("# Phase 2: Python EDA"),
        nbf.v4.new_code_cell("""import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('../1_data/ola_bangalore_100k.csv')"""),
        nbf.v4.new_code_cell("""# 1. Shape, nulls, datatypes
print(df.shape)
print(df.isnull().sum())
print(df.dtypes)"""),
        nbf.v4.new_code_cell("""# 2. Peak Hours
df['Hour'] = pd.to_datetime(df['Time'], errors='coerce').dt.hour
df['Hour'].value_counts().plot(kind='bar')"""),
        nbf.v4.new_code_cell("""# 3. Top 10 Pickup Locations in Bangalore
df['Pickup_Location'].value_counts().head(10).plot(kind='barh')"""),
        nbf.v4.new_code_cell("""# 4. Success vs Cancelled
df['Booking_Status'].value_counts().plot(kind='pie', autopct='%1.1f%%')"""),
        nbf.v4.new_code_cell("""# 5. Cancellation Reasons
cancel_reasons = pd.concat([df['Reason_for_Cancelling_by_Customer'], df['Reason_for_Cancelling_by_Driver']]).dropna()
cancel_reasons.value_counts().head(10).plot(kind='barh')"""),
        nbf.v4.new_code_cell("""# 6. Vehicle Type demand - Auto vs Mini vs Prime
df['Vehicle_Type'].value_counts().plot(kind='bar')"""),
        nbf.v4.new_code_cell("""# 7. Avg Ride Distance by Vehicle
df.groupby('Vehicle_Type')['Ride_Distance'].mean().plot(kind='bar')"""),
        nbf.v4.new_code_cell("""# 8. Revenue by Payment Method (UPI, Cash, Card)
df.groupby('Payment_Method')['Booking_Value'].sum().plot(kind='bar')"""),
        nbf.v4.new_code_cell("""# 9. Driver vs Customer Ratings
df[['Driver_Ratings', 'Customer_Rating']].mean().plot(kind='bar')"""),
        nbf.v4.new_code_cell("""# 10. Weekend vs Weekday
df['Weekday'] = pd.to_datetime(df['Date']).dt.day_name()
df.groupby('Weekday')['Booking_Value'].sum().plot(kind='bar')""")
    ]
    with open(os.path.join(base_dir, '2_notebooks', '01_EDA.ipynb'), 'w') as f:
        nbf.write(nb, f)

def create_ml_notebook():
    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell("# Phase 3: ML Model"),
        nbf.v4.new_code_cell("""import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import shap

df = pd.read_csv('../1_data/ola_bangalore_100k.csv')"""),
        nbf.v4.new_code_cell("""# Feature Engineering - Bangalore specific
df['Hour'] = pd.to_datetime(df['Time'], errors='coerce').dt.hour
df['Is_Weekend'] = pd.to_datetime(df['Date']).dt.dayofweek >= 5
df['Is_Peak'] = df['Hour'].isin([8,9,10,18,19,20]) # Bangalore peak"""),
        nbf.v4.new_code_cell("""# Select features
cat_cols = ['Vehicle_Type', 'Pickup_Location', 'Drop_Location']
num_cols = ['Ride_Distance', 'Hour', 'Is_Weekend', 'Is_Peak']

df_ml = df.dropna(subset=cat_cols + num_cols + ['Booking_Value']).copy()
X = pd.get_dummies(df_ml[cat_cols + num_cols], drop_first=True)
y = df_ml['Booking_Value'] # Predicting Booking_Value

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)"""),
        nbf.v4.new_code_cell("""model = XGBRegressor(n_estimators=150, max_depth=6, learning_rate=0.1, random_state=42)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

print(f"R2 Score: {r2_score(y_test, y_pred):.2f}") # Aim >0.85
print(f"MAE: {mean_absolute_error(y_test, y_pred):.2f}")"""),
        nbf.v4.new_code_cell("""# Feature Importance - which factor affects ETA most?
importance = pd.DataFrame({'Feature': X.columns, 'Importance': model.feature_importances_}).sort_values('Importance', ascending=False).head(10)
importance"""),
        nbf.v4.new_code_cell("""# SHAP for explainability - MUST for AI/ML specialization
try:
    explainer = shap.TreeExplainer(model)
except Exception:
    explainer = shap.Explainer(model, X_train)
shap_values = explainer(X_test)
shap.summary_plot(shap_values, X_test)"""),
        nbf.v4.new_code_cell("""# Save predictions for Power BI
results = pd.DataFrame({'Actual': y_test, 'Predicted': y_pred})
results.to_csv('../1_data/predictions_for_pbi.csv', index=False)""")
    ]
    with open(os.path.join(base_dir, '2_notebooks', '02_XGBoost_Model.ipynb'), 'w') as f:
        nbf.write(nb, f)

create_eda_notebook()
create_ml_notebook()
