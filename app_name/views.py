import os
import tensorflow as tf
from keras.applications.resnet import ResNet50, preprocess_input
from keras.layers import GlobalMaxPooling2D
import cv2
import numpy as np
from numpy.linalg import norm
import pickle
from sklearn.neighbors import NearestNeighbors
import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Get the absolute path of the project's root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load the feature list and filenames
feature_list = np.array(pickle.load(open(os.path.join(BASE_DIR, "data/featurevector.pkl"), "rb")))
filenames = pickle.load(open(os.path.join(BASE_DIR, "data/filenames.pkl"), "rb"))

# Load the ResNet50 model
model = ResNet50(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
model.trainable = False

# Create the model architecture
model = tf.keras.Sequential([
    model,
    GlobalMaxPooling2D()
])
model.summary()

# Load the fashion data
fashion_data = pd.read_csv(os.path.join(BASE_DIR, "data/fashion.csv"))

@csrf_exempt
def similar_images(request):
    if request.method == "POST":
        # Get the image file from the request
        image_file = request.FILES.get('image')
        if not image_file:
            return JsonResponse({"error": "No image file found."}, status=400)

        img = cv2.imdecode(np.fromstring(image_file.read(), np.uint8), cv2.IMREAD_UNCHANGED)
        img = cv2.resize(img, (224, 224))
        img = np.array(img)
        expand_img = np.expand_dims(img, axis=0)
        pre_img = preprocess_input(expand_img)
        result = model.predict(pre_img).flatten()
        normalized = result / norm(result)

        # Perform similarity search
        neighbors = NearestNeighbors(n_neighbors=10, algorithm="brute", metric="euclidean")
        neighbors.fit(feature_list)
        distance, indices = neighbors.kneighbors([normalized])

        # Get the filenames of similar images
        similar_images_filenames = [filenames[file] for file in indices[0]]

        # Get the product IDs from the filenames
        product_ids = [int(file.split("\\")[-1].split(".")[0]) for file in similar_images_filenames]

        # Retrieve information from fashion data based on product IDs
        fashion_info = fashion_data[fashion_data["ProductId"].isin(product_ids)].to_dict(orient="records")

        # Serialize the response as JSON
        response_data = {"similar_images": fashion_info}
        return JsonResponse(response_data)
    else:
        # Handle GET requests
        return JsonResponse({"message": "Send a POST request with an image file to get similar images."})
