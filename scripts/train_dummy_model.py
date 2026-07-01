import os
import joblib
import numpy as np

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression


MODEL_PATH = "models/credit_risk_model.joblib"


def create_training_data():
    """
    Creates simple synthetic credit-risk-style data.

    Features:
    0. credit_score
    1. annual_income
    2. existing_loans
    3. has_default_history
    4. employment_years

    Target:
    0 = low risk
    1 = high risk
    """

    np.random.seed(42)

    total_rows = 1000

    credit_score = np.random.randint(300, 851, total_rows)
    annual_income = np.random.randint(20000, 150001, total_rows)
    existing_loans = np.random.randint(0, 8, total_rows)
    has_default_history = np.random.randint(0, 2, total_rows)
    employment_years = np.random.randint(0, 31, total_rows)

    X = np.column_stack([
        credit_score,
        annual_income,
        existing_loans,
        has_default_history,
        employment_years
    ])

    # Simple rule to create labels.
    # This is not a real credit-risk model.
    # It only gives us a model for inference testing.
    y = (
        (credit_score < 600) |
        (annual_income < 40000) |
        (existing_loans >= 5) |
        (has_default_history == 1)
    ).astype(int)

    return X, y


def train_and_save_model():
    X, y = create_training_data()

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(max_iter=1000))
    ])

    model.fit(X, y)

    os.makedirs("models", exist_ok=True)

    model_package = {
        "model": model,
        "feature_count": 5,
        "model_version": "dummy-credit-risk-v1",
        "feature_names": [
            "credit_score",
            "annual_income",
            "existing_loans",
            "has_default_history",
            "employment_years"
        ]
    }

    joblib.dump(model_package, MODEL_PATH)

    print(f"Model saved successfully at: {MODEL_PATH}")


if __name__ == "__main__":
    train_and_save_model()