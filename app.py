from flask import Flask, request, jsonify
import pandas as pd
import joblib
import mysql.connector
from mysql.connector import Error
from sklearn.preprocessing import LabelEncoder
from surprise import SVD, Dataset, Reader

app = Flask(__name__)

class Database:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                self.cursor = self.connection.cursor()
                print("Successfully connected to the database")
        except Error as e:
            print(f"Error: {e}")

    def fetch_data(self, query):
        try:
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            print(f"Error fetching data: {e}")
            return []

    def close_connection(self):
        if self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            print("MySQL connection closed.")


# Database configuration
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "rekomendasi_kegiatan"
MODEL_PATH = "tuned_svd_model.joblib"

# Load the pre-trained model
model = joblib.load(MODEL_PATH)
print("Model loaded successfully.")

@app.route('/get_recommendations', methods=['GET'])
def get_recommendations():
    try:
        # Initialize and connect to the database for each request
        db = Database(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
        db.connect()

        # Fetch data from the database (including kegiatan column)
        query = "SELECT NPM, KATEGORI, rating, kegiatan FROM merged_data_1;"
        data_from_db = db.fetch_data(query)

        if not data_from_db:
            db.close_connection()
            return jsonify({"error": "No data found in the database"}), 404

        # Convert data to DataFrame
        df = pd.DataFrame(data_from_db, columns=["NPM", "KATEGORI", "rating", "KEGIATAN"])

        # Encode categorical data
        le_user = LabelEncoder()
        le_item = LabelEncoder()
        df["NPM_encoded"] = le_user.fit_transform(df["NPM"])
        df["KATEGORI_encoded"] = le_item.fit_transform(df["KATEGORI"])

        # Get sample user NPM from request args
        sample_user_npm = request.args.get('npm', type=int)

        if sample_user_npm not in df["NPM"].values:
            db.close_connection()
            return jsonify({"error": f"User {sample_user_npm} not found in the database!"}), 404

        sample_user_encoded = le_user.transform([sample_user_npm])[0]

        # Generate predictions for all categories
        all_categories = df["KATEGORI_encoded"].unique()
        recommendations = []

        for category_encoded in all_categories:
            raw_category = le_item.inverse_transform([category_encoded])[0]
            # Find the corresponding kegiatan for this category
            kegiatan_name = df[df["KATEGORI_encoded"] == category_encoded]["KEGIATAN"].iloc[0]
            prediction = model.predict(uid=sample_user_encoded, iid=category_encoded)
            recommendations.append({
                "category": raw_category,
                "predicted_rating": prediction.est,
                "kegiatan": kegiatan_name
            })

        # Sort by predicted rating in descending order
        recommendations.sort(key=lambda x: x['predicted_rating'], reverse=True)

        # Close the database connection
        db.close_connection()

        # Return top 3 recommendations as JSON
        return jsonify(recommendations[:3])

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "An error occurred while fetching recommendations"}), 500


@app.route('/')
def index():
    return jsonify({"message": "Welcome to the Recommendation API"})


if __name__ == "__main__":
    app.run(debug=True)
