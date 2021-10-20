import os
import prefect
from prefect import task, Flow, Parameter
from prefect.engine.results.s3_result import S3Result
from prefect.storage.docker import Docker
from prefect.tasks.aws.s3 import S3Upload, S3Download


@task
def add(x, y=1):
    """
    The only task we use so far here ;-)
    """
    logger = prefect.context.get("logger")
    logger.info("Hello from add(x,y)!")
    return x + y


@task
def download_file(filename):
    """
    Download the file
    """
    logger = prefect.context.get("logger")

    s3dl = S3Download(bucket="mayra-test", boto_kwargs=dict(
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
        endpoint_url="http://minio:9000",
    ))

    logger.info(f"Downloading {filename}")
    value = s3dl.run(filename)
    logger.info(f"Contents: {value}")
    return value

@task
def upload_file(filename):
    """
    Upload the file
    """
    logger = prefect.context.get("logger")

    s3ul = S3Upload(bucket="mayra-test", boto_kwargs=dict(
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
        endpoint_url="http://minio:9000",
    ))

    logger.info(f"Uploading {filename}")
    value = s3ul.run("Upload Test", key=filename)
    logger.info(f"Upload Key: {value}")
    return value


@task
def reader():
    """
    This task will read the file "data.txt" from the local filesystem
    """
    logger = prefect.context.get("logger")
    logger.info("Hello from reader()!")
    s3_result = S3Result(bucket="results")
    saved_result = s3_result.read("data.txt")
    model = saved_result.value
    logger.info(f"The model is {model}")



    # result = S3Result(
    #     bucket="results",
    #     boto3_kwargs=dict(
    #         aws_access_key_id="minioadmin",
    #         aws_secret_access_key="minioadmin",
    #         endpoint_url="http://minio:9000",
    #     ),
    # )

with Flow("Sample Flow") as flow:
    filename = Parameter("filename", default="hello2.txt")
    # first_result = add(1, y=2)
    # second_result = add(x=first_result, y=100)

    # Download the flow
    # download_file(filename)

    # Upload file
    upload_file(filename)

flow.run()


# create_flow()
