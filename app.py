# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path

app = Flask(__name__)
CORS(app)

# ============================================
# LOAD ALL MODEL FILES
# ============================================
print("=" * 50)
print("LOADING MODEL FILES...")
print("=" * 50)

model_path = Path(__file__).parent / "model"

# Load Random Forest model
rf_model = joblib.load(model_path / "random_forest_model.pkl")
scaler = joblib.load(model_path / "scaler.pkl")
business_type_mapping = joblib.load(model_path / "business_type_target_mapping.pkl")

# Load CSV lookups
brgy_lookup = pd.read_csv(model_path / "barangay_lookup.csv")
biz_competition = pd.read_csv(model_path / "business_competition_lookup.csv")

# Fix negative competitor success rates
if 'competitor_success_rate' in biz_competition.columns:
    biz_competition['competitor_success_rate'] = biz_competition['competitor_success_rate'].clip(lower=0, upper=1)

print(f"✅ Loaded {len(brgy_lookup)} barangays")
print(f"✅ Loaded {len(business_type_mapping)} business types")
print(f"✅ Competition lookup columns: {biz_competition.columns.tolist()}")

# ============================================
# HELPER FUNCTIONS
# ============================================

def find_barangay(user_input):
    if not isinstance(user_input, str):
        return None
    user_input = user_input.strip().upper()
    exact_matches = brgy_lookup[brgy_lookup["barangay"].str.upper() == user_input]
    if not exact_matches.empty:
        return exact_matches.iloc[0]["barangay"]
    for _, row in brgy_lookup.iterrows():
        brgy_name = row["barangay"].upper()
        if user_input in brgy_name or brgy_name in user_input:
            return row["barangay"]
    return None

def find_business_type(user_input):
    if not isinstance(user_input, str):
        return None
    user_input = user_input.upper().strip()
    if user_input in business_type_mapping:
        return user_input
    for bt in business_type_mapping.keys():
        if user_input in bt or bt in user_input:
            return bt
    return None

