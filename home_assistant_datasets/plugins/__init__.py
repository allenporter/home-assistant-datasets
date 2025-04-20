"""pytest plugins for driving evaluation tasks.

There are two primary plugins used by tests:

- pytest_scrape: This module is used when scraping outputs from a model. It is
    configured with a dataset and some models and stores the output in a model
    output directory.
- pytest_metrics: This module is for scoring or evaluating the outputs against
    the specified eval task. This reads the previously scraped output, evaluates
    the model on the tasks, and generates a summary report.

These modules internally use pytest plugins and libraries to perform the entire
workflow.
"""

__all__ = [
    "pytest_synthetic_home",
    "pytest_scrape",
    "pytest_metrics",
]
