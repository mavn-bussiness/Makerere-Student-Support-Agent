from pathlib import Path

from src.core.download_mak_policies import (
    CATEGORY_PATH,
    POLICY_PATH,
    is_allowed_file_url,
    is_allowed_url,
    safe_name,
)


def test_only_expected_makerere_paths_are_allowed():
    assert is_allowed_url("https://policies.mak.ac.ug/policy-category/academic", CATEGORY_PATH)
    assert is_allowed_url("https://policies.mak.ac.ug/policy/student-welfare", POLICY_PATH)
    assert not is_allowed_url("https://evil.example/policy/student-welfare", POLICY_PATH)
    assert not is_allowed_url("https://policies.mak.ac.ug:443/policy/student-welfare", POLICY_PATH)
    assert not is_allowed_url("https://policies.mak.ac.ug/blog/spam", POLICY_PATH)


def test_file_links_are_restricted_to_the_site_file_tree():
    assert is_allowed_file_url("https://policies.mak.ac.ug/sites/default/files/policy.pdf")
    assert not is_allowed_file_url("https://other.example/sites/default/files/policy.pdf")
    assert not is_allowed_file_url("https://policies.mak.ac.ug/sites/default/files/")
    assert not is_allowed_file_url(
        "https://policies.mak.ac.ug/sites/default/files/../private.pdf"
    )
    assert not is_allowed_file_url(
        "https://policies.mak.ac.ug/sites/default/files/%2e%2e/private.pdf"
    )


def test_safe_name_prevents_path_traversal():
    filename = safe_name("../../Student policy (final).pdf")
    assert Path(filename).name == filename
    assert ".." not in filename