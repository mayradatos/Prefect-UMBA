import prefect
from prefect import task
from prefect.tasks.aws.s3 import S3Upload, S3Download

from sklearn.metrics import roc_curve
import numpy as np
import matplotlib.pyplot as plt


@task
def Model_NB(cleanData):
    from sklearn.naive_bayes import GaussianNB

    # ti = kwargs["ti"]
    # # Get key from the PrepareData task
    # X_train_key = ti.xcom_pull(task_ids="PrepareData", key="X_train")
    # Y_train_key = ti.xcom_pull(task_ids="PrepareData", key="y_train")
    # X_test_key = ti.xcom_pull(task_ids="PrepareData", key="X_test")
    # Y_test_key = ti.xcom_pull(task_ids="PrepareData", key="y_test")

    # # Download from S3
    # s3 = S3Hook(aws_conn_id="custom_s3")
    # X_train_path = s3.download_file(key=X_train_key, bucket_name="dag-umba")
    # Y_train_path = s3.download_file(key=Y_train_key, bucket_name="dag-umba")
    # X_test_path = s3.download_file(key=X_test_key, bucket_name="dag-umba")
    # Y_test_path = s3.download_file(key=Y_test_key, bucket_name="dag-umba")
    # extract clean data from kwargs
    # cleanData = kwargs["cleanData"]
    # Load Numpy arrays
    X_train = cleanData["X_train"]
    y_train = cleanData["y_train"]
    X_test = cleanData["X_test"]
    y_test = cleanData["y_test"]

    # Criando o classificador logreg
    GNB = GaussianNB()

    # Fitting with train data
    model = GNB.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    # Roc Curve it could be a new module
    y_pred_prob = model.predict_proba(X_test)[:, 1]
    # Generate ROC curve values: fpr, tpr, thresholds
    fpr, tpr, thresholds = roc_curve(y_test, y_pred_prob)

    # Plot ROC curve
    plt.plot([0, 1], [0, 1], "k--")
    plt.plot(fpr, tpr)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve")
    plt.savefig("roc_curve.png")
    plt.close()

    # Upload ROC curve to S3
    # ds = kwargs["execution_date"].strftime("%Y-%m-%d-%H-%M-%S")
    ds = prefect.context.scheduled_start_time.strftime("%Y-%m-%d-%H-%M-%S")
    curveKey = ds + "/roc_curve_model_nb.png"
    botoArgs = dict(
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
        endpoint_url="http://minio:9000",
    )
    with open("roc_curve.png", "rb") as f:
        curveKey = S3Upload(bucket="airflow-port", boto_kwargs=botoArgs).run(
            f.read(), key=curveKey
        )
    # s3.load_file(
    #     filename="roc_curve.png",
    #     key=curveKey,
    #     bucket_name="dag-umba",
    #     replace=True,
    # )

    # Upload y_pred to S3
    # y_pred_key = ds + "/trainingData/y_pred_model_nb.npy"
    # np.save("y_pred_model_nb.npy", y_pred)

    # s3.load_file(
    #     filename="y_pred_model_nb.npy",
    #     key=y_pred_key,
    #     bucket_name="dag-umba",
    #     replace=True,
    # )

    return {
        "y_pred": y_pred,
        "roc_curve": curveKey,
        "details": "Model Score: {}".format(model.score(X_train, y_train)),
    }


