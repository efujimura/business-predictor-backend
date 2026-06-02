# ============================================================================
# GENERATE 20 SAMPLE PREDICTIONS USING YOUR EXISTING API
# ============================================================================

import requests
import random
import pandas as pd
import time

# ============================================================================
# CONFIGURATION
# ============================================================================

API_URL = "http://localhost:5000/predict"  # Your Flask API endpoint

# List of all barangays (from your app)
BARANGAYS = [
    "Alcala", "Alobo", "Anislag", "Bagumbayan", "Balinad", "Bañadero", "Bañag",
    "Bascaran", "Bigao", "Binitayan", "Bongalon", "Budiao", "Burgos", "Busay",
    "Canarom", "Cullat", "Dela Paz", "Dinorawan", "Gabawan", "Gapo", "Ibaugan",
    "Ilawod", "Inarado", "Kidaco", "Kilicao", "Kimantong", "Kinawitan", "Kiwalo",
    "Lacag", "Mabini", "Malabog", "Malobago", "Maopi", "Market Site", "Maroroy",
    "Matnog", "Mayon", "Mi-isi", "Nabasan", "Namantao", "Pandan", "Peñafrancia",
    "Sagpon", "Salvacion", "San Rafael", "San Ramon", "San Roque",
    "San Vicente Grande", "San Vicente Pequeño", "Sipi", "Tabon-tabon",
    "Tagas", "Talahib", "Villahermosa"
]

# List of common business types (from your app)
BUSINESS_TYPES = [
    "RESTAURANT", "EATERY", "BAKERY", "CAFE", "FAST FOOD", 
    "GROCERY", "SARI-SARI STORE", "HARDWARE", "PHARMACY", 
    "SALON", "LAUNDRY SERVICE", "PRINTING SERVICE", "FURNITURE",
    "HOTEL", "INN", "FUNCTION HALL", "MEDICAL CLINIC",
    "RICE MILL", "POULTRY FARM", "CONSTRUCTION SUPPLY",
    "FOOD CART", "CATERING", "BAR", "CLOTHING STORE",
    "ELECTRONICS", "BOOKSTORE", "TUTORIAL CENTER",
    "TRUCKING", "COURIER", "REAL ESTATE", "PAWNSHOP"
]

# ============================================================================
# GENERATE RANDOM PREDICTIONS
# ============================================================================

def get_random_prediction():
    """Call the API with random barangay and business type"""
    
    barangay = random.choice(BARANGAYS)
    business_type = random.choice(BUSINESS_TYPES)
    
    try:
        response = requests.post(
            API_URL,
            json={"barangay": barangay, "business_type": business_type},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "barangay": barangay,
                "business_type": business_type,
                "success_probability": data.get("success_probability", 0),
                "predicted_outcome": data.get("predicted_outcome", "N/A"),
                "confidence": data.get("confidence", 0),
                "market_competition": data.get("market_competition", 0),
                "foot_traffic_score": data.get("foot_traffic_score", 0),
                "competitor_success_rate": data.get("competitor_success_rate", 0),
                "business_type_success_rate": data.get("business_type_success_rate", 0),
                "spatial_score": data.get("spatial_score", 0),
                "population": data.get("population", 0)
            }
        else:
            print(f"Error: {response.status_code} for {barangay} - {business_type}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None

# ============================================================================
# GENERATE 20 SAMPLES
# ============================================================================

print("=" * 80)
print("GENERATING 20 SAMPLE PREDICTIONS FROM YOUR API")
print("=" * 80)
print(f"API URL: {API_URL}")
print("=" * 80)

predictions = []
failed = 0

for i in range(20):
    print(f"Generating prediction {i+1}/20...", end=" ")
    result = get_random_prediction()
    
    if result:
        predictions.append(result)
        print(f"✅ {result['barangay']} - {result['business_type']}: {result['success_probability']}%")
    else:
        failed += 1
        print(f"❌ Failed")
    
    time.sleep(0.5)  # Small delay to avoid overwhelming the API

print("\n" + "=" * 80)
print(f"✅ Successfully generated {len(predictions)} predictions")
print(f"❌ Failed: {failed}")
print("=" * 80)

# ============================================================================
# DISPLAY RESULTS TABLE
# ============================================================================

print("\n" + "=" * 100)
print("20 SAMPLE PREDICTIONS")
print("=" * 100)
print(f"{'#':<3} {'Barangay':<22} {'Business Type':<22} {'Prob':>6} {'Outcome':<8} {'Conf':>6} {'Comp':>6} {'Foot':>8}")
print("-" * 100)

for i, pred in enumerate(predictions, 1):
    # Determine risk level
    if pred['success_probability'] >= 65:
        risk = "Low"
    elif pred['success_probability'] >= 40:
        risk = "Mod"
    else:
        risk = "High"
    
    print(f"{i:<3} {pred['barangay']:<22} {pred['business_type']:<22} {pred['success_probability']:>5.1f}%   {pred['predicted_outcome']:<8} {pred['confidence']:>5.1f}%   {pred['market_competition']:>5.0f}   {pred['foot_traffic_score']:>7.1f}")

print("=" * 100)

# ============================================================================
# STATISTICAL SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("STATISTICAL SUMMARY")
print("=" * 80)

probs = [p['success_probability'] for p in predictions]

print(f"Total Predictions: {len(predictions)}")
print(f"Average Success Probability: {sum(probs)/len(probs):.1f}%")
print(f"Min Success Probability: {min(probs):.1f}%")
print(f"Max Success Probability: {max(probs):.1f}%")

# Count by risk level
high = sum(1 for p in probs if p < 40)
moderate = sum(1 for p in probs if 40 <= p < 65)
low = sum(1 for p in probs if p >= 65)

print(f"\nRisk Level Distribution:")
print(f"   High Risk (<40%):     {high} ({high/20*100:.0f}%)")
print(f"   Moderate Risk (40-64%): {moderate} ({moderate/20*100:.0f}%)")
print(f"   Low Risk (≥65%):     {low} ({low/20*100:.0f}%)")

# ============================================================================
# EXPORT TO CSV
# ============================================================================

df = pd.DataFrame(predictions)
df.to_csv("sample_20_predictions.csv", index=False)
print(f"\n✅ Saved to sample_20_predictions.csv")

# Display the CSV content preview
print("\n" + "=" * 80)
print("CSV FILE PREVIEW")
print("=" * 80)
print(df.head(10).to_string(index=False))

print("\n" + "=" * 80)
print("✅ 20 SAMPLE PREDICTIONS COMPLETE!")
print("=" * 80)