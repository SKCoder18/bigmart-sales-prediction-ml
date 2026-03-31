from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import pickle
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import io
import os

# Initialize Flask app and enable CORS
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Load model and columns
try:
    with open("rforest_model.pkl", "rb") as f:
        model = pickle.load(f)

    with open("preprocessing_metadata.pkl", "rb") as f:
        metadata = pickle.load(f)

    columns = metadata["columns"]
except Exception as e:
    logging.error(f"Error loading model or metadata: {e}")
    raise

# Initialize SQLite database and create users table if not exists
def init_db():
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logging.error(f"Error initializing database: {e}")
        raise

init_db()

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    password_hash = generate_password_hash(password)
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        conn.close()
        return jsonify({"message": "User registered successfully"})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 400
    except sqlite3.Error as e:
        logging.error(f"Database error during registration: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()

        if row and check_password_hash(row[0], password):
            return jsonify({"message": "Login successful"})
        else:
            return jsonify({"error": "Invalid username or password"}), 401
    except sqlite3.Error as e:
        logging.error(f"Database error during login: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        logging.debug(f"Received input data for prediction: {data}")

        required_fields = ["Item_Identifier", "Item_Weight", "Item_Fat_Content", "Item_Visibility", "Item_Type",
                           "Item_MRP", "Outlet_Identifier", "Outlet_Establishment_Year", "Outlet_Size",
                           "Outlet_Location_Type", "Outlet_Type"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        df = pd.DataFrame([data])
        logging.debug(f"Input DataFrame before preprocessing: {df}")

        df['Item_Fat_Content'] = df['Item_Fat_Content'].replace({
            'LF': 'Low Fat', 'low fat': 'Low Fat', 'reg': 'Regular'
        })
        df = pd.get_dummies(df)
        df = df.reindex(columns=columns, fill_value=0)
        logging.debug(f"Input DataFrame after preprocessing: {df}")

        prediction = model.predict(df)[0]
        logging.debug(f"Prediction result: {prediction}")

        return jsonify({"Item_Outlet_Sales": round(float(prediction), 2)})
    except Exception as e:
        logging.error(f"Error during prediction: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/products", methods=["GET"])
def get_products():
    try:
        data = pd.read_csv("test.csv")
        products = data[[
            "Item_Identifier", "Item_Type", "Item_Weight", "Item_Fat_Content", "Item_MRP", "Item_Visibility",
            "Outlet_Establishment_Year", "Outlet_Identifier", "Outlet_Size", "Outlet_Location_Type", "Outlet_Type"
        ]]
        products = products.rename(columns={
            "Item_Identifier": "id",
            "Item_Type": "name",
            "Item_Weight": "weight",
            "Item_Fat_Content": "fatContent",
            "Item_MRP": "price",
            "Item_Visibility": "visibility",
            "Outlet_Establishment_Year": "establishedYear",
            "Outlet_Identifier": "outletIdentifier",
            "Outlet_Size": "outletSize",
            "Outlet_Location_Type": "outletLocationType",
            "Outlet_Type": "outletType"
        })
        product_list = products.to_dict(orient="records")
        for product in product_list:
            for key, value in product.items():
                if isinstance(value, float) and (value != value):  # NaN check
                    product[key] = None
        return jsonify(product_list)
    except Exception as e:
        logging.error(f"Error fetching products: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/test-products", methods=["GET"])
def get_test_products():
    try:
        data = pd.read_csv("test.csv")
        products = data[[
            "Item_Identifier", "Item_Type", "Item_Weight", "Item_Fat_Content", "Item_MRP",
            "Outlet_Establishment_Year", "Outlet_Identifier", "Outlet_Size", "Outlet_Location_Type", "Outlet_Type"
        ]]
        products = products.rename(columns={
            "Item_Identifier": "id",
            "Item_Type": "name",
            "Item_Weight": "weight",
            "Item_Fat_Content": "fatContent",
            "Item_MRP": "price",
            "Outlet_Establishment_Year": "establishedYear",
            "Outlet_Identifier": "outletIdentifier",
            "Outlet_Size": "outletSize",
            "Outlet_Location_Type": "outletLocationType",
            "Outlet_Type": "outletType"
        })
        product_list = products.to_dict(orient="records")
        for product in product_list:
            for key, value in product.items():
                if isinstance(value, float) and (value != value):  # NaN check
                    product[key] = None
        return jsonify(product_list)
    except Exception as e:
        logging.error(f"Error fetching test products: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/save-prediction", methods=["POST"])
def save_prediction():
    try:
        data = request.get_json()
        username = data.get("username")  # Expecting username to be sent in the request
        if not username:
            return jsonify({"error": "Username is required"}), 400

        # Ensure the file path is consistent
        file_path = os.path.join(os.getcwd(), f"{username}_predicted_sales.csv")

        # Ensure all required fields are present
        required_fields = [
            "Item_Identifier", "Item_Weight", "Item_Fat_Content", "Item_Visibility", "Item_Type",
            "Item_MRP", "Outlet_Identifier", "Outlet_Establishment_Year", "Outlet_Size",
            "Outlet_Location_Type", "Outlet_Type", "Predicted_Sales"
        ]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        # Convert data to DataFrame
        df = pd.DataFrame([data])

        # Append to the existing file or create a new one
        try:
            if os.path.exists(file_path):
                df.to_csv(file_path, mode="a", header=False, index=False)
            else:
                df.to_csv(file_path, index=False)
        except PermissionError:
            logging.error("Permission denied: Ensure the file is not open in another program.")
            return jsonify({"error": "Permission denied: Close the file if it is open in another program"}), 500
        except Exception as e:
            logging.error(f"Error writing to CSV file: {e}")
            return jsonify({"error": "Failed to write to CSV file"}), 500

        return jsonify({"message": "Prediction saved successfully"})
    except Exception as e:
        logging.error(f"Error saving prediction: {e}")
        return jsonify({"error": "Failed to save prediction"}), 500

@app.route("/download-predictions", methods=["POST"])
def download_predictions():
    try:
        data = request.get_json()
        username = data.get("username")  # Expecting username to be sent in the request
        if not username:
            return jsonify({"error": "Username is required"}), 400

        file_path = f"{username}_predicted_sales.csv"
        if not os.path.exists(file_path):
            return jsonify({"error": "No predictions to download"}), 400

        with open(file_path, "r") as file:
            csv_data = file.read()

        return csv_data, 200, {"Content-Type": "text/csv"}
    except Exception as e:
        logging.error(f"Error generating CSV file: {e}")
        return jsonify({"error": "Failed to generate CSV file"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5001)
