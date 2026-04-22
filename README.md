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
3. Environment Variables

To run this project, you need the following environment variables:

- **ALCHEMY_RPC**: Get your Alchemy RPC URL by signing up at [Alchemy](https://www.alchemy.com/).
- **PRIVATE_KEY**: Generate a private key from your Ethereum wallet (e.g., MetaMask).
- **HEALTHCHAIN_ADDRESS**: This is the contract address for the HealthChain project. Contact your project administrator for this value.
- **PINATA_API_KEY**: Sign up at [Pinata](https://pinata.cloud/) and retrieve your API key from your dashboard.
- **PINATA_SECRET_KEY**: After signing in, go to your API keys section to find your secret key.
- **ENCRYPTION_KEY**: This key should be generated securely for encryption purposes. Consult your developer for specifications.
make sure to create a `.env` file in the root directory of the project and copy the provided variables from `.env.example` to your `.env` file. The `.env.example` file contains a template for setting up your environment variables.

## Running the Application
To run the application, use the following command:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

This command will start the server on `http://localhost:8000` and enable auto-reloading for development purposes.
