import pandas as pd
import joblib
import mysql.connector
from mysql.connector import Error
from sklearn.preprocessing import LabelEncoder
from surprise import SVD, Dataset, Reader

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

# Main execution block
if __name__ == "__main__":
    # Database configuration
    DB_HOST = "localhost"
    DB_USER = "root"
    DB_PASSWORD = ""
    DB_NAME = "rekomendasi_kegiatan"

    # Path to the trained model
    model_path = "tuned_svd_model.joblib"

    # Create an instance of the Database class
    db = Database(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)

    # Test the database connection
    print("Testing database connection...")
    db.connect()

    try:
        # Fetch data from the database (including kegiatan column)
        query = "SELECT NPM, KATEGORI, rating, kegiatan FROM merged_data_1;"
        data_from_db = db.fetch_data(query)

        # Check if data is fetched successfully
        if not data_from_db:
            raise Exception("No data fetched from the database!")

        # Convert data to a DataFrame
        df = pd.DataFrame(data_from_db, columns=["NPM", "KATEGORI", "rating", "KEGIATAN"])

        # Encode categorical data
        le_user = LabelEncoder()
        le_item = LabelEncoder()
        df["NPM_encoded"] = le_user.fit_transform(df["NPM"])
        df["KATEGORI_encoded"] = le_item.fit_transform(df["KATEGORI"])

        # Load the pre-trained model
        model = joblib.load(model_path)
        print("Model loaded successfully.")

        # Test predictions for a sample user
        sample_user_npm = 1931005  # Replace with an actual NPM value
        if sample_user_npm not in df["NPM"].values:
            print(f"User {sample_user_npm} not found in the database!")
        else:
            sample_user_encoded = le_user.transform([sample_user_npm])[0]

            # Generate predictions for all categories
            all_categories = df["KATEGORI_encoded"].unique()
            recommendations = []

            for category_encoded in all_categories:
                raw_category = le_item.inverse_transform([category_encoded])[0]
                # Find the corresponding kegiatan for this category
                kegiatan_name = df[df["KATEGORI_encoded"] == category_encoded]["KEGIATAN"].iloc[0]
                prediction = model.predict(uid=sample_user_encoded, iid=category_encoded)
                recommendations.append((raw_category, prediction.est, kegiatan_name))

            # Sort by predicted rating in descending order
            recommendations.sort(key=lambda x: x[1], reverse=True)

            # Display the top 3 recommendations
            print("Top 3 Predicted Categories:")
            for category, predicted_rating, kegiatan_name in recommendations[:3]:
                print(f"Category: {category}, Predicted Rating: {predicted_rating}, Kegiatan: {kegiatan_name}")

    except Exception as e:
        print(f"Error: {e}")

    # Close the database connection
    db.close_connection()