def predict_success(barangay, business_type):
    # Find matching barangay
    matched_barangay = find_barangay(barangay)
    if matched_barangay is None:
        return {"error": f"Barangay '{barangay}' not found."}
    
    # Find matching business type
    matched_business_type = find_business_type(business_type)
    if matched_business_type is None:
        return {"error": f"Business type '{business_type}' not found."}
    
    # Get barangay data
    brgy_row = brgy_lookup[brgy_lookup["barangay"] == matched_barangay].iloc[0]
    
    # Get competition data - USING CORRECT COLUMN NAMES
    comp_row = biz_competition[
        (biz_competition["barangay"].str.upper().str.strip() == matched_barangay.upper()) &
        (biz_competition["business_type"].str.upper().str.strip() == matched_business_type.upper())
    ]
    
    # Extract values
    foot_traffic_raw = float(brgy_row["foot_traffic"]) if "foot_traffic" in brgy_row else 0
    foot_traffic_log = float(brgy_row["foot_traffic_log"]) if "foot_traffic_log" in brgy_row else 0
    
    if not comp_row.empty:
        # USE CORRECT COLUMN NAME: "competition_count" (not "competition_count_raw")
        market_competition_raw = float(comp_row["competition_count"].iloc[0]) if "competition_count" in comp_row else 0
        market_competition_log = float(comp_row["competition_count_log"].iloc[0]) if "competition_count_log" in comp_row else 0
        competitor_success_rate_raw = float(comp_row["competitor_success_rate"].iloc[0]) if "competitor_success_rate" in comp_row else 0.5
        competitor_success_rate_raw = max(0, min(1, competitor_success_rate_raw))
    else:
        market_competition_raw = 0
        market_competition_log = 0
        competitor_success_rate_raw = 0.5
    
    pop_growth_rate = float(brgy_row["pop_growth"]) if "pop_growth" in brgy_row else 0
    biz_saturation_raw = float(brgy_row["biz_sat"]) if "biz_sat" in brgy_row else 0
    biz_saturation_log = float(brgy_row["biz_sat_log"]) if "biz_sat_log" in brgy_row else 0
    
    # Get business type success rate
    business_type_value = float(business_type_mapping.get(matched_business_type, 0.5))
    business_type_success_rate = round(business_type_value * 100, 1)
    
    spatial_score = float(brgy_row["spatial_score"]) if "spatial_score" in brgy_row else 0.5
    total_biz = int(brgy_row["total_biz"]) if "total_biz" in brgy_row else 0
    population = int(brgy_row["pop_2020"]) if "pop_2020" in brgy_row else 0
    
    # Build feature vector
    features = np.array([[
        foot_traffic_log,
        market_competition_log,
        pop_growth_rate,
        biz_saturation_log,
        business_type_value,
        spatial_score,
        competitor_success_rate_raw
    ]])
    
    # Make prediction
    prob = float(rf_model.predict_proba(features)[0, 1])
    predicted_outcome = "SUCCESS" if prob >= 0.5 else "FAIL"
    confidence = round(abs(prob - 0.5) * 2, 4)
    
    # Generate recommendations
    recommendations = []
    if market_competition_raw > 10:
        recommendations.append(f"High competition ({int(market_competition_raw)} similar businesses)")
    elif market_competition_raw > 5:
        recommendations.append(f"Moderate competition ({int(market_competition_raw)} similar businesses)")
    else:
        recommendations.append(f"Low competition ({int(market_competition_raw)} similar businesses)")
    
    if foot_traffic_raw < 15:
        recommendations.append("Low foot traffic - invest in online marketing")
    elif foot_traffic_raw < 30:
        recommendations.append("Moderate foot traffic - good for business")
    else:
        recommendations.append("High foot traffic - excellent for customer-facing business")
    
    if spatial_score < 0.4:
        recommendations.append("Remote location - consider delivery services")
    elif spatial_score < 0.7:
        recommendations.append("Decent location - good accessibility")
    else:
        recommendations.append("Prime location near town center")
    
    if prob >= 0.65:
        recommendations.append("Strong potential! Proceed with your business plan.")
    elif prob >= 0.40:
        recommendations.append("Moderate risk. Refine your strategy before proceeding.")
    else:
        recommendations.append("High risk. Consider different location or business type.")
    
    return {
        "success": True,
        "barangay": matched_barangay,
        "business_type": matched_business_type,
        "population": population,
        "total_businesses": total_biz,
        "success_probability": round(prob * 100, 1),
        "predicted_outcome": predicted_outcome,
        "confidence": round(confidence * 100, 1),
        "market_competition": int(market_competition_raw),
        "foot_traffic_score": round(foot_traffic_raw, 2),
        "business_saturation": round(biz_saturation_raw, 1),
        "spatial_score": round(spatial_score, 3),
        "population_growth": round(pop_growth_rate, 2),
        "competitor_success_rate": round(competitor_success_rate_raw * 100, 1),
        "business_type_success_rate": business_type_success_rate,
        "recommendations": recommendations
    }

# ============================================
# API ENDPOINTS
# ============================================

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'model': 'Random Forest',
        'barangays': len(brgy_lookup)
    })

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        barangay = data.get('barangay', '')
        business_type = data.get('business_type', '')
        
        if not barangay or not business_type:
            return jsonify({'success': False, 'error': 'Barangay and business_type required'}), 400
        
        result = predict_success(barangay, business_type)
        
        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/barangays', methods=['GET'])
def get_barangays():
    """Return list of all barangays"""
    return jsonify({'barangays': brgy_lookup['barangay'].tolist()})

@app.route('/barangay-data', methods=['GET'])
def get_barangay_data():
    """Return all barangay data for map visualization"""
    barangay_list = []
    
    for _, row in brgy_lookup.iterrows():
        barangay_list.append({
            'barangay': row['barangay'],
            'total_businesses': int(row['total_biz']),
            'population': int(row['pop_2020']),
            'business_saturation': float(row['biz_sat']),
            'foot_traffic': float(row['foot_traffic']),
            'spatial_score': float(row['spatial_score']),
            'pop_growth': float(row['pop_growth'])
        })
    
    return jsonify({'barangays': barangay_list})

@app.route('/business-types', methods=['GET'])
def get_business_types():
    """Return list of all business types"""
    return jsonify({'business_types': list(business_type_mapping.keys())})

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("🚀 FLASK API STARTING...")
    print("=" * 50)
    print(f"📍 API: http://localhost:5000")
    print(f"📊 Health: http://localhost:5000/health")
    print(f"🔮 Predict: POST to http://localhost:5000/predict")
    print(f"🗺️ Barangay Data: http://localhost:5000/barangay-data")
    print("=" * 50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)