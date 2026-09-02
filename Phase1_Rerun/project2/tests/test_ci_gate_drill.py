import pytest


pytestmark = [
    pytest.mark.no_database,
    pytest.mark.critical,
]


def test_ci_failure_blocks_docker_build():
    pytest.fail("Intentional CI red-to-green drill")
