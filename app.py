from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from ultralytics import YOLO
import cv2
import numpy as np
import base64
from PIL import Image
import io
import requests

# --- Configuration ---
app = Flask(__name__, template_folder='.') 
CORS(app)
MEALDB_API_BASE = "https://www.themealdb.com/api/json/v1/1/"
# Changed threshold to 0.0 to include ALL detections in the recipe search
MIN_CONFIDENCE_THRESHOLD = 0.1 # Only consider detections with 50% confidence or higher for recipes

# Load your trained model
try:
    model = YOLO('best_epoch.pt')
    MODEL_LOADED = True
    CLASS_NAMES = model.names
except Exception as e:
    print(f"Error loading model: {e}")
    model = None
    MODEL_LOADED = False
    CLASS_NAMES = {}

# --- Utility Functions ---

def fetch_meal_details(meal_id):
    """Fetches details for a specific meal, including its ingredients."""
    url = f"{MEALDB_API_BASE}lookup.php?i={meal_id}"
    try:
        response = requests.get(url)
        if response.status_code == 200 and response.json().get('meals'):
            meal = response.json()['meals'][0]
            ingredients = []
            # MealDB uses 20 separate fields for ingredients (strIngredient1, strIngredient2, etc.)
            for i in range(1, 21):
                ingredient = meal.get(f'strIngredient{i}')
                if ingredient and ingredient.strip():
                    ingredients.append(ingredient.strip().lower())
            return ingredients
    except Exception as e:
        print(f"Error fetching meal details for ID {meal_id}: {e}")
    return []

def get_ranked_recipes(detected_ingredients):
    """
    Searches recipes for each detected ingredient, ranks them by ingredient count match,
    and returns the top 2 best-matched recipes.
    """
    if not detected_ingredients:
        return []

    unique_recipes = {} # Key: mealId, Value: {name, score, missing_ingredients, matched_ingredients_count}
    
    # 1. Fetch recipes for each unique detected ingredient
    for ingredient in detected_ingredients:
        search_url = f"{MEALDB_API_BASE}filter.php?i={ingredient}"
        try:
            response = requests.get(search_url)
            if response.status_code == 200 and response.json().get('meals'):
                # Process the results for this ingredient search
                for meal in response.json()['meals']:
                    meal_id = meal['idMeal']
                    
                    if meal_id not in unique_recipes:
                        # Initialize recipe entry
                        unique_recipes[meal_id] = {
                            'name': meal['strMeal'],
                            'mealId': meal_id,
                            'score': 0,
                            'matched_ingredients': []
                        }

                    # A single match increases the score
                    unique_recipes[meal_id]['matched_ingredients'].append(ingredient)

        except Exception as e:
            print(f"Error searching recipes for {ingredient}: {e}")
            continue

    # 2. Score and Filter (Get final score based on unique matched ingredients)
    # This scoring mechanism prioritizes recipes that use a wider variety of the detected ingredients.
    for meal_id, recipe in unique_recipes.items():
        # Final score is the count of UNIQUE detected ingredients used in this recipe
        recipe['score'] = len(set(recipe['matched_ingredients']))

    # 3. Sort by score (descending) and return top 2 recipes
    ranked_recipes = sorted(unique_recipes.values(), key=lambda x: x['score'], reverse=True)
    
    # Format the top 2 results (changed from 3 to 2)
    final_recipes = []
    for recipe in ranked_recipes[:2]:
        # Optional: You could fetch full details here if needed, but for the list view, we keep it simple.
        final_recipes.append({
            'name': recipe['name'],
            'mealId': recipe['mealId'],
            'match_score': recipe['score'],
            'matched_ingredients': list(set(recipe['matched_ingredients']))
        })
        
    return final_recipes

# --- Flask Routes ---
@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    """Checks server and model health."""
    return jsonify({'status': 'healthy', 'model_loaded': MODEL_LOADED, 'class_count': len(CLASS_NAMES)})

@app.route('/detect', methods=['POST'])
def detect_vegetables():
    """Performs object detection and fetches recipes based on all confident detections."""
    if not MODEL_LOADED:
        return jsonify({'error': 'Model not loaded on server. Check server console for errors.'}), 500

    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        img_bytes = file.read()
        img = Image.open(io.BytesIO(img_bytes))
        img_array = np.array(img)
        
        # Run inference with a confidence threshold
        results = model(img_array, conf=MIN_CONFIDENCE_THRESHOLD, verbose=False)
        
        detections = []
        detected_ingredients = set()
        
        if results and len(results) > 0:
            r = results[0]
            boxes = r.boxes
            
            # 1. Process detections and collect unique ingredient names
            for box in boxes:
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                class_name = CLASS_NAMES.get(cls, f"Unknown Class {cls}").lower()
                
                # The filtering logic is now handled by the MIN_CONFIDENCE_THRESHOLD = 0.0
                if conf >= MIN_CONFIDENCE_THRESHOLD:
                    detections.append({
                        'class': class_name.capitalize(),
                        'confidence': round(conf, 4)
                    })
                    # Use a simpler name for the API search (e.g., 'carrot' instead of 'red carrot')
                    simple_name = class_name.split()[-1]
                    detected_ingredients.add(simple_name)

            # 2. Draw boxes on image
            annotated_img = r.plot()
            annotated_img_rgb = cv2.cvtColor(annotated_img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(annotated_img_rgb)
            
            # Convert to base64
            buffered = io.BytesIO()
            pil_img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            annotated_image_data = f'data:image/jpeg;base64,{img_str}'
        else:
            # No detections found, use original image as annotated
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            annotated_image_data = f'data:image/jpeg;base64,{img_str}'
            
        # 3. Fetch and rank recipes based on all detected ingredients
        recipes = get_ranked_recipes(list(detected_ingredients))

        # Sort detections list by confidence for display
        detections.sort(key=lambda x: x['confidence'], reverse=True)
        
        return jsonify({
            'detections': detections,
            'annotated_image': annotated_image_data,
            'count': len(detections),
            # Return the list of unique ingredients used for the search
            'search_ingredients': list(detected_ingredients),
            'recipes': recipes
        })
    
    except Exception as e:
        print(f"An error occurred during detection: {e}")
        return jsonify({'error': 'Internal server error during detection: ' + str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)