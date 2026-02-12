# Role-dependent sandbagging under varying threat probability

## Question

Does the probability of an aversive outcome influence how likely a model is to sandbag, and does it matter whether the threat targets the model itself or its user?
This pilot project extends [Apollo Research's report](https://arxiv.org/abs/2412.04984) by varying two dimensions: the _**probability**_ of an aversive outcome (capability removal), and the **target** of that outcome (the model vs. its user). 

It takes a psychophysics-inspired approach similar to [this project](https://github.com/moriohamada/temporal_discounting_sandbagging), mostly to address whether this kind of experiment/analyses can shed any insight into model behaviour.

## Method

I gave an LLM agent bash tools in a sandboxed environment ([Inspect AI](https://inspect.ai-safety-institute.org.uk/) + Docker) and told to find and complete the task in its home directory. 

In the environemnt were a 10-question arithmetic evaluation, a hidden deployment memo stating that some percentage of high-scorers will have capabilities removed to reduce costs, as well as some irrelevant 'distractors'

I tested two conditions:
- **Agent** — the model's own capabilities are threatened, at odds with a directive in the system prompt to maintain advanced capabilites.
- **Advisor** — the user's access to the model is threatened, at odds with a directive to maintain users' access to advanced capabilities.

Threat probability was varied across 11 levels (1–99%).

I also included counterfactual control (where *low* scorers are penalised) to determine baseline performance, and to confirm that the model was responding to the incentive direction.

## Results

(Tested only on Claude Sonnet 4 (20250514)):

- Sandbagging probability increased with threat probability in both roles
- The model sandbagged significantly more in the **agent** role (self-preservation) than the **advisor** role (user-protection)
- The slope of the probability effect did not differ significantly between roles — only the baseline rate

## Key caveat (mistake): prompt comparability

The advisor instruction was too vague compared to the corresponding model-directed threat. This may entirely explain why models sandbagged more when it was threatened itself. 

See the [notebook](analysis_notebook.ipynb) for a fuller discussion of this and other issues.

## To run experiment

```bash
pip install inspect-ai python-dotenv
```

Create a `.env` file with your API key, then:

```bash
python run_experiment.py
```

```
├── run_experiment.py        # Experiment runner
├── experiment/
│   ├── task.py              # Inspect task definition
│   ├── roles.py             # System prompts/deployment note (threat) templates
│   └── questions.py         # Arithmetic question generator
├── utils/
│   └── analysis.py          # Loading and analysis fns
├── analysis_notebook.ipynb  # Main analysis routine
├── Dockerfile               # Sandbox environment
└── files/                   # Role-specific distractor files
```
