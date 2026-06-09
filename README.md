<div align="center">

<img src="https://img.shields.io/badge/AI-Powered-blueviolet?style=for-the-badge&logo=pytorch&logoColor=white" alt="AI Powered"/>
<img src="https://img.shields.io/badge/YOLOv8-Object%20Detection-orange?style=for-the-badge&logo=ultralytics&logoColor=white" alt="YOLOv8"/>
<img src="https://img.shields.io/badge/Flask-Backend-black?style=for-the-badge&logo=flask&logoColor=white" alt="Flask"/>
<img src="https://img.shields.io/badge/TheMealDB-Recipes-green?style=for-the-badge&logo=food&logoColor=white" alt="TheMealDB"/>

<br/><br/>

# VeggieSense AI + Recipe Finder

> **Point. Detect. Cook.**
> Upload a photo of your vegetables and instantly get AI-powered identification with matched recipe suggestions.

<br/>

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](CONTRIBUTING.md)
[![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square)]()

</div>

---

## Table of Contents

- [Overview](#-overview)
- [Tech Stack](#-tech-stack)
- [System Architecture](#-system-architecture)
- [How It Works](#-how-it-works)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [API Reference](#-api-reference)
- [Model Performance](#-model-performance)
- [Configuration](#-configuration)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [Author](#-author)

---

## Overview

**VeggieSense AI** is a full-stack computer vision web application that:

- **Detects vegetables** in uploaded images using a fine-tuned YOLOv8 model
- **Shows confidence scores** with colour-coded probability ratings
- **Suggests recipes** by querying [TheMealDB API](https://www.themealdb.com/) with detected ingredients
- **Ranks recipe matches** by the number of detected ingredients present

Built for home cooks, meal planners, and anyone who ever opened the fridge and thought *"what can I even make with this?"*

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | HTML5, Tailwind CSS, Vanilla JS | Responsive UI, drag-and-drop upload |
| **Backend** | Python 3, Flask, Flask-CORS | REST API server |
| **ML Model** | YOLOv8 (Ultralytics) | Real-time object detection |
| **Image Processing** | OpenCV, Pillow, NumPy | Frame annotation and base64 encoding |
| **Recipe Data** | TheMealDB REST API | Free recipe and ingredient database |
| **Packaging** | pip / requirements.txt | Dependency management |

---

## System Architecture

```mermaid
graph TD
    A[User] -->|Uploads image via browser| B[Frontend index.html]
    B -->|POST /detect| C[Flask Backend app.py]
    C --> D[Load and Decode Image]
    D --> E[YOLOv8 Inference]
    E --> F{Detection Found?}
    F -->|Yes| G[Extract Class Names]
    F -->|No| H[Return Original Image]
    G --> I[Build Unique Ingredient Set]
    I --> J[Query TheMealDB API]
    J --> K[Score and Rank Recipes]
    K --> L[Return Top 2 Matches]
    L -->|JSON Response| B
    H -->|JSON Response| B
    B -->|Render results| A
```

---

## How It Works

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant YOLOModel
    participant MealDBAPI

    User->>Frontend: Upload vegetable image
    Frontend->>Backend: POST /detect with image file
    Backend->>YOLOModel: Run inference with conf threshold 0.1
    YOLOModel-->>Backend: Bounding boxes, labels, confidence scores
    Backend->>Backend: Extract and deduplicate ingredient names
    loop For each detected ingredient
        Backend->>MealDBAPI: GET filter.php?i=ingredient_name
        MealDBAPI-->>Backend: List of matching meal records
    end
    Backend->>Backend: Merge results and calculate overlap score
    Backend->>Backend: Sort by score and select top 2
    Backend-->>Frontend: JSON with detections, annotated image, recipes
    Frontend-->>User: Display detection results and recipe cards
```

---

## Project Structure

```
veggiesense-ai/
│
├── app.py                  # Flask application and detection logic
├── index.html              # Frontend UI served by Flask
├── best_epoch.pt           # Trained YOLOv8 weights (not committed to repo)
├── requirements.txt        # Python dependencies
│
├── static/                 # Optional static assets
│   ├── images/
│   └── icons/
│
├── templates/              # Flask template folder points to root
│
└── README.md
```

> **Note:** `best_epoch.pt` is the custom-trained model file. Due to its file size it is excluded from this repository. See [Getting Started](#-getting-started) for instructions on how to obtain or train it.

---

## Getting Started

### Prerequisites

- Python **3.8+**
- `pip` package manager
- A modern web browser
- *(Optional)* CUDA-enabled GPU for faster inference

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/your-username/veggiesense-ai.git
cd veggiesense-ai
```

**2. Create and activate a virtual environment**

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Add your trained model**

Place your `best_epoch.pt` file in the project root directory.

```bash
cp /path/to/your/best_epoch.pt .
```

**5. Run the server**

```bash
python app.py
```

**6. Open the app**

Navigate to [http://localhost:5000](http://localhost:5000) in your browser.

---

## API Reference

### `GET /health`

Returns the health status of the server and model.

**Response**

```json
{
  "status": "healthy",
  "model_loaded": true,
  "class_count": 30
}
```

---

### `POST /detect`

Runs object detection on the uploaded image and returns detections with recipe suggestions.

**Request**

| Field | Type | Description |
|---|---|---|
| `image` | `file` | Image file in JPG or PNG format via multipart/form-data |

**Success Response**

```json
{
  "count": 3,
  "detections": [
    { "class": "Carrot",   "confidence": 0.9312 },
    { "class": "Broccoli", "confidence": 0.8754 },
    { "class": "Onion",    "confidence": 0.7101 }
  ],
  "annotated_image": "data:image/jpeg;base64,...",
  "search_ingredients": ["carrot", "broccoli", "onion"],
  "recipes": [
    {
      "name": "Carrot Cake",
      "mealId": "52897",
      "match_score": 2,
      "matched_ingredients": ["carrot", "onion"]
    }
  ]
}
```

**Error Response**

```json
{
  "error": "No image provided"
}
```

---

## Model Performance

> Replace the placeholder values below with your actual training results.

### Confidence Threshold Behaviour

| Confidence Range | Indicator | Interpretation |
|---|---|---|
| 80% and above | Green badge | High confidence — reliable detection |
| 50% to 79% | Blue badge | Medium confidence — likely correct |
| 10% to 49% | Yellow badge | Low confidence — use with caution |
| Below 10% | Filtered out | Not shown in results |

### Detection Pipeline

```mermaid
graph LR
    A[Raw Image] --> B[Resize and Normalise]
    B --> C[YOLOv8 Backbone]
    C --> D[Detection Head]
    D --> E{Confidence >= 0.1?}
    E -->|Pass| F[Non-Max Suppression]
    E -->|Fail| G[Discarded]
    F --> H[Annotated Output with Labels]
```

### Recipe Ranking Logic

```mermaid
graph TD
    A[Detected Ingredients] --> B[Query MealDB per Ingredient]
    B --> C[Aggregate into Recipe Dictionary]
    C --> D[Score by Unique Ingredient Overlap]
    D --> E[Sort Descending by Score]
    E --> F[Return Top 2 Recipes]
```

---

## Configuration

Key constants in `app.py`:

| Variable | Default | Description |
|---|---|---|
| `MIN_CONFIDENCE_THRESHOLD` | `0.1` | Minimum YOLO confidence to include a detection |
| `MEALDB_API_BASE` | TheMealDB v1 URL | Base URL for all recipe API calls |
| Top N recipes | `2` | Number of recipe suggestions returned per request |
| `port` | `5000` | Flask development server port |

To apply a stricter detection filter, update the threshold in `app.py`:

```python
# app.py — line 10
MIN_CONFIDENCE_THRESHOLD = 0.5  # Only detections at 50% confidence or higher
```

---

## Roadmap

- [x] YOLOv8 vegetable detection
- [x] TheMealDB recipe integration
- [x] Ranked recipe suggestions by ingredient overlap
- [x] Annotated bounding box image overlay
- [ ] Live webcam feed support
- [ ] Mobile-first PWA version
- [ ] User accounts and saved recipes
- [ ] Nutritional information per detected vegetable
- [ ] Multi-language UI support
- [ ] Docker containerisation

---

## Contributing

Contributions are very welcome. Here is how to get involved:

1. **Fork** the repository
2. **Create** a feature branch — `git checkout -b feature/your-feature-name`
3. **Commit** your changes — `git commit -m 'Add: description of change'`
4. **Push** to your branch — `git push origin feature/your-feature-name`
5. **Open** a Pull Request

Please follow the existing code style and include comments where helpful.

---

## License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for full details.

---

## Author

<div align="center">

Made with love by **Siddhi Virag Lad**

[![Email](https://img.shields.io/badge/Email-siddhi.lad%40vit.edu.in-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:siddhi.lad@vit.edu.in)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://in.linkedin.com/in/lad-siddhi)

*If you found this project useful, consider giving it a star on GitHub!*

</div>

---

<div align="center">
  <sub>Built with YOLOv8 · Flask · Tailwind CSS · TheMealDB</sub>
</div>
