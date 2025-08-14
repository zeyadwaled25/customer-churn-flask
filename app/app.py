from flask import Flask, render_template, request
import joblib
import pandas as pd
import os

app = Flask(__name__)

# Load the trained pipeline
model = joblib.load("best_pipeline.pkl")

# Columns expected by the model (must match training data order exactly)
expected_columns = [
    'Senior Citizen', 'Partner', 'Dependents',
    'Tenure Months', 'Paperless Billing', 'Monthly Charges',
    'Internet Service_Fiber optic', 'Internet Service_No',
    'Online Security_Yes', 'Online Backup_Yes', 'Device Protection_Yes',
    'Tech Support_Yes', 'Streaming TV_Yes', 'Streaming Movies_Yes',
    'Sum_Of_Services', 'Tenure Category_Old_Customers',
    'Contract_One year', 'Contract_Two year', 'Is Manual Payment'
]

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    # Read numerical inputs from form
    monthly_charges = float(request.form['monthly_charges'])
    total_charges = float(request.form['total_charges'])  # Display only
    tenure = int(request.form['tenure'])

    # Initialize dictionary with numeric and derived features
    input_dict = {
        'Monthly Charges': monthly_charges,
        'Tenure Months': tenure,
        'Tenure Category_Old_Customers': 1 if tenure >= 12 else 0,
        'Contract_One year': 1 if request.form['contract_type'] == "One year" else 0,
        'Contract_Two year': 1 if request.form['contract_type'] == "Two year" else 0,
        'Is Manual Payment': 1 if request.form['payment_method'] in ["Electronic check", "Mailed check"] else 0,
        'Internet Service_Fiber optic': 1 if request.form['internet_service'] == "Fiber optic" else 0,
        'Internet Service_No': 1 if request.form['internet_service'] == "No" else 0
    }

    # Mapping Yes/No inputs to binary columns
    yes_no_mappings = {
        'senior_citizen': 'Senior Citizen',
        'partner': 'Partner',
        'dependents': 'Dependents',
        'paperless_billing': 'Paperless Billing',
        'online_security': 'Online Security_Yes',
        'online_backup': 'Online Backup_Yes',
        'device_protection': 'Device Protection_Yes',
        'tech_support': 'Tech Support_Yes',
        'streaming_tv': 'Streaming TV_Yes',
        'streaming_movies': 'Streaming Movies_Yes'
    }

    # Add Yes/No columns and calculate Sum_Of_Services
    sum_of_services = 0
    for form_key, model_col in yes_no_mappings.items():
        val = 1 if request.form.get(form_key) == "Yes" else 0
        input_dict[model_col] = val
        # Count service-related yes values for Sum_Of_Services
        if model_col in [
            'Online Security_Yes', 'Online Backup_Yes', 'Device Protection_Yes',
            'Tech Support_Yes', 'Streaming TV_Yes', 'Streaming Movies_Yes'
        ]:
            sum_of_services += val

    input_dict['Sum_Of_Services'] = sum_of_services

    # Create DataFrame and ensure all expected columns exist
    input_df = pd.DataFrame([input_dict])
    for col in expected_columns:
        if col not in input_df.columns:
            input_df[col] = 0

    # Reorder columns to match training data
    input_df = input_df[expected_columns]

    # Prediction
    pred_class = model.predict(input_df)[0]
    pred_prob = model.predict_proba(input_df)[0][pred_class] * 100
    result = "Customer will Churn" if pred_class == 1 else "Customer will Stay"

    return render_template(
        "result.html",
        prediction=result,
        probability=f"{pred_prob:.2f}%",
        prediction_class_name="positive" if pred_class == 1 else "negative",
        prediction_class="text-danger" if pred_class == 1 else "text-success",
        monthly_charges=monthly_charges,
        total_charges=total_charges,
        tenure=tenure,
        contract_type=request.form['contract_type'],
        payment_method=request.form['payment_method']
    )

@app.route("/visualizations")
def visualizations():
    # Path of images Folder
    img_folder = os.path.join(app.static_folder, "visualizations")
    images = os.listdir(img_folder)  # All Photos

    return render_template("visualization.html", images=images)

@app.route("/about")
def about():
    return render_template("about.html")

if __name__ == "__main__":
    app.run(debug=True)