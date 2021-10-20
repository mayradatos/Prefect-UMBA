import prefect
from prefect import task
from prefect.tasks.aws.s3 import S3Upload, S3Download

from io import BytesIO, StringIO

import pandas as pd
import numpy as np


@task(log_stdout=True)
def DataLoad():
    """
    #### Load Node
    A simple task which downloads relevant data from S3 and makes it available on the common `include` folder.
    """
    botoArgs = dict(
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
        endpoint_url="http://minio:9000",
    )
    print("Downloading Data from CSV")
    downloadContents = S3Download(bucket="airflow-port", boto_kwargs=botoArgs).run(
        "data/german_credit_data.csv"
    )
    df_credit = pd.read_csv(StringIO(downloadContents), index_col=0)

    interval = (18, 25, 35, 60, 120)
    cats = ["Student", "Young", "Adult", "Senior"]
    df_credit["Age_cat"] = pd.cut(df_credit.Age, interval, labels=cats)
    uploadContents = bytes(
        df_credit.to_csv(line_terminator="\r\n", index=False), encoding="utf-8"
    )
    # Upload to S3
    uploadKey = (
        prefect.context.scheduled_start_time.strftime("%Y-%m-%d-%H-%M-%S")
        + "/german_credit_data_LDA.csv"
    )
    print("Uploading Data")
    uploadKey = S3Upload(bucket="airflow-port", boto_kwargs=botoArgs).run(
        uploadContents, key=uploadKey
    )
    return uploadKey


@task()
def PrepareData(dataPath):
    """
    #### Prepare Data
    A task which prepares the data for all ML models.
    """
    from sklearn.model_selection import train_test_split

    # s3 = S3Hook(aws_conn_id="custom_s3")
    botoArgs = dict(
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
        endpoint_url="http://minio:9000",
    )
    # ds = kwargs["execution_date"].strftime("%Y-%m-%d-%H-%M-%S")
    ds = prefect.context.scheduled_start_time.strftime("%Y-%m-%d-%H-%M-%S")
    # downloadPath = s3.download_file(
    #     key=ds + "/german_credit_data_LDA.csv",
    #     bucket_name="dag-umba",
    # )
    downloadContents = S3Download(bucket="airflow-port", boto_kwargs=botoArgs).run(
        dataPath
    )
    df_credit = pd.read_csv(StringIO(downloadContents), index_col=0)
    df_credit["Saving accounts"] = df_credit["Saving accounts"].fillna("no_inf")
    df_credit["Checking account"] = df_credit["Checking account"].fillna("no_inf")

    df_credit = df_credit.merge(
        pd.get_dummies(
            df_credit[
                [
                    "Purpose",
                    "Sex",
                    "Housing",
                    "Risk",
                    "Checking account",
                    "Saving accounts",
                    "Age_cat",
                ]
            ],
            prefix=["Purpose", "Sex", "Housing", "Risk", "Check", "Savings", "Age_cat"],
            drop_first=False,
        ),
        left_index=True,
        right_index=True,
    )

    del df_credit["Saving accounts"]
    del df_credit["Checking account"]
    del df_credit["Purpose"]
    del df_credit["Sex"]
    del df_credit["Housing"]
    del df_credit["Age_cat"]
    del df_credit["Risk"]
    del df_credit["Risk_good"]
    # del df_credit["Purpose_business"]
    # del df_credit["Sex_female"]
    # del df_credit["Housing_free"]
    # del df_credit["Check_little"]
    # del df_credit["Savings_little"]
    # del df_credit["Age_cat_Student"]

    uploadContents = bytes(
        df_credit.to_csv(line_terminator="\r\n", index=False), encoding="utf-8"
    )
    # Upload to S3
    uploadKey = ds + "/german_credit_data_PD.csv"
    # s3.load_file(
    #     bucket_name="dag-umba",
    #     key=uploadKey,
    #     filename="german_credit_data_PD.csv",
    #     replace=True,
    # )
    uploadKey = S3Upload(bucket="airflow-port", boto_kwargs=botoArgs).run(
        uploadContents, key=uploadKey
    )

    # Creating the X and y variables
    df_credit["Credit amount"] = np.log(df_credit["Credit amount"])
    X = df_credit.drop("Risk_bad", 1).values
    y = df_credit["Risk_bad"].values

    # Spliting X and y into train and test version
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42
    )

    # ## Upload training splits to S3
    # X_train_key = ds + "/trainingData/X_train.npy"
    # y_train_key = ds + "/trainingData/y_train.npy"
    # X_test_key = ds + "/trainingData/X_test.npy"
    # y_test_key = ds + "/trainingData/y_test.npy"

    # # uploadContents = bytes(file.getvalue(), encoding="utf-8")
    # X_train_file = BytesIO()
    # np.save(X_train_file, X_train)
    # X_train_key = S3Upload(bucket="airflow-port", boto_kwargs=botoArgs).run(
    #     X_train_file.getbuffer(), key=X_train_key
    # )

    # y_train_file = BytesIO()
    # np.save(y_train_file, y_train)
    # y_train_key = S3Upload(bucket="airflow-port", boto_kwargs=botoArgs).run(
    #     y_train_file.getbuffer(), key=y_train_key
    # )

    # X_test_file = BytesIO()
    # np.save(X_test_file, X_test)
    # X_test_key = S3Upload(bucket="airflow-port", boto_kwargs=botoArgs).run(
    #     X_test_file.getbuffer(), key=X_test_key
    # )

    # y_test_file = BytesIO()
    # np.save(y_test_file, y_test)
    # y_test_key = S3Upload(bucket="airflow-port", boto_kwargs=botoArgs).run(
    #     y_test_file.getbuffer(), key=y_test_key
    # )

    # # np.save("X_train.npy", X_train)
    # # with open("X_train.npy", "rb") as f:
    # X_train_key = S3Upload(bucket="airflow-port", boto_kwargs=botoArgs).run(
    #     X_train.tobytes(), key=X_train_key
    # )

    # # s3.load_file(
    # #     bucket_name="dag-umba",
    # #     key=X_train_key,
    # #     filename="X_train.npy",
    # #     replace=True,
    # # )
    #
    # # np.save("Y_train.npy", y_train)
    # # with open("Y_train.npy", "rb") as f:
    # y_train_key = S3Upload(bucket="airflow-port", boto_kwargs=botoArgs).run(
    #     y_train.tobytes(), key=y_train_key
    # )
    # # s3.load_file(
    # #     bucket_name="dag-umba",
    # #     key=y_train_key,
    # #     filename="Y_train.npy",
    # #     replace=True,
    # # )
    #
    # X_test_key = S3Upload(bucket="airflow-port", boto_kwargs=botoArgs).run(
    #     X_test.tobytes(), key=X_test_key
    # )
    # # s3.load_file(
    # #     bucket_name="dag-umba",
    # #     key=X_test_key,
    # #     filename="X_test.npy",
    # #     replace=True,
    # # )
    #
    # # np.save("Y_test.npy", y_test)
    # # with open("Y_test.npy", "rb") as f:
    # # new buffer named buf

    # y_test_key = S3Upload(bucket="airflow-port", boto_kwargs=botoArgs).run(
    #     y_test.tobytes(), key=y_test_key
    # )

    return {
        "dataKey": uploadKey,
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
    }
