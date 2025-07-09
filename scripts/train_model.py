import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import joblib

# Paths (keep directory structure intact)
FEATURES_PATH = os.path.join(os.path.dirname(__file__), '..', 'features', 'dataset.csv')
MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'model')
os.makedirs(MODEL_DIR, exist_ok=True)

# Load dataset
df = pd.read_csv(FEATURES_PATH)

# Encode labels
df['label'] = df['label'].map({'real': 1, 'fake': 0})

# Split features and target
X = df.drop('label', axis=1)
y = df['label']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Optional: Scale features (not required for Random Forest but included for pipeline compatibility)
scaler = StandardScaler()

# Define base model
base_model = RandomForestClassifier(random_state=42)

# Grid search hyperparameter tuning
param_grid = {
    'classifier__n_estimators': [100, 200],
    'classifier__max_depth': [10, 20, None],
    'classifier__min_samples_split': [2, 5],
    'classifier__max_features': ['sqrt', 'log2', None]
}

# Build pipeline
pipeline = Pipeline([
    ('scaler', scaler),
    ('classifier', base_model)
])

# Perform grid search with cross-validation
grid_search = GridSearchCV(pipeline, param_grid, cv=5, n_jobs=-1, scoring='accuracy')
grid_search.fit(X_train, y_train)

# Get best model from grid search
best_model = grid_search.best_estimator_
print("Best hyperparameters found:", grid_search.best_params_)

# Evaluate on test set
y_pred = best_model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Test Accuracy: {accuracy * 100:.2f}%")

# Additional evaluation metrics
print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))
print("Classification Report:")
print(classification_report(y_test, y_pred))

# Cross-validation accuracy on entire dataset
cv_scores = cross_val_score(best_model, X, y, cv=5, scoring='accuracy')
print(f"Mean Cross-Validation Accuracy: {np.mean(cv_scores) * 100:.2f}%")

# Extract feature importances from the RandomForest model inside the pipeline
rf_model = best_model.named_steps['classifier']
importances = rf_model.feature_importances_
feature_names = X.columns
sorted_idx = np.argsort(importances)[::-1]

print("\nTop Feature Importances:")
for idx in sorted_idx:
    print(f"{feature_names[idx]}: {importances[idx]:.4f}")

# Save the full pipeline (model + preprocessing)
MODEL_PATH = os.path.join(MODEL_DIR, 'rolex_model.pkl')
joblib.dump(best_model, MODEL_PATH)
print(f"Model saved to {MODEL_PATH}")
