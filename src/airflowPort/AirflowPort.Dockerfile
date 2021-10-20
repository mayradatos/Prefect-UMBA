FROM prefecthq/prefect:latest-python3.6

RUN pip install pip --upgrade && pip install numpy pandas seaborn plotly scikit-learn scipy xgboost wheel boto3 matplotlib
COPY Tasks Tasks
## Prefect will inject additional code into the Dockerfile
