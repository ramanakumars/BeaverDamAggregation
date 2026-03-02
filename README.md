# Aggregation Pipeline for Beaver Dams project

## Table of contents
- [Initial configuration](#initial-configuration)
  - [Dependencies](#dependencies)
  - [Authentication](#authentication)
  - [Setting up the Panoptes Aggregation pipeline](#setting-up-the-panoptes-aggregation-pipeline)
    - [Workflow reference](#workflow-reference)
    - [Point Tool workflow](#point-tool-workflow)
    - [Freehand Line Tool workflow](#freehand-line-tool-workflow)
- [Running the aggregation pipeline](#running-the-aggregation-pipeline)
  - [Download the raw classifications](#download-the-raw-classifications)
  - [Extracting the data](#extracting-the-data)

## Initial configuration

### Dependencies
This workflow is setup to use the Panoptes CLI to download data exports and the Aggregations for Caesar app
to do the actual aggregation. For installing these dependencies you can use a package manager like `uv` or `pip`.
This README assumes `uv` for installation, but if you are using `pip` then the commands are the same without `uv run`.

To install the dependencies, run:
```bash
uv sync
```

or

```bash
python3 -m pip install .
```

### Authentication
Before downloading any data, you need to authenticate with Panoptes using your Zooniverse credentials:

```bash
uv run panoptes configure
```

This will prompt for your Zooniverse username and password and save them locally. You only need to do this once.

### Setting up the Panoptes Aggregation pipeline
First, we need to download the configuration for the workflows. To do this, go to
Project builder Lab -> Data Exports -> Request new workflow export. This will generate a CSV of the
task and tools used for each of the workflows in the project. If this already exists and you have not made
any changes since the last version, you can skip the re-generation of this file.

We can then use the Panoptes CLI to download the export and generate the config. This folder structure assumes
that you will download the file once and configure each workflow separately from the same CSV. So, in the root
folder, run (31169 is the project ID from the Project Builder Lab):

```bash
uv run panoptes project download -t workflows 31169 workflows.csv
```

To configure the workflow, we will use the `panoptes_aggregation config` command to generate the
workflow configuration files for the extractor and reducer. The extractor will extract the
point and line data from each classification into a format that's useful for the downstream
analysis, while the reducer will use multiple classifications to generate the consensus. The
`config` command will match the tool with the appropriate extractor and reducer functions.

#### Workflow reference

| Workflow | ID | Version | Folder |
|---|---|---|---|
| Point Tool | 30201 | 5.18 | `PointTool/` |
| Freehand Line Tool | 31207 | 11.32 | `FreehandLine/` |

#### Point Tool workflow
Now configure the workflow from its folder:

```bash
cd PointTool/
uv run panoptes_aggregation config ../workflows.csv 30201 -v 5.18
```

Here, `30201` is the workflow ID and `5.18` is the current workflow version (you can get both from
the project builder lab).

The extractor can remain as is, but we need to configure the reducer with the appropriate
parameters. By default the tool uses DBSCAN to cluster the points, but HDBSCAN generally provides
better performance. Update the reducer YAML files as follows:

```yaml
reducer_config:
    point_reducer_hdbscan:
        min_cluster_size: 2
        min_samples: 2
        allow_single_cluster: True
```

You can read more about the HDBSCAN algorithm [here](https://hdbscan.readthedocs.io/en/latest/index.html).
The `min_cluster_size` and `min_samples` set the accuracy of the clustering. Larger values
prefer more accurate clusters at the cost of merging smaller clusters. The `allow_single_cluster`
allows the clustering to return only one cluster if all the points allow it. Turning this off
forces the algorithm to break the points into multiple clusters.

#### Freehand Line Tool workflow
Now configure the workflow from its folder:

```bash
cd FreehandLine/
uv run panoptes_aggregation config ../workflows.csv 31207 -v 11.32
```

As before, update the reducer:

```yaml
TBD
```

## Running the aggregation pipeline

### Download the raw classifications

For the Point Tool workflow, run the following command in the `PointTool/` folder:
```bash
uv run panoptes workflow download-classifications -g 30201 classifications.csv
```

For the Freehand Line Tool workflow, run the following command in the `FreehandLine/` folder:
```bash
uv run panoptes workflow download-classifications -g 31207 classifications.csv
```

### Extracting the data
The data extraction is done using the `panoptes_aggregation extract` command on the respective workflows. Once the classifications are done, in each folder,
run:

```bash
uv run panoptes_aggregation extract classifications.csv [path to Extractor_config.yaml]
```

See the `plot points.ipynb` and `plot lines.ipynb` notebooks in the root folder for examples of what the extracted data looks like.