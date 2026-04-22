# HealthChain Backend

## Project Overview
HealthChain is a backend service that provides a robust API for managing health-related data. It is built with a focus on scalability and performance, allowing for efficient data handling and retrieval.

## Installation Instructions
1. Clone the repository:
   ```bash
   git clone https://github.com/sarvadandge/healthchain-backend.git
   cd healthchain-backend
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your environment variables as needed.

## Running the Application
To run the application, use the following command:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

This command will start the server on `http://localhost:8000` and enable auto-reloading for development purposes.