import prefect
from prefect import task
from prefect.tasks.aws.s3 import S3Upload, S3Download

import pandas as pd
import numpy as np

from io import StringIO

@task()
def VisualAnalysis(dataPath):
    """
    # Visual Analysis
    Renders multiple graphs that help explore the data.
    """
    botoArgs = dict(
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
        endpoint_url="http://minio:9000",
    )
    # s3 = S3Hook(aws_conn_id="custom_s3")
    # downloadPath = s3.download_file(key=dataPath, bucket_name="dag-umba")
    downloadContents = S3Download(
        bucket="airflow-port",
        boto_kwargs=botoArgs
    ).run(dataPath)
    df_credit = pd.read_csv(StringIO(downloadContents))
    # it's a library that we work with plotly
    # import plotly.offline as py
    import plotly.graph_objs as go  # it's like "plt" of matplot
    import plotly.tools as tls  # It's useful to we get some tools of plotly
    import matplotlib.pyplot as plt  # to plot some parameters in seaborn
    import seaborn as sns  # Graph library that use matplot in background
    from io import BytesIO
    import base64

    graphs = []
    # ------------------------------------------ Graph 1 ----------------------------------------- #

    trace0 = go.Bar(
        x=df_credit[df_credit["Risk"] == "good"]["Risk"].value_counts().index.values,
        y=df_credit[df_credit["Risk"] == "good"]["Risk"].value_counts().values,
        name="Good credit",
    )

    trace1 = go.Bar(
        x=df_credit[df_credit["Risk"] == "bad"]["Risk"].value_counts().index.values,
        y=df_credit[df_credit["Risk"] == "bad"]["Risk"].value_counts().values,
        name="Bad credit",
    )

    data = [trace0, trace1]

    layout = go.Layout()

    layout = go.Layout(
        yaxis=dict(title="Count"),
        xaxis=dict(title="Risk Variable"),
        title="Target variable distribution",
    )

    fig = go.Figure(data=data, layout=layout)
    graphs.append(fig)

    # ------------------------------------------ Graph 2 ----------------------------------------- #
    print(df_credit.columns)

    df_good = df_credit.loc[df_credit["Risk"] == "good"]["Age"].values.tolist()
    df_bad = df_credit.loc[df_credit["Risk"] == "bad"]["Age"].values.tolist()
    df_age = df_credit["Age"].values.tolist()

    # First plot
    trace0 = go.Histogram(x=df_good, histnorm="probability", name="Good Credit")
    # Second plot
    trace1 = go.Histogram(x=df_bad, histnorm="probability", name="Bad Credit")
    # Third plot
    trace2 = go.Histogram(x=df_age, histnorm="probability", name="Overall Age")

    # Creating the grid
    fig = tls.make_subplots(
        rows=2,
        cols=2,
        specs=[[{}, {}], [{"colspan": 2}, None]],
        subplot_titles=("Good", "Bad", "General Distribuition"),
    )

    # setting the figs
    fig.append_trace(trace0, 1, 1)
    fig.append_trace(trace1, 1, 2)
    fig.append_trace(trace2, 2, 1)

    fig["layout"].update(showlegend=True, title="Age Distribuition", bargap=0.05)
    # py.iplot(fig, filename="custom-sized-subplot-with-subplot-titles")
    graphs.append(fig)

    # ------------------------------------------ Graph 3 ----------------------------------------- #
    df_good = df_credit[df_credit["Risk"] == "good"]
    df_bad = df_credit[df_credit["Risk"] == "bad"]

    fig, ax = plt.subplots(nrows=2, figsize=(12, 8))
    plt.subplots_adjust(hspace=0.4, top=0.8)

    g1 = sns.distplot(df_good["Age"], ax=ax[0], color="g")
    g1 = sns.distplot(df_bad["Age"], ax=ax[0], color="r")
    g1.set_title("Age Distribuition", fontsize=15)
    g1.set_xlabel("Age")
    g1.set_xlabel("Frequency")

    g2 = sns.countplot(x="Age", data=df_credit, palette="hls", ax=ax[1], hue="Risk")
    g2.set_title("Age Counting by Risk", fontsize=15)
    g2.set_xlabel("Age")
    g2.set_xlabel("Count")
    graphs.append(fig)

    # ------------------------------------------ Graph 4 ----------------------------------------- #
    trace0 = go.Box(
        y=df_good["Credit amount"],
        x=df_good["Age_cat"],
        name="Good credit",
        marker=dict(color="#3D9970"),
    )

    trace1 = go.Box(
        y=df_bad["Credit amount"],
        x=df_bad["Age_cat"],
        name="Bad credit",
        marker=dict(color="#FF4136"),
    )

    data = [trace0, trace1]

    layout = go.Layout(
        yaxis=dict(title="Credit Amount (US Dollar)", zeroline=False),
        xaxis=dict(title="Age Categorical"),
        boxmode="group",
    )
    fig = go.Figure(data=data, layout=layout)
    graphs.append(fig)
    # ------------------------------------------ Graph 5 ----------------------------------------- #
    # First plot
    trace0 = go.Bar(
        x=df_credit[df_credit["Risk"] == "good"]["Housing"].value_counts().index.values,
        y=df_credit[df_credit["Risk"] == "good"]["Housing"].value_counts().values,
        name="Good credit",
    )

    # Second plot
    trace1 = go.Bar(
        x=df_credit[df_credit["Risk"] == "bad"]["Housing"].value_counts().index.values,
        y=df_credit[df_credit["Risk"] == "bad"]["Housing"].value_counts().values,
        name="Bad Credit",
    )

    data = [trace0, trace1]

    layout = go.Layout(title="Housing Distribuition")

    fig = go.Figure(data=data, layout=layout)

    graphs.append(fig)
    # ------------------------------------------ Graph 6 ----------------------------------------- #
    fig = {
        "data": [
            {
                "type": "violin",
                "x": df_good["Housing"],
                "y": df_good["Credit amount"],
                "legendgroup": "Good Credit",
                "scalegroup": "No",
                "name": "Good Credit",
                "side": "negative",
                "box": {"visible": True},
                "meanline": {"visible": True},
                "line": {"color": "blue"},
            },
            {
                "type": "violin",
                "x": df_bad["Housing"],
                "y": df_bad["Credit amount"],
                "legendgroup": "Bad Credit",
                "scalegroup": "No",
                "name": "Bad Credit",
                "side": "positive",
                "box": {"visible": True},
                "meanline": {"visible": True},
                "line": {"color": "green"},
            },
        ],
        "layout": {
            "yaxis": {
                "zeroline": False,
            },
            "violingap": 0,
            "violinmode": "overlay",
        },
    }
    fig = go.Figure(fig)
    # py.iplot(fig, filename = 'violin/split', validate = False)
    graphs.append(fig)
    # ------------------------------------------ Graph 7 ----------------------------------------- #
    # First plot
    trace0 = go.Bar(
        x=df_credit[df_credit["Risk"] == "good"]["Sex"].value_counts().index.values,
        y=df_credit[df_credit["Risk"] == "good"]["Sex"].value_counts().values,
        name="Good credit",
    )

    # First plot 2
    trace1 = go.Bar(
        x=df_credit[df_credit["Risk"] == "bad"]["Sex"].value_counts().index.values,
        y=df_credit[df_credit["Risk"] == "bad"]["Sex"].value_counts().values,
        name="Bad Credit",
    )

    # Second plot
    trace2 = go.Box(
        x=df_credit[df_credit["Risk"] == "good"]["Sex"],
        y=df_credit[df_credit["Risk"] == "good"]["Credit amount"],
        name=trace0.name,
    )

    # Second plot 2
    trace3 = go.Box(
        x=df_credit[df_credit["Risk"] == "bad"]["Sex"],
        y=df_credit[df_credit["Risk"] == "bad"]["Credit amount"],
        name=trace1.name,
    )

    data = [trace0, trace1, trace2, trace3]

    fig = tls.make_subplots(
        rows=1, cols=2, subplot_titles=("Sex Count", "Credit Amount by Sex")
    )

    fig.append_trace(trace0, 1, 1)
    fig.append_trace(trace1, 1, 1)
    fig.append_trace(trace2, 1, 2)
    fig.append_trace(trace3, 1, 2)

    fig["layout"].update(
        height=400, width=800, title="Sex Distribuition", boxmode="group"
    )
    # py.iplot(fig, filename='sex-subplot')
    graphs.append(fig)

    # ------------------------------------------ Graph 8 ----------------------------------------- #
    # First plot
    trace0 = go.Bar(
        x=df_credit[df_credit["Risk"] == "good"]["Job"].value_counts().index.values,
        y=df_credit[df_credit["Risk"] == "good"]["Job"].value_counts().values,
        name="Good credit Distribuition",
    )

    # Second plot
    trace1 = go.Bar(
        x=df_credit[df_credit["Risk"] == "bad"]["Job"].value_counts().index.values,
        y=df_credit[df_credit["Risk"] == "bad"]["Job"].value_counts().values,
        name="Bad Credit Distribuition",
    )

    data = [trace0, trace1]

    layout = go.Layout(title="Job Distribuition")

    fig = go.Figure(data=data, layout=layout)
    # py.iplot(fig, filename='grouped-bar')
    graphs.append(fig)
    # ------------------------------------------ Graph 9 ----------------------------------------- #
    trace0 = go.Box(x=df_good["Job"], y=df_good["Credit amount"], name="Good credit")

    trace1 = go.Box(x=df_bad["Job"], y=df_bad["Credit amount"], name="Bad credit")

    data = [trace0, trace1]

    layout = go.Layout(
        yaxis=dict(title="Credit Amount distribuition by Job"), boxmode="group"
    )
    fig = go.Figure(data=data, layout=layout)
    graphs.append(fig)
    # py.iplot(fig, filename='box-age-cat')
    # ------------------------------------------ Graph 10 ----------------------------------------- #

    fig = {
        "data": [
            {
                "type": "violin",
                "x": df_good["Job"],
                "y": df_good["Age"],
                "legendgroup": "Good Credit",
                "scalegroup": "No",
                "name": "Good Credit",
                "side": "negative",
                "box": {"visible": True},
                "meanline": {"visible": True},
                "line": {"color": "blue"},
            },
            {
                "type": "violin",
                "x": df_bad["Job"],
                "y": df_bad["Age"],
                "legendgroup": "Bad Credit",
                "scalegroup": "No",
                "name": "Bad Credit",
                "side": "positive",
                "box": {"visible": True},
                "meanline": {"visible": True},
                "line": {"color": "green"},
            },
        ],
        "layout": {
            "yaxis": {
                "zeroline": False,
            },
            "violingap": 0,
            "violinmode": "overlay",
        },
    }
    graphs.append(go.Figure(fig))
    # py.iplot(fig, filename = 'Age-Housing', validate = False)
    # ------------------------------------------ Graph 11 ----------------------------------------- #
    fig, ax = plt.subplots(figsize=(12, 12), nrows=2)

    g1 = sns.boxplot(
        x="Job", y="Credit amount", data=df_credit, palette="hls", ax=ax[0], hue="Risk"
    )
    g1.set_title("Credit Amount by Job", fontsize=15)
    g1.set_xlabel("Job Reference", fontsize=12)
    g1.set_ylabel("Credit Amount", fontsize=12)

    g2 = sns.violinplot(
        x="Job",
        y="Age",
        data=df_credit,
        ax=ax[1],
        hue="Risk",
        split=True,
        palette="hls",
    )
    g2.set_title("Job Type reference x Age", fontsize=15)
    g2.set_xlabel("Job Reference", fontsize=12)
    g2.set_ylabel("Age", fontsize=12)

    plt.subplots_adjust(hspace=0.4, top=0.9)

    graphs.append(fig)
    # ------------------------------------------- Graph 12 ----------------------------------------- #
    import plotly.figure_factory as ff
    import numpy as np

    # Add histogram data
    x1 = np.log(df_good["Credit amount"])
    x2 = np.log(df_bad["Credit amount"])

    # Group data together
    hist_data = [x1, x2]

    group_labels = ["Good Credit", "Bad Credit"]

    # Create distplot with custom bin_size
    fig = ff.create_distplot(hist_data, group_labels, bin_size=0.2)

    # Plot!
    # py.iplot(fig, filename='Distplot with Multiple Datasets')
    graphs.append(fig)
    # ------------------------------------------ Graph 13 ----------------------------------------- #
    # Ploting the good and bad dataframes in distplot
    fig = plt.figure(figsize=(8, 5))

    g = sns.distplot(df_good["Credit amount"], color="r")
    g = sns.distplot(df_bad["Credit amount"], color="g")
    g.set_title("Credit Amount Frequency distribuition", fontsize=15)
    # plt.show()
    graphs.append(fig)
    # ------------------------------------------ Graph 14 ----------------------------------------- #
    from plotly import tools
    import numpy as np
    import plotly.graph_objs as go

    count_good = go.Bar(
        x=df_good["Saving accounts"].value_counts().index.values,
        y=df_good["Saving accounts"].value_counts().values,
        name="Good credit",
    )
    count_bad = go.Bar(
        x=df_bad["Saving accounts"].value_counts().index.values,
        y=df_bad["Saving accounts"].value_counts().values,
        name="Bad credit",
    )

    box_1 = go.Box(
        x=df_good["Saving accounts"], y=df_good["Credit amount"], name="Good credit"
    )
    box_2 = go.Box(
        x=df_bad["Saving accounts"], y=df_bad["Credit amount"], name="Bad credit"
    )

    scat_1 = go.Box(x=df_good["Saving accounts"], y=df_good["Age"], name="Good credit")
    scat_2 = go.Box(x=df_bad["Saving accounts"], y=df_bad["Age"], name="Bad credit")

    data = [scat_1, scat_2, box_1, box_2, count_good, count_bad]

    fig = tools.make_subplots(
        rows=2,
        cols=2,
        specs=[[{}, {}], [{"colspan": 2}, None]],
        subplot_titles=(
            "Count Saving Accounts",
            "Credit Amount by Savings Acc",
            "Age by Saving accounts",
        ),
    )

    fig.append_trace(count_good, 1, 1)
    fig.append_trace(count_bad, 1, 1)

    fig.append_trace(box_2, 1, 2)
    fig.append_trace(box_1, 1, 2)

    fig.append_trace(scat_1, 2, 1)
    fig.append_trace(scat_2, 2, 1)

    fig["layout"].update(
        height=700, width=800, title="Saving Accounts Exploration", boxmode="group"
    )

    # py.iplot(fig, filename="combined-savings")
    graphs.append(fig)
    # ------------------------------------------ Graph 15 ----------------------------------------- #
    print("Description of Distribuition Saving accounts by Risk:  ")
    print(pd.crosstab(df_credit["Saving accounts"], df_credit.Risk))

    fig, ax = plt.subplots(3, 1, figsize=(12, 12))
    g = sns.countplot(
        x="Saving accounts", data=df_credit, palette="hls", ax=ax[0], hue="Risk"
    )
    g.set_title("Saving Accounts Count", fontsize=15)
    g.set_xlabel("Saving Accounts type", fontsize=12)
    g.set_ylabel("Count", fontsize=12)

    g1 = sns.violinplot(
        x="Saving accounts",
        y="Job",
        data=df_credit,
        palette="hls",
        hue="Risk",
        ax=ax[1],
        split=True,
    )
    g1.set_title("Saving Accounts by Job", fontsize=15)
    g1.set_xlabel("Savings Accounts type", fontsize=12)
    g1.set_ylabel("Job", fontsize=12)

    g = sns.boxplot(
        x="Saving accounts",
        y="Credit amount",
        data=df_credit,
        ax=ax[2],
        hue="Risk",
        palette="hls",
    )
    g2.set_title("Saving Accounts by Credit Amount", fontsize=15)
    g2.set_xlabel("Savings Accounts type", fontsize=12)
    g2.set_ylabel("Credit Amount(US)", fontsize=12)

    plt.subplots_adjust(hspace=0.4, top=0.9)
    graphs.append(fig)
    # plt.show()

    # ------------------------------------------ Graph 16 ----------------------------------------- #
    print("Values describe: ")
    print(pd.crosstab(df_credit.Purpose, df_credit.Risk))

    fig = plt.figure(figsize=(14, 12))

    plt.subplot(221)
    g = sns.countplot(x="Purpose", data=df_credit, palette="hls", hue="Risk")
    g.set_xticklabels(g.get_xticklabels(), rotation=45)
    g.set_xlabel("", fontsize=12)
    g.set_ylabel("Count", fontsize=12)
    g.set_title("Purposes Count", fontsize=20)

    plt.subplot(222)
    g1 = sns.violinplot(
        x="Purpose", y="Age", data=df_credit, palette="hls", hue="Risk", split=True
    )
    g1.set_xticklabels(g1.get_xticklabels(), rotation=45)
    g1.set_xlabel("", fontsize=12)
    g1.set_ylabel("Count", fontsize=12)
    g1.set_title("Purposes by Age", fontsize=20)

    plt.subplot(212)
    g2 = sns.boxplot(
        x="Purpose", y="Credit amount", data=df_credit, palette="hls", hue="Risk"
    )
    g2.set_xlabel("Purposes", fontsize=12)
    g2.set_ylabel("Credit Amount", fontsize=12)
    g2.set_title("Credit Amount distribuition by Purposes", fontsize=20)

    plt.subplots_adjust(hspace=0.6, top=0.8)
    graphs.append(fig)

    # ------------------------------------------ Graph 17 ----------------------------------------- #
    fig = plt.figure(figsize=(12, 14))

    g = plt.subplot(311)
    g = sns.countplot(x="Duration", data=df_credit, palette="hls", hue="Risk")
    g.set_xlabel("Duration Distribuition", fontsize=12)
    g.set_ylabel("Count", fontsize=12)
    g.set_title("Duration Count", fontsize=20)

    g1 = plt.subplot(312)
    g1 = sns.pointplot(
        x="Duration", y="Credit amount", data=df_credit, hue="Risk", palette="hls"
    )
    g1.set_xlabel("Duration", fontsize=12)
    g1.set_ylabel("Credit Amount(US)", fontsize=12)
    g1.set_title("Credit Amount distribuition by Duration", fontsize=20)

    g2 = plt.subplot(313)
    g2 = sns.distplot(df_good["Duration"], color="g")
    g2 = sns.distplot(df_bad["Duration"], color="r")
    g2.set_xlabel("Duration", fontsize=12)
    g2.set_ylabel("Frequency", fontsize=12)
    g2.set_title("Duration Frequency x good and bad Credit", fontsize=20)

    plt.subplots_adjust(wspace=0.4, hspace=0.4, top=0.9)

    graphs.append(fig)

    # ------------------------------------------ Graph 18 ----------------------------------------- #
    # First plot
    trace0 = go.Bar(
        x=df_credit[df_credit["Risk"] == "good"]["Checking account"]
        .value_counts()
        .index.values,
        y=df_credit[df_credit["Risk"] == "good"]["Checking account"]
        .value_counts()
        .values,
        name="Good credit Distribuition",
    )

    # Second plot
    trace1 = go.Bar(
        x=df_credit[df_credit["Risk"] == "bad"]["Checking account"]
        .value_counts()
        .index.values,
        y=df_credit[df_credit["Risk"] == "bad"]["Checking account"]
        .value_counts()
        .values,
        name="Bad Credit Distribuition",
    )

    data = [trace0, trace1]

    layout = go.Layout(
        title="Checking accounts Distribuition",
        xaxis=dict(title="Checking accounts name"),
        yaxis=dict(title="Count"),
        barmode="group",
    )

    fig = go.Figure(data=data, layout=layout)

    # py.iplot(fig, filename = 'Age-ba', validate = False)
    graphs.append(fig)

    # ------------------------------------------ Graph 19 ----------------------------------------- #
    df_good = df_credit[df_credit["Risk"] == "good"]
    df_bad = df_credit[df_credit["Risk"] == "bad"]

    trace0 = go.Box(
        y=df_good["Credit amount"],
        x=df_good["Checking account"],
        name="Good credit",
        marker=dict(color="#3D9970"),
    )

    trace1 = go.Box(
        y=df_bad["Credit amount"],
        x=df_bad["Checking account"],
        name="Bad credit",
        marker=dict(color="#FF4136"),
    )

    data = [trace0, trace1]

    layout = go.Layout(yaxis=dict(title="Cheking distribuition"), boxmode="group")
    fig = go.Figure(data=data, layout=layout)

    # py.iplot(fig, filename='box-age-cat')
    graphs.append(fig)
    # ------------------------------------------ Graph 20 ----------------------------------------- #
    print("Total values of the most missing variable: ")
    print(df_credit.groupby("Checking account")["Checking account"].count())

    fig = plt.figure(figsize=(12, 10))

    g = plt.subplot(221)
    g = sns.countplot(x="Checking account", data=df_credit, palette="hls", hue="Risk")
    g.set_xlabel("Checking Account", fontsize=12)
    g.set_ylabel("Count", fontsize=12)
    g.set_title("Checking Account Counting by Risk", fontsize=20)

    g1 = plt.subplot(222)
    g1 = sns.violinplot(
        x="Checking account",
        y="Age",
        data=df_credit,
        palette="hls",
        hue="Risk",
        split=True,
    )
    g1.set_xlabel("Checking Account", fontsize=12)
    g1.set_ylabel("Age", fontsize=12)
    g1.set_title("Age by Checking Account", fontsize=20)

    g2 = plt.subplot(212)
    g2 = sns.boxplot(
        x="Checking account",
        y="Credit amount",
        data=df_credit,
        hue="Risk",
        palette="hls",
    )
    g2.set_xlabel("Checking Account", fontsize=12)
    g2.set_ylabel("Credit Amount(US)", fontsize=12)
    g2.set_title("Credit Amount by Cheking Account", fontsize=20)

    plt.subplots_adjust(wspace=0.2, hspace=0.3, top=0.9)

    graphs.append(fig)
    # ------------------------------------------ Graph 21 ----------------------------------------- #
    fig = plt.figure(figsize=(10, 6))

    g = sns.violinplot(
        x="Housing", y="Job", data=df_credit, hue="Risk", palette="hls", split=True
    )
    g.set_xlabel("Housing", fontsize=12)
    g.set_ylabel("Job", fontsize=12)
    g.set_title("Housing x Job - Dist", fontsize=20)

    graphs.append(fig)
    # -------------------------------------------------------------------------------------------- #
    with open("VisualAnalysis.html", "w") as f:
        for graph in graphs:
            if isinstance(graph, go.Figure):
                f.write(graph.to_html(full_html=False, include_plotlyjs="cdn"))
            elif isinstance(graph, plt.Figure):
                g = BytesIO()
                graph.savefig(g, format="png")
                encoded = base64.b64encode(g.getvalue()).decode("utf-8")
                html_string = """<img src="data:image/png;base64,{}">""".format(encoded)
                f.write(html_string)
            else:
                print("Invalid Graph Type Found: " + str(type(graph)))

    # Upload to S3
    # ds = kwargs["execution_date"].strftime("%Y-%m-%d-%H-%M-%S")
    ds = prefect.context.scheduled_start_time.strftime("%Y-%m-%d-%H-%M-%S")
    key = ds + "/VisualAnalysis.html"
    
    # s3.load_file(
    #     bucket_name="dag-umba",
    #     key=key,
    #     filename="VisualAnalysis.html",
    #     replace=True,
    # )
    with open("VisualAnalysis.html", "r", encoding="utf-8") as f:
        contents = f.read()
        key = S3Upload(
            bucket="airflow-port",
            boto_kwargs=botoArgs
        ).run(contents, key=key)
        print("SUCCESS: " + key)

