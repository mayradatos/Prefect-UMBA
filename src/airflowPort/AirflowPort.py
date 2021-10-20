from prefect import Flow, case
from prefect.tasks.control_flow import merge
from prefect.run_configs import DockerRun
from prefect.storage import Docker
from prefect.executors import LocalDaskExecutor

# Structure from Airflow project
from Tasks import tasks, dataLoaders, models, graphs

with Flow(
    "Airflow Port",
    run_config=DockerRun(),
    #executor=LocalDaskExecutor(),
    storage=Docker(dockerfile="AirflowPort.Dockerfile"),
) as flow:
    data = dataLoaders.DataLoad()

    tasks.SimpleAnalysis(data)
    graphs.VisualAnalysis(data)
    cleanData = dataLoaders.PrepareData(data)

    tasks.CorrelationGrid(cleanData)
    # Switch statement
    selectedModel = tasks.SelectModel(cleanData)
    customPipeline = models.Custom_Pipeline(cleanData)

    with case(selectedModel, "NB"):
        NBModelResult = models.Model_NB(cleanData)
    with case(selectedModel, "RF"):
        RFModelResult = models.Model_RF(cleanData)
    with case(selectedModel, "XGB"):
        XGBModelResult = models.Model_XGB(cleanData)

    modelResult = merge(NBModelResult, RFModelResult, XGBModelResult)
    finalNode = tasks.WriteOutput(customPipeline, modelResult, cleanData)

flow.run()