@task
def Model_RF(cleanData):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import GridSearchCV

    # ti = kwargs["ti"]
    # # Get key from the PrepareData task
    # X_train_key = ti.xcom_pull(task_ids="PrepareData", key="X_train")
    # Y_train_key = ti.xcom_pull(task_ids="PrepareData", key="y_train")
    # X_test_key = ti.xcom_pull(task_ids="PrepareData", key="X_test")
    # Y_test_key = ti.xcom_pull(task_ids="PrepareData", key="y_test")

    # # Download from S3
    # s3 = S3Hook(aws_conn_id="custom_s3")
    # X_train_path = s3.download_file(key=X_train_key, bucket_name="dag-umba")
    # Y_train_path = s3.download_file(key=Y_train_key, bucket_name="dag-umba")
    # X_test_path = s3.download_file(key=X_test_key, bucket_name="dag-umba")
    # Y_test_path = s3.download_file(key=Y_test_key, bucket_name="dag-umba")

    # Load Numpy arrays
    X_train = cleanData["X_train"]
    y_train = cleanData["y_train"]
    X_test = cleanData["X_test"]
    y_test = cleanData["y_test"]

    # Seting the Hyper Parameters
    param_grid = {
        "max_depth": [3, 5, 7, 10, None],
        "n_estimators": [3, 5, 10, 25, 50, 150],
        "max_features": [4, 7, 15, 20],
    }

    # Creating the classifier
    model = RandomForestClassifier(random_state=2)

    grid_search = GridSearchCV(
        model, param_grid=param_grid, cv=5, scoring="recall", verbose=4
    )
    grid_search.fit(X_train, y_train)

    rf = RandomForestClassifier(
        max_depth=grid_search.best_params_["max_depth"],
        max_features=grid_search.best_params_["max_features"],
        n_estimators=grid_search.best_params_["n_estimators"],
        random_state=2,
    )
    # trainning with the best params
    rf.fit(X_train, y_train)

    # Testing the model
    # Predicting using our  model
    y_pred = rf.predict(X_test)
    # Roc Curve it could be a new module
    y_pred_prob = rf.predict_proba(X_test)[:, 1]
    # Generate ROC curve values: fpr, tpr, thresholds
    fpr, tpr, thresholds = roc_curve(y_test, y_pred_prob)

    # Plot ROC curve
    plt.plot([0, 1], [0, 1], "k--")
    plt.plot(fpr, tpr)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve")
    plt.savefig("roc_curve.png")
    plt.close()

    # Upload ROC curve to S3
    # ds = kwargs["execution_date"].strftime("%Y-%m-%d-%H-%M-%S")
    ds = prefect.context.scheduled_start_time.strftime("%Y-%m-%d-%H-%M-%S")
    curveKey = ds + "/roc_curve_model_rf.png"

    botoArgs = dict(
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
        endpoint_url="http://minio:9000",
    )
    with open("roc_curve.png", "rb") as f:
        curveKey = S3Upload(bucket="airflow-port", boto_kwargs=botoArgs).run(
            f.read(), key=curveKey
        )
    # s3.load_file(
    #     filename="roc_curve.png",
    #     key=curveKey,
    #     bucket_name="dag-umba",
    #     replace=True,
    # )
    # Upload y_pred to S3
    # y_pred_key = ds + "/trainingData/y_pred_model_rf.npy"
    # np.save("y_pred_model_rf.npy", y_pred)
    # s3.load_file(
    #     filename="y_pred_model_rf.npy",
    #     key=y_pred_key,
    #     bucket_name="dag-umba",
    #     replace=True,
    # )

    return {
        "y_pred": y_pred,
        "roc_curve": curveKey,
        "details": "Best Score generated by Grid Search: {}\nParameters of the Best calculated Grid: {}".format(
            grid_search.best_score_, grid_search.best_params_
        ),
    }


@task
def Model_XGB(cleanData):
    from sklearn.model_selection import GridSearchCV
    from xgboost import XGBClassifier

    # ti = kwargs["ti"]
    # # Get key from the PrepareData task
    # X_train_key = ti.xcom_pull(task_ids="PrepareData", key="X_train")
    # Y_train_key = ti.xcom_pull(task_ids="PrepareData", key="y_train")
    # X_test_key = ti.xcom_pull(task_ids="PrepareData", key="X_test")
    # Y_test_key = ti.xcom_pull(task_ids="PrepareData", key="y_test")

    # # Download from S3
    # s3 = S3Hook(aws_conn_id="custom_s3")
    # X_train_path = s3.download_file(key=X_train_key, bucket_name="dag-umba")
    # Y_train_path = s3.download_file(key=Y_train_key, bucket_name="dag-umba")
    # X_test_path = s3.download_file(key=X_test_key, bucket_name="dag-umba")
    # Y_test_path = s3.download_file(key=Y_test_key, bucket_name="dag-umba")

    # Load Numpy arrays
    X_train = cleanData["X_train"]
    y_train = cleanData["y_train"]
    X_test = cleanData["X_test"]
    y_test = cleanData["y_test"]

    # Seting the Hyper Parameters
    param_test1 = {
        "max_depth": [3, 5, 6, 10],
        "min_child_weight": [3, 5, 10],
        "gamma": [0.0, 0.1, 0.2, 0.3, 0.4],
        # 'reg_alpha':[1e-5, 1e-2, 0.1, 1, 10],
        "subsample": [i / 100.0 for i in range(75, 90, 5)],
        "colsample_bytree": [i / 100.0 for i in range(75, 90, 5)],
    }

    # Creating the classifier
    model_xg = XGBClassifier(random_state=2)

    grid_search = GridSearchCV(model_xg, param_grid=param_test1, cv=5, scoring="recall")
    grid_search.fit(X_train, y_train)
    y_pred = grid_search.predict(X_test)
    # Roc Curve it could be a new module
    y_pred_prob = grid_search.predict_proba(X_test)[:, 1]
    # Generate ROC curve values: fpr, tpr, thresholds
    fpr, tpr, thresholds = roc_curve(y_test, y_pred_prob)

    # Plot ROC curve
    plt.plot([0, 1], [0, 1], "k--")
    plt.plot(fpr, tpr)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve")
    plt.savefig("roc_curve.png")
    plt.close()

    # Upload ROC curve to S3
    # ds = kwargs["execution_date"].strftime("%Y-%m-%d-%H-%M-%S")
    ds = prefect.context.scheduled_start_time.strftime("%Y-%m-%d-%H-%M-%S")
    curveKey = ds + "/roc_curve_model_xgb.png"

    botoArgs = dict(
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
        endpoint_url="http://minio:9000",
    )
    with open("roc_curve.png", "rb") as f:
        curveKey = S3Upload(bucket="airflow-port", boto_kwargs=botoArgs).run(
            f.read(), key=curveKey
        )

    # s3.load_file(
    #     filename="roc_curve.png",
    #     key=curveKey,
    #     bucket_name="dag-umba",
    #     replace=True,
    # )

    # Upload y_pred to S3
    # y_pred_key = ds + "/trainingData/y_pred_model_xgb.npy"
    # np.save("y_pred_model_xgb.npy", y_pred)
    # s3.load_file(
    #     filename="y_pred_model_xgb.npy",
    #     key=y_pred_key,
    #     bucket_name="dag-umba",
    #     replace=True,
    # )

    return {
        "y_pred": y_pred,
        "roc_curve": curveKey,
        "details": "Best Score generated by Grid Search: {}\nParameters of the Best calculated Grid: {}".format(
            grid_search.best_score_, grid_search.best_params_
        ),
    }


