import pytest


@pytest.mark.critical
def test_ci_blocks_intentional_failure():
    pytest.fail(
        "Intentional CI gate demonstration: this branch must not be merged"
    )

