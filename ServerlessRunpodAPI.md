# Creating a Serverless API on RunPod: A Detailed Guide

This guide breaks down the concepts and steps shown in the video for deploying and using serverless APIs on RunPod. We will cover the fundamental concepts, how to deploy an endpoint, and most importantly, how to interact with it using Python.

## Part 1: Understanding Serverless Concepts

Before deploying, it's essential to understand the core terminology.

### What is Serverless?

Serverless computing doesn't mean there are no servers. It means you, as the developer, don't have to manage the underlying infrastructure (like provisioning servers, handling OS updates, or scaling). You provide your code, and the platform (RunPod) handles the rest.

*   **You focus on:** Your application code (e.g., a Python script for image generation).
*   **The platform handles:** Allocating resources (CPU, GPU, RAM), scaling instances up or down based on demand, and managing the servers.

### Workers and Cold Starts

*   **Worker:** A worker is a single, running instance of your application environment (your Docker container). When you send an API request, it's routed to a worker to be processed. You can have multiple workers to handle concurrent requests.
*   **Cold Start:** Serverless platforms are cost-effective because they scale workers down to zero when there are no requests. A "cold start" is the initial delay experienced when the *very first* request comes in after a period of inactivity. The platform needs to:
    1.  Provision a new instance.
    2.  Download your Docker container.
    3.  Start the container and initialize your application (e.g., load a machine learning model into GPU memory).

This initialization takes time. Subsequent requests are fast because they hit an already "warm" or "active" worker.

*   **Active Workers:** To minimize cold starts for applications that need low latency, RunPod allows you to configure a minimum number of "Active Workers." These workers are kept running 24/7 (at a discounted rate) so they are always ready to process requests instantly.

## Part 2: Deploying a Serverless Endpoint on RunPod

You have two primary methods for deploying your code as a serverless endpoint.

### Method 1: Using a Pre-built Docker Image (Recommended for Beginners)

This is the simplest way to get started. Many common models and applications are already packaged into Docker images and hosted on registries like Docker Hub.

1.  **Navigate to Serverless:** In your RunPod dashboard, go to `Manage -> Serverless`.
2.  **Create Endpoint:** Click the `+ New Endpoint` button.
3.  **Select Custom Source:** Choose the **Docker Image** option.
4.  **Enter Container Image:** Provide the name of the image. For example, to deploy Stable Diffusion XL, you might use an image like `runpod/ai-api-sdxl:2.1.0`.
5.  **Configure Endpoint:**
    *   **Endpoint Name:** Give your endpoint a memorable name.
    *   **Worker Configuration:** Select the GPU type and size required for your model.
    *   **Workers:**
        *   **Max Workers:** The maximum number of concurrent workers that can be spun up.
        *   **Active Workers:** The number of workers to keep running 24/7 to avoid cold starts (set to 0 if you only want to pay for active processing time).
        *   **Idle Timeout:** The number of seconds a worker will stay warm after processing a request before shutting down.
6.  **Deploy:** Click `Create Endpoint` and wait for the build to complete.

### Method 2: Using a Dockerfile from a GitHub Repo (for Customization)

If you need a custom environment, you can point RunPod to a GitHub repository containing a `Dockerfile`. RunPod will automatically build the image for you and deploy it. The process is similar to the above, but you select **GitHub Repo** instead of Docker Image and provide the repository URL.

## Part 3: The Anatomy of a Custom Worker

When you build a custom worker, two files are essential in your repository:

### 1. The `Dockerfile`

This is a text file with instructions on how to build your environment. It defines everything from the base operating system to the Python dependencies.

**Example `Dockerfile` from the `worker-template`:**
```dockerfile
# Start from a base RunPod image with CUDA pre-installed
FROM runpod/base:0.6.3-cuda11.8.0

# Set the working directory inside the container
WORKDIR /

# Set Python 3.11 as the default
RUN ln -sf $(which python3.11) /usr/local/bin/python && \
    ln -sf $(which python3.11) /usr/local/bin/python3

# Copy your Python requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --upgrade -r requirements.txt --no-cache-dir --system

# Copy your handler file and any other necessary files
COPY handler.py .

# Define the command to run when the container starts
# This starts the RunPod serverless handler
CMD python -u /handler.py
```

### 2. The `handler.py`

This Python script is the core of your worker. It contains the logic for processing incoming API requests.

*   It must define a `handler(job)` function that takes a job payload as input.
*   The job payload contains the `input` sent in your API request body.
*   The script uses `runpod.serverless.start({"handler": handler})` to start a server that listens for jobs and passes them to your handler function.

**Example `handler.py` from the `worker-template`:**
```python
import runpod

def handler(job):
    """
    The handler function that processes jobs.
    'job' is a dictionary containing the job payload.
    """
    # Get the input from the job payload
    job_input = job['input']
    name = job_input.get('name', 'World')

    # Your processing logic goes here
    # For example, loading a model and running inference
    output = f"Hello, {name}!"

    # Return the output
    return output

# Start the serverless handler
runpod.serverless.start({"handler": handler})
```