@task
def Custom_Pipeline(cleanData):
    """
    ## Custom Pipeline Node
    This node is used to execute a custom pipeline.
    Uses GaussianNB as baseline model along with some tuning with PCA and KBest.
    """
    from sklearn.pipeline import Pipeline
    from sklearn.pipeline import FeatureUnion
    from sklearn.decomposition import PCA
    from sklearn.feature_selection import SelectKBest
    from sklearn.naive_bayes import GaussianNB

    # ti = kwargs["ti"]
    # # Get key from the PrepareData task
    # X_train_key = ti.xcom_pull(task_ids="PrepareData", key="X_train")
    # Y_train_key = ti.xcom_pull(task_ids="PrepareData", key="y_train")
    # X_test_key = ti.xcom_pull(task_ids="PrepareData", key="X_test")
    # Y_test_key = ti.xcom_pull(task_ids="PrepareData", key="y_test")

    # # Download from S3
    # s3 = S3Hook(aws_conn_id="custom_s3")
    # X_train_path = s3.download_file(key=X_train_key, bucket_name="dag-umba")
    # Y_train_path = s3.download_file(key=Y_train_key, bucket_name="dag-umba")
    # X_test_path = s3.download_file(key=X_test_key, bucket_name="dag-umba")
    # Y_test_path = s3.download_file(key=Y_test_key, bucket_name="dag-umba")

    # Load Numpy arrays
    X_train = cleanData["X_train"]
    y_train = cleanData["y_train"]
    X_test = cleanData["X_test"]
    y_test = cleanData["y_test"]

    features = []
    features.append(("pca", PCA(n_components=2)))
    features.append(("select_best", SelectKBest(k=6)))
    feature_union = FeatureUnion(features)
    # create pipeline
    estimators = []
    estimators.append(("feature_union", feature_union))
    estimators.append(("logistic", GaussianNB()))
    model = Pipeline(estimators)
    # evaluate pipeline
    # seed = 7
    # kfold = KFold(n_splits=10)
    # results = cross_val_score(model, X_train, y_train, cv=kfold)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    # Roc Curve it could be a new module
    y_pred_prob = model.predict_proba(X_test)[:, 1]
    # Generate ROC curve values: fpr, tpr, thresholds
    fpr, tpr, thresholds = roc_curve(y_test, y_pred_prob)

    # Plot ROC curve
    plt.plot([0, 1], [0, 1], "k--")
    plt.plot(fpr, tpr)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve")
    plt.savefig("roc_curve.png")
    plt.close()

    # Upload ROC curve to S3
    # ds = kwargs["execution_date"].strftime("%Y-%m-%d-%H-%M-%S")
    ds = prefect.context.scheduled_start_time.strftime("%Y-%m-%d-%H-%M-%S")

    botoArgs = dict(
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
        endpoint_url="http://minio:9000",
    )
    curveKey = ds + "/roc_curve_pipeline.png"
    with open("roc_curve.png", "rb") as f:
        curveKey = S3Upload(bucket="airflow-port", boto_kwargs=botoArgs).run(
            f.read(), key=curveKey
        )
    # s3.load_file(
    #     filename="roc_curve.png",
    #     key=curveKey,
    #     bucket_name="dag-umba",
    #     replace=True,
    # )

    # Upload y_pred to S3
    # y_pred_key = ds + "/trainingData/y_pred_pipeline.npy"
    # np.save("y_pred_pipeline.npy", y_pred)
    # s3.load_file(
    #     filename="y_pred_pipeline.npy",
    #     key=y_pred_key,
    #     bucket_name="dag-umba",
    #     replace=True,
    # )

    return {
        "y_pred": y_pred,
        "roc_curve": curveKey,
        "details": "Model Score: {}".format(model.score(X_train, y_train)),
    }
