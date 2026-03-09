import pandas as pd
from datetime import datetime

EXPECTED_COLS = [
    'amt', 'zip', 'lat', 'long', 'city_pop', 'merch_lat', 'merch_long', 
    'age', 'hour', 'day', 'month',
    'category_food_dining', 'category_gas_transport', 'category_grocery_net', 
    'category_grocery_pos', 'category_health_fitness', 'category_home', 
    'category_kids_pets', 'category_misc_net', 'category_misc_pos', 
    'category_personal_care', 'category_shopping_net', 'category_shopping_pos', 
    'category_travel'
]

def prepare_features(txn: dict, velocity: dict) -> pd.DataFrame:
    """
    Transforms raw JSON transaction and redis velocity to the matching ML feature schema.
    Velocity features are returned alongside, but might be used by a rule-based engine instead of XGBoost.
    """
    dob = datetime.strptime(txn["dob"], "%Y-%m-%d")
    trans = datetime.strptime(txn["trans_date_trans_time"], "%Y-%m-%d %H:%M:%S")
    age = (trans - dob).days // 365

    features = {
        'amt': float(txn['amt']),
        'zip': int(txn['zip']),
        'lat': float(txn['lat']),
        'long': float(txn['long']),
        'city_pop': int(txn['city_pop']),
        'merch_lat': float(txn['merch_lat']),
        'merch_long': float(txn['merch_long']),
        'age': age,
        'hour': trans.hour,
        'day': trans.day,
        'month': trans.month
    }

    # Set dummy categorical columns
    cat_col = f"category_{txn['category']}"
    for col in EXPECTED_COLS:
        if col.startswith("category_"):
            features[col] = 1 if col == cat_col else 0

    df = pd.DataFrame([features])
    return df[EXPECTED_COLS]