## Part 4: Interacting with Your Serverless API (Python Examples)

Once your endpoint is deployed and `Ready`, you can start sending requests.

### Step 1: Get Your API Key and Endpoint URL

1.  **Endpoint URL:** Find this in the `Requests` tab of your endpoint's dashboard. It will look like `https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run`.
2.  **API Key:** Go to `Account -> Settings -> API Keys`. Create a new key if you don't have one. **Treat this key like a password.**

### Step 2: Understanding the API Request Body (Schema)

The JSON body you send must match what the `handler.py` of the worker expects. For the `runpod/ai-api-sdxl` worker, the schema requires an `input` object with various parameters.

**Example JSON Body for SDXL:**
```json
{
  "input": {
    "prompt": "A futuristic cityscape at night",
    "negative_prompt": "blurry, distorted, ugly",
    "height": 1024,
    "width": 1024,
    "num_inference_steps": 30,
    "guidance_scale": 7.5,
    "seed": null
  }
}
```

### Step 3: Making API Calls with Python

Here are pure Python examples using the popular `requests` library to replace the `n8n` workflows.

#### Asynchronous Request (`/run`)

This is a two-step process, ideal for long-running jobs (e.g., generating a video). You first submit the job, then you check its status later.

```python
import requests
import time
import os

# --- Configuration ---
RUNPOD_API_KEY = "YOUR_RUNPOD_API_KEY"
ENDPOINT_ID = "YOUR_ENDPOINT_ID"
API_URL_BASE = f"https://api.runpod.ai/v2/{ENDPOINT_ID}"

headers = {
    "Authorization": f"Bearer {RUNPOD_API_KEY}"
}

payload = {
    "input": {
        "prompt": "A robotic lion on a hill, cinematic lighting",
        "negative_prompt": "low quality, blurry",
        "num_inference_steps": 25
    }
}

# --- 1. Submit the Job ---
print("Submitting job...")
response = requests.post(f"{API_URL_BASE}/run", json=payload, headers=headers)

if response.status_code != 200:
    print(f"Error submitting job: {response.text}")
    exit()
    
job_data = response.json()
job_id = job_data['id']
print(f"Job submitted successfully with ID: {job_id}")

# --- 2. Poll for the Result ---
print("Polling for job completion...")
while True:
    status_response = requests.get(f"{API_URL_BASE}/status/{job_id}", headers=headers)
    
    if status_response.status_code != 200:
        print(f"Error checking status: {status_response.text}")
        break

    status_data = status_response.json()
    status = status_data['status']
    
    print(f"Current job status: {status}")

    if status == "COMPLETED":
        print("\nJob completed!")
        print("Output:", status_data['output'])
        # Handle the output (e.g., save the image) in Part 4
        break
    elif status == "FAILED":
        print("\nJob failed!")
        print("Error details:", status_data.get('error', 'No error details provided.'))
        break
    
    # Wait for 5 seconds before checking again
    time.sleep(5)
```

#### Synchronous Request (`/runsync`)

This is simpler and best for tasks that complete quickly (under a few minutes). The request will hang and wait until the job is done, then return the full result in one go.

```python
import requests
import base64

# --- Configuration ---
RUNPOD_API_KEY = "YOUR_RUNPOD_API_KEY"
ENDPOINT_ID = "YOUR_ENDPOINT_ID"
API_URL_BASE = f"https://api.runpod.ai/v2/{ENDPOINT_ID}"

headers = {
    "Authorization": f"Bearer {RUNPOD_API_KEY}"
}

payload = {
    "input": {
        "prompt": "A futuristic cityscape at night",
        "negative_prompt": "blurry, distorted, ugly",
        "num_inference_steps": 30
    }
}

# --- Submit the Job and Wait for the Result ---
print("Submitting synchronous job... (this may take a moment)")
response = requests.post(f"{API_URL_BASE}/runsync", json=payload, headers=headers)

if response.status_code != 200:
    print(f"Error: {response.text}")
    exit()

result = response.json()

if result['status'] == "COMPLETED":
    print("Job completed successfully!")
    # The output is directly available in the response
    image_url = result['output']['image_url']
    print(f"Image is ready: {image_url}")

    # --- Step 4: Handling the Image Data ---
    # The image_url contains Base64 encoded data
    # Format: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg..."

    try:
        # 1. Remove the prefix to get just the Base64 string
        base64_data = image_url.split(',')[1]

        # 2. Decode the Base64 string into bytes
        image_bytes = base64.b64decode(base64_data)

        # 3. Save the bytes to a file
        with open("output_image.png", "wb") as f:
            f.write(image_bytes)
        print("Image saved to output_image.png")

    except Exception as e:
        print(f"Failed to decode and save image: {e}")
else:
    print(f"Job failed with status: {result['status']}")
    print("Error details:", result.get('error', 'No error details provided.'))
```