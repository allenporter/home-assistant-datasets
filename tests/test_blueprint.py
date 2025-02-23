"""Tests for the blueprint module."""

import textwrap
from home_assistant_datasets.blueprint import (
    extract_blueprint_content,
)


def test_extract_yaml_from_markdown():
    """Test extracting yaml from markdown."""
    response = textwrap.dedent(
        """
    Here is some text
    ```yaml
    key: value
    ```
    And some more text
    """
    )
    with extract_blueprint_content(response) as content:
        assert content.status.valid
        assert content.yaml_content == "key: value"
        assert content.filename is not None


def test_invalid_markdown():
    """Test invalid markdown."""
    response = textwrap.dedent(
        """
    Here is some text
    And some more text
    """
    )
    with extract_blueprint_content(response) as content:
        assert not content.status.valid
        assert (
            content.status.error_details
            == "Could not extract YAML from model response:  Here is some text And some more text "
        )
        assert content.yaml_content is None
        assert content.filename is None
