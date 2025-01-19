# Home Assistant Datasets

This package is a collection of datasets for evaluating AI Models in the context
of Home Assistant. The overall approach is:
- Synthetic Data Generation: Create synthetic datasets that represent a home
- Synthetic Home: Load the data into Home Assistant and exercise different device states (e.g. light on, off)
- Model Evaluation: Evaluate Home Assistant Conversation agents with different models (e.g. OpenAI, Google, local models)
- Human Annotation: Humans can annotate the results (e.g. great, ok, bad)
- Results Visualization: Track improvements over time with different models, prompts, tools, RAG, etc.

```mermaid
graph LR;
    A[Synthetic Data Generation]
    B[Dataset]
    C[Model Evaluation]
    D[Synthetic Home]
    F[Human Annotation]
    G[Visualize Results]

    H[OpenAI]
    I[Conversation Agent]

    J[Local LM]
    K[Conversation Agent]

    L[Google]
    M[Conversation Agent]

    A --> B
    B --> D
    D --> C
    C --> F
    F --> G

    H --> I
    J --> K
    L --> M

    I --> C
    K --> C
    M --> C

    I --> D
    K --> D
    M --> D
```

The idea would also be to start building datasets that can be used for training in the future.

## Synthetic Datasets

See the [datasets README](datasets/README.md) for details on the available
datasets including Home descriptions, Area descriptions, Device descriptions
and summaries that can be performed on a home.

The device level datasets are defined using the [Synthetic Home](https://github.com/allenporter/home-assistant-synthetic-home/)
format including its device registry of synthetic devices.

### Synthetic Data Generation

See the [generation README](generation/README.md) for more details on how synthetic
data generation using LLMs works. The data is generated from a small amount of seed
example data and a prompt, then is persisted.

The synthetic data generation is run with Jupyter notebooks.


```mermaid

classDiagram
    direction LR
    Home <|-- Area
    Area <|-- Device
    Device <|-- EntityStates
    class Home{
        +String name
        +String country_code
        +String location
        +String type
    }
    class Area {
        +String name
    }
    class Device {
        +String name
        +String device_type
        +String model
        +String mfg
        +String sw_version
    }
    class EntityState {
        +String state
    }

```

## Model Evaluation

You can use the generated synthetic data in Home Assistat and with integrated
converation agents to produce outputs for evaluation.

Model evaluation is currently performed with pytest, [Synthetic Home](https://github.com/allenporter/home-assistant-synthetic-home/), and any conversation agent (Open AI, Google, custom components, etc)

See [docs/eval.md] for instructions on how run an evaluation and update the
leaderboard.

### Home Assistant Actions - Offline Evaluation

The most commonly used evaluation is for the Home Assistant conversation agent actions
for integrating with the assist pipeline. See the following dataset directories
for more information on running an evaluation:

- [datasets/assist](datasets/assist/README.md) - Dataset with a set of corner cases meant to challenge models on voice actions, but with a medium size home.
- [datasets/assist-mini](datasets/assist-mini/README.md) - A much simpler dataset set of tasks for smaller models using very limited number of entities.
- [datasets/intents](datasets/intents/README.md) - A dataset based on the home assistant intents repository unit tests that are used for the NLP model. These have a very large home.


Models are configured in `models.yaml`.

### Example Evaluation for Area Summaries

There are additional datasets for human evaluation of summarization tasks. These were the
initial use case for this repo. It works something like this:

- Configure the Synthetic Home and devices
- Configure the conversation agent and prompt ("summarize this area")
- Ask the conversation agent to summarize:
  - Each area of the home
  - For each interesting device state in the area (e.g. lights on, lights off)
- Record the results

These can be used for human evaluation to determine the model quality. In this phase, we take the model outputs from a human rater and use them for
evaluation.

Human rater (me) scores the result quality:
  - 1: Low: Bad, incorrect, misleading, etc.
  - 2: Medium: Solid, not incorrect, though perhaps a missed opportunity
  - 3: High: Good

See the [script/](script/) directory for more details on preparing the data for
human eval procedure using Doccano.
