import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import pickle

# Load dataset
data = pd.read_csv("Train.csv")

# Fill missing values
data['Item_Weight'].fillna(data['Item_Weight'].mean(), inplace=True)
data['Outlet_Size'].fillna(data['Outlet_Size'].mode()[0], inplace=True)
data['Item_Visibility'] = data['Item_Visibility'].replace(0, data['Item_Visibility'].mean())

# Normalize Fat Content
data['Item_Fat_Content'] = data['Item_Fat_Content'].replace({
    'LF': 'Low Fat', 'low fat': 'Low Fat', 'reg': 'Regular'
})

# Split data
y = data['Item_Outlet_Sales']
X = data.drop(['Item_Outlet_Sales'], axis=1)

# Encode
X_encoded = pd.get_dummies(X)
columns = X_encoded.columns.tolist()

# Save metadata
with open("preprocessing_metadata.pkl", "wb") as f:
    pickle.dump({"columns": columns}, f)

# Train
X_train, X_test, y_train, y_test = train_test_split(X_encoded, y, test_size=0.2, random_state=42)
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Save model
with open("rforest_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("✅ Model and metadata saved!")
