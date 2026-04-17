"""
Machine Learning Core Module — Multi-Model Ensemble
====================================================
Uses 6 different classifiers and combines them via soft-voting
for a more robust heart disease prediction.

Models used:
  1. Logistic Regression
  2. Random Forest Classifier
  3. Support Vector Machine (SVM)
  4. K-Nearest Neighbors (KNN)
  5. Gradient Boosting (HistGradientBoostingClassifier)
  6. Multi-Layer Perceptron (Neural Network)
"""
import os
import warnings
import joblib
import pandas as pd
import numpy as np

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier, VotingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from sklearn.exceptions import ConvergenceWarning

# Suppress convergence warnings during training
warnings.filterwarnings("ignore", category=ConvergenceWarning)

# ── Path Configuration ──
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BACKEND_DIR)
DATASETS_DIR = os.path.join(PROJECT_DIR, 'datasets')
MODEL_PATH = os.path.join(PROJECT_DIR, 'model.pkl')

DATASET_FILES = [
    "heart.csv",
    "heart_dataset_bharath0609_304.csv",
    "heart_dataset_jocelyndumlao_1000.csv",
    "heart_dataset_RafaelGranza_1026.csv",
    "heart_dataset_rishidamarla_271.csv",
]

FEATURE_COLS = ['age', 'sex', 'cp', 'trestbps', 'chol', 'fbs',
                'restecg', 'thalach', 'exang', 'oldpeak',
                'slope', 'ca', 'thal']

# ── Individual model definitions ──────────────────────────────────────────────

MODELS = {
    "Logistic Regression": LogisticRegression(
        max_iter=1000,
        C=1.0,
        solver='lbfgs',
        random_state=42,
    ),
    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    ),
    "SVM (RBF Kernel)": SVC(
        kernel='rbf',
        C=1.0,
        gamma='scale',
        probability=True,   # required for soft voting
        random_state=42,
    ),
    "K-Nearest Neighbors": KNeighborsClassifier(
        n_neighbors=7,
        weights='distance',
        metric='minkowski',
    ),
    "Gradient Boosting": HistGradientBoostingClassifier(
        learning_rate=0.1,
        max_iter=200,
        max_depth=5,
        l2_regularization=0.1,
        random_state=42,
    ),
    "Neural Network (MLP)": MLPClassifier(
        hidden_layer_sizes=(128, 64, 32),
        activation='relu',
        solver='adam',
        max_iter=500,
        learning_rate='adaptive',
        random_state=42,
    ),
}

# ── Data loading & cleaning ───────────────────────────────────────────────────

def _load_data():
    """Load and clean all CSV datasets from datasets/ directory."""
    target_col = 'target'
    frames = []
    for filename in DATASET_FILES:
        path = os.path.join(DATASETS_DIR, filename)
        if os.path.exists(path):
            frames.append(pd.read_csv(path, encoding='utf-8-sig'))

    if not frames:
        raise FileNotFoundError(
            f"No dataset files found in {DATASETS_DIR}! "
            "Place CSV files in the datasets/ directory."
        )

    df = pd.concat(frames, ignore_index=True)
    available_cols = [c for c in FEATURE_COLS + [target_col] if c in df.columns]
    df = df[available_cols].drop_duplicates().dropna(subset=[target_col])

    for col in FEATURE_COLS:
        if col in df.columns and df[col].isnull().any():
            df[col] = df[col].fillna(df[col].median())

    df[target_col] = df[target_col].astype(int)
    return df[FEATURE_COLS], df[target_col]

# ── Training ─────────────────────────────────────────────────────────────────

def train_all_models():
    """
    Train every individual model + a soft-voting ensemble.
    Returns (ensemble_model, individual_models_dict, scaler, cv_scores_dict).
    """
    X_raw, y = _load_data()

    scaler = StandardScaler()
    X = scaler.fit_transform(X_raw)

    trained_models = {}
    cv_scores = {}

    print(f"  {'Model':<28} {'CV Accuracy':>12}")
    print("-" * 44)

    for name, estimator in MODELS.items():
        estimator.fit(X, y)
        scores = cross_val_score(estimator, X, y, cv=5, scoring='accuracy')
        mean_acc = scores.mean()
        cv_scores[name] = {
            "mean": round(float(mean_acc), 4),
            "std": round(float(scores.std()), 4),
        }
        trained_models[name] = estimator
        print(f"  {name:<28} {mean_acc:.4f} ± {scores.std():.4f}")

    # Build soft-voting ensemble from trained estimators
    ensemble = VotingClassifier(
        estimators=[(name, est) for name, est in trained_models.items()],
        voting='soft',
    )
    ensemble.estimators_ = list(trained_models.values())
    ensemble.le_ = None
    ensemble.classes_ = np.array([0, 1])
    ensemble.fit(X, y)

    ens_scores = cross_val_score(ensemble, X, y, cv=5, scoring='accuracy')
    cv_scores["Ensemble (Soft Vote)"] = {
        "mean": round(float(ens_scores.mean()), 4),
        "std": round(float(ens_scores.std()), 4),
    }
    print(f"  {'Ensemble (Soft Vote)':<28} {ens_scores.mean():.4f} ± {ens_scores.std():.4f}")
    print("-" * 44)

    return ensemble, trained_models, scaler, cv_scores


def _load_or_train():
    """Load model from model.pkl if available, otherwise train from scratch."""
    if os.path.exists(MODEL_PATH):
        print("=" * 50)
        print("  HeartGuard AI — Loading saved model...")
        print("=" * 50)
        data = joblib.load(MODEL_PATH)
        print(f"  Loaded model with {len(data['individual_models'])} sub-models")
        print("[OK] Model loaded successfully.\n")
        return (
            data['ensemble_model'],
            data['individual_models'],
            data['scaler'],
            data['cv_scores']
        )
    else:
        print("=" * 50)
        print("  HeartGuard AI — Training 6 ML Models...")
        print("  (No model.pkl found — run train_model.py to pre-train)")
        print("=" * 50)
        result = train_all_models()
        print("\n[OK] All models trained successfully.\n")
        return result


# ── Load model at module import ──────────────────────────────────────────────

ensemble_model, individual_models, scaler, model_cv_scores = _load_or_train()

# ── Prediction API ────────────────────────────────────────────────────────────

def predict_heart_disease(patient_data):
    """
    Takes a dictionary of patient data and returns:
      - ensemble prediction & probability
      - per-model predictions & probabilities
      - cross-validation accuracy scores
    """
    input_list = [patient_data.get(col, 0) for col in FEATURE_COLS]
    input_df = pd.DataFrame([input_list], columns=FEATURE_COLS)
    input_scaled = scaler.transform(input_df)

    # Ensemble result
    ens_prediction = int(ensemble_model.predict(input_scaled)[0])
    ens_probability = float(ensemble_model.predict_proba(input_scaled)[0][1])

    # Per-model breakdown
    model_details = {}
    votes_positive = 0
    for name, est in individual_models.items():
        pred = int(est.predict(input_scaled)[0])
        prob = float(est.predict_proba(input_scaled)[0][1])
        votes_positive += pred
        model_details[name] = {
            "prediction": pred,
            "probability": round(prob, 4),
            "vote": "High Risk" if pred == 1 else "Low Risk",
            "cv_accuracy": model_cv_scores.get(name, {}),
        }

    total_models = len(individual_models)

    return {
        # backward-compatible keys
        "prediction": ens_prediction,
        "probability": ens_probability,
        "risk_level": "High Risk" if ens_prediction == 1 else "Low Risk",
        # detailed keys
        "model_count": total_models,
        "votes_positive": votes_positive,
        "votes_negative": total_models - votes_positive,
        "consensus": f"{votes_positive}/{total_models} models predict High Risk",
        "model_details": model_details,
        "ensemble_cv_accuracy": model_cv_scores.get("Ensemble (Soft Vote)", {}),
    }
