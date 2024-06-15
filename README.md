# Content Recommendation Prototype

This repository contains a prototype for a content recommendation model designed for an online news platform. The model provides personalized article recommendations to users based on their interaction history and article metadata.

## Table of Contents
- [Content Recommendation Prototype](#content-recommendation-prototype)
  - [Table of Contents](#table-of-contents)
  - [Project Structure](#project-structure)
  - [Setup Instructions](#setup-instructions)
  - [Usage](#usage)
  - [Model Overview](#model-overview)
  - [Deployment Strategy](#deployment-strategy)
  - [Contact](#contact)

## Project Structure
- `src/data_loader.py`: Contains functions to load article metadata, embeddings, and user click data.
- `src/recommender.py`: Implements the recommendation model using matrix factorization and content-based filtering.
- `src/main.py`: Main script to run the recommendation system and interact with the user.
- `setup/setup.sh`: Bash script to set up the development environment using conda.
- `setup/requirements.yaml`: Conda environment configuration file.
- `deployment.md`: Documentation outlining the strategy for deploying the recommendation model in a production cloud environment.

## Setup Instructions
To set up the development environment, follow these steps:

1. **Install Conda**: Ensure that Conda is installed on your system. If not, download and install it from [Conda's official website](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html).

2. **Run the setup script**:
    ```bash
    source setup/setup.sh
    ```
    This script will:
    - Check if Conda and curl are installed.
    - Remove any existing Conda environment named `content-recommendation-prototype`.
    - Create a new Conda environment using the configuration in `setup/requirements.yaml`.
    - Activate the new environment.

## Usage
To run the recommendation system and get article recommendations for a specific user, follow these steps:

1. **Activate the Conda environment**:
    ```bash
    conda activate content-recommendation-prototype
    ```

2. **Run the main script**:
    ```bash
    cd src
    python main.py
    ```
3. **Interact with the system**:
    - Enter a user ID when prompted to get recommendations.
    - Enter 'q' to quit the program.

## Model Overview
The recommendation model integrates collaborative filtering and content-based filtering techniques. Key components include:

- **Data Loading**:
    - `load_data()`: Loads article metadata, embeddings, and user clicks data. Merges user click data with article metadata.
  
- **Matrix Factorization**:
    - Utilizes Truncated SVD to perform matrix factorization on the user-item interaction matrix.
    - Precomputes user and item factors for efficient recommendation computation.

- **Content-Based Filtering**:
    - Uses article embeddings to compute content similarity.
    - Implements an embedding-based index using FAISS for fast nearest neighbor search.

- **Recommendation Generation**:
    - Combines collaborative filtering scores with content-based scores.
    - Boosts scores based on user preferences for publishers and categories, word count similarity, and article recency.

## Deployment Strategy
For details on deploying this recommendation model in a production cloud environment, refer to the [deployment.md](deployment.md) document. It covers:

- **Cloud Services and Resources**: Outlines the necessary cloud services for deployment, including AWS EC2, Lambda, S3, RDS, DynamoDB, VPC, ELB, and SageMaker.
- **Monitoring and Performance Metrics**: Discusses the tools and metrics for monitoring model performance in production.
- **CI/CD Pipeline**: Proposes a continuous integration and continuous deployment pipeline using CodeCommit/GitHub, CodePipeline, CodeBuild, and CodeDeploy.
- **Security Considerations**: Addresses potential security issues and compliance with data protection regulations.

## Contact
For any questions or support, please reach out to [me](mailto:spkgyk@outlook.com)!

