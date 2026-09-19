import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix

def prepare_data(df):
    """Filter to a clean binary classification problem and select features."""
    # Drop the ambiguous '-1' class — we're only predicting benign (0) vs pathogenic (1)
    df = df[df["ClinSigSimple"].isin([0, 1])].copy()

    features = ["Type", "NumberSubmitters", "ReviewStatus"]
    X = df[features]
    y = df["ClinSigSimple"]
    return X, y

def build_pipeline():
    """Build a preprocessing + model pipeline.
    'Type' and 'ReviewStatus' are categorical text — need to be one-hot encoded
    (turned into 0/1 columns per category) since models need numbers, not strings.
    'NumberSubmitters' is already numeric, so it passes through unchanged."""
    categorical_features = ["Type", "ReviewStatus"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features)
        ],
        remainder="passthrough"  # keep NumberSubmitters as-is
    )

    pipeline = Pipeline([
        ("preprocess", preprocessor),
        ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced"))
    ])
    return pipeline

def train_and_evaluate(X, y):
    """Split data, train the model, and report how well it performs."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)

    print(classification_report(y_test, y_pred, target_names=["Not pathogenic", "Pathogenic"]))
    print("Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))

    return pipeline