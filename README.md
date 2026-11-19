# Beta Bank Retention Desk: customer attrition application

**Live app:** [beta-retention-desk-application.streamlit.app](https://beta-retention-desk-application.streamlit.app/) · **Notebook and project folder:** [AIOPS-Portfolio-Projects](https://github.com/ahmadhassan-aiops/AIOPS-Portfolio-Projects/tree/main/2.%20Machine%20Learning%20Projects/customer%20attrition%20at%20Beta%20Bank%20using%20ML)

A retention console for Beta Bank, by **Ahmad Hassan** (AI Engineer). Customers are leaving the bank little by
little, and keeping them is cheaper than winning new ones. A tuned XGBoost pipeline, trained on 8,000 customers and
tested once on 2,000 it never saw, **meets the brief with F1 0.631 (target 0.59) and AUC-ROC 0.864**, and its
probabilities match real churn rates, so they can be multiplied by balances to show deposits at risk.

- **Worklist**: today's call queue, ranked by deposits at risk or chance of leaving, with each customer's main
  reasons; a treemap of where the deposits at risk sit; the full scored list (select a row to open the file);
  upload your own customer file.
- **Customer file**: an LED risk meter and profile sheet, a SHAP waterfall from the average customer to this one,
  and **retention levers**: the model's score if the bank re-activates the customer, moves them to two products or
  adds a credit card, with a recommended play.
- **Churn map**: age by country, age by activity, products, country and gender.
- **Scorecard**: the F1 target check, an interactive act line with F1/recall/precision and the confusion matrix,
  ROC, calibration, how class imbalance was handled, and a fair comparison with the first version's model.
- **Method**: data, model search, fixes to the first notebook, limits.

## Why this stack

| Need | Choice |
|---|---|
| An internal tool for a retention team: queues, filters, drill-down to a customer, what-if levers | **Streamlit** with sidebar navigation and session state for the worklist-to-file flow |
| One artefact from raw record to probability | **scikit-learn `Pipeline`** (one-hot encoding, median imputation of tenure, XGBoost), saved with `joblib` |
| Ranking on tabular data, calibrated probabilities, exact explanations | **XGBoost** with native SHAP values; tied with gradient boosting and random forest in cross-validation |
| Reject bad uploads | **pydantic** schema per row |
| Trust that the shipped file is the evaluated model | **pytest** + GitHub Actions: scores, F1/AUC, SHAP additivity, levers, validation, every screen |

`retention/` has no Streamlit dependency, so the same model and levers can sit behind an API for a CRM.

## How it is built

```
app.py              entry point (sidebar navigation, logo)
nav.py              screen registry
screens/            worklist, customer_file, churn_map, scorecard, method
retention/          schema.py (pydantic), model.py (scores, SHAP, status, retention levers)
desk/               dark console UI kit, Plotly charts, theme, value formatting, cached loaders
model/              beta_bank_attrition_xgb.joblib + metadata.json
data/               held-out book with names and scores, all customers, reference statistics
train.py            rebuilds model/ and data/ from Churn.csv
tests/              model and screen tests
```

## Run locally

```bash
pip install -r requirements-dev.txt
pytest -q
streamlit run app.py
python train.py "path/to/Churn.csv"   # rebuild the model and data
```

## Data

10,000 anonymised customers of Beta Bank (a case-study bank in France, Germany and Spain). Scores are a
demonstration, not financial advice. The retention levers show how the model's score changes, not proven effects.
