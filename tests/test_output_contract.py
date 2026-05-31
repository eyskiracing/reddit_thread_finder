"""Tests for the safety/output contract, security fixes, and dependency hardening."""

from __future__ import annotations

import unittest
from pathlib import Path

from reddit_thread_finder_core import constants
from reddit_thread_finder_core.models import (
    ALLOWED_OUTPUT_FIELDS,
    DISALLOWED_OUTPUT_FIELDS,
    RedditThreadResult,
)
from reddit_thread_finder_core.output import result_to_safe_dict, _resolve_safe_output_path
from reddit_thread_finder_core.focus import (
    analyze_topic_specificity,
    build_focused_query,
    create_search_brief,
    split_terms,
)
from reddit_thread_finder_core.query import generate_search_queries
from reddit_thread_finder_core.validation import parse_score, parse_positive_int, parse_yyyy_mm_dd


class OutputContractTests(unittest.TestCase):
    """Verify that result exports remain lightweight and safe."""

    def test_max_top_k_is_100(self):
        """Ensure the maximum returned links cap remains 100."""
        self.assertEqual(constants.MAX_TOP_K, 100)

    def test_output_fields_do_not_include_body_author_or_comments(self):
        """Ensure exported result fields exclude body, author, and comments."""
        result_fields = set(RedditThreadResult.__dataclass_fields__.keys())

        self.assertFalse(result_fields.intersection(DISALLOWED_OUTPUT_FIELDS))
        self.assertTrue(result_fields.issubset(ALLOWED_OUTPUT_FIELDS))

    def test_result_to_safe_dict_allows_only_safe_fields(self):
        """Ensure JSON conversion enforces the safe output schema."""
        result = RedditThreadResult(
            title="Example title",
            subreddit="example",
            url="https://www.reddit.com/r/example/comments/123/example",
            reddit_id="123",
            created_at="2026-01-01",
            reddit_score=10,
            num_comments=5,
            semantic_score=0.8,
            pain_score=0.5,
            engagement_score=0.2,
            recency_score=0.9,
            composite_score=0.75,
            matched_queries=["example query"],
        )

        safe = result_to_safe_dict(result)

        self.assertEqual(set(safe.keys()), ALLOWED_OUTPUT_FIELDS)
        self.assertFalse(set(safe.keys()).intersection(DISALLOWED_OUTPUT_FIELDS))


class OutputPathSecurityTests(unittest.TestCase):
    """Verify that JSON output path traversal is rejected."""

    def test_path_within_cwd_is_accepted(self):
        """A relative path within the current directory resolves successfully."""
        import os
        cwd = Path.cwd()
        # Should not raise
        resolved = _resolve_safe_output_path("results.json")
        self.assertTrue(str(resolved).startswith(str(cwd.resolve())))

    def test_path_traversal_is_rejected(self):
        """A path escaping the current directory raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            _resolve_safe_output_path("../../etc/passwd")
        self.assertIn("current working directory", str(ctx.exception))

    def test_absolute_path_outside_cwd_is_rejected(self):
        """An absolute path outside the working directory raises ValueError."""
        with self.assertRaises(ValueError):
            _resolve_safe_output_path("/tmp/stolen_results.json")

    def test_tilde_expansion_outside_cwd_is_rejected(self):
        """A ~ path that resolves outside CWD raises ValueError."""
        home = Path.home().resolve()
        cwd = Path.cwd().resolve()
        # Only run this assertion if home is actually outside cwd
        if not str(home).startswith(str(cwd)):
            with self.assertRaises(ValueError):
                _resolve_safe_output_path("~/results.json")


class QueryLimitTests(unittest.TestCase):
    """Verify that candidate retrieval inputs remain bounded."""

    def test_query_variants_are_capped(self):
        """Ensure query expansion cannot exceed the configured cap."""
        queries = generate_search_queries(
            "small businesses struggling with SOC 2 evidence collection and "
            "manual screenshots for audits"
        )
        self.assertLessEqual(len(queries), constants.MAX_QUERY_VARIANTS)

    def test_allowed_sorts_are_conservative(self):
        """Ensure Reddit search sorts remain limited to conservative modes."""
        self.assertEqual(constants.ALLOWED_SORTS, ["relevance", "new"])


class DependencyHardeningTests(unittest.TestCase):
    """Verify dependency and model supply-chain controls."""

    def test_sentence_transformers_minimum_blocks_known_vulnerable_range(self):
        """Ensure the vulnerable sentence-transformers version range is blocked."""
        requirements = Path("requirements.txt").read_text(encoding="utf-8")
        self.assertIn("sentence-transformers>=3.1.1", requirements)
        self.assertIn("<4.0.0", requirements)

    def test_praw_and_dotenv_are_not_in_requirements(self):
        """praw and python-dotenv must not be declared as dependencies in this branch."""
        import re
        requirements = Path("requirements.txt").read_text(encoding="utf-8")
        # Check that no uncommented lines declare praw or python-dotenv
        active_lines = [l for l in requirements.splitlines() if l.strip() and not l.strip().startswith("#")]
        active_text = "\n".join(active_lines)
        self.assertNotIn("praw", active_text)
        self.assertNotIn("python-dotenv", active_text)

    def test_requests_is_in_requirements(self):
        """requests must be declared in requirements.txt for Arctic Shift."""
        requirements = Path("requirements.txt").read_text(encoding="utf-8")
        self.assertIn("requests>=", requirements)

    def test_semantic_model_revision_is_pinned(self):
        """Ensure the embedding model name and revision remain pinned."""
        self.assertEqual(
            constants.MODEL_NAME,
            "sentence-transformers/all-MiniLM-L6-v2",
        )
        self.assertRegex(constants.MODEL_REVISION, r"^[0-9a-f]{40}$")
        self.assertEqual(
            constants.MODEL_REVISION,
            "c9745ed1d9f207416be6d2e6f8de32d1f16199bf",
        )


class ModularStructureTests(unittest.TestCase):
    """Verify that the implementation keeps the expected modular structure."""

    def test_expected_modules_exist(self):
        """Ensure all expected modular source files remain present."""
        expected = [
            "constants.py",
            "models.py",
            "security.py",
            "query.py",
            "reddit_search.py",
            "scoring.py",
            "output.py",
            "validation.py",
            "cli.py",
            "focus.py",
            "text_utils.py",
            "discovery.py",
        ]

        package_dir = Path("reddit_thread_finder_core")
        for filename in expected:
            self.assertTrue((package_dir / filename).exists(), f"Missing: {filename}")


class ValidationTests(unittest.TestCase):
    """Verify input parsing produces clear errors on bad input."""

    def test_parse_score_rejects_non_numeric(self):
        """parse_score raises ValueError with a helpful message for non-numeric input."""
        with self.assertRaises(ValueError) as ctx:
            parse_score("abc")
        self.assertIn("abc", str(ctx.exception))

    def test_parse_score_rejects_out_of_range(self):
        """parse_score raises ValueError when score is outside 0.0–1.0."""
        with self.assertRaises(ValueError):
            parse_score("1.5")
        with self.assertRaises(ValueError):
            parse_score("-0.1")

    def test_parse_score_accepts_valid_values(self):
        """parse_score accepts valid floats in range."""
        self.assertEqual(parse_score("0.0"), 0.0)
        self.assertEqual(parse_score("1.0"), 1.0)
        self.assertAlmostEqual(parse_score("0.5"), 0.5)

    def test_parse_positive_int_rejects_non_numeric(self):
        """parse_positive_int raises ValueError with a helpful message for non-numeric input."""
        with self.assertRaises(ValueError) as ctx:
            parse_positive_int("xyz", "top_k")
        self.assertIn("xyz", str(ctx.exception))

    def test_parse_positive_int_rejects_zero_and_negative(self):
        """parse_positive_int rejects zero and negative values."""
        with self.assertRaises(ValueError):
            parse_positive_int("0", "top_k")
        with self.assertRaises(ValueError):
            parse_positive_int("-5", "top_k")

    def test_parse_yyyy_mm_dd_rejects_bad_format(self):
        """parse_yyyy_mm_dd raises ValueError with a helpful message for bad date format."""
        with self.assertRaises(ValueError) as ctx:
            parse_yyyy_mm_dd("05/29/2026")
        self.assertIn("YYYY-MM-DD", str(ctx.exception))

    def test_parse_yyyy_mm_dd_rejects_future_date(self):
        """parse_yyyy_mm_dd rejects future dates."""
        with self.assertRaises(ValueError) as ctx:
            parse_yyyy_mm_dd("2099-01-01")
        self.assertIn("future", str(ctx.exception))


class FocusBuilderTests(unittest.TestCase):
    """Verify generic pain-point scope narrowing behavior."""

    def test_split_terms_returns_clean_unique_terms(self):
        """Ensure comma-separated term input is cleaned and deduplicated."""
        self.assertEqual(
            split_terms("SOC2, HIPAA, SOC2,  cloud alerts "),
            ["SOC2", "HIPAA", "cloud alerts"],
        )

    def test_specific_input_scores_higher_than_broad_input(self):
        """Ensure concrete pain inputs score higher than vague product-category inputs."""
        broad_score, _ = analyze_topic_specificity("AI automation software platform")
        specific_score, _ = analyze_topic_specificity(
            "support teams manually tag customer tickets to find recurring product issues"
        )
        self.assertGreater(specific_score, broad_score)

    def test_create_search_brief_is_product_agnostic(self):
        """Ensure the focus builder works without compliance-specific assumptions."""
        brief = create_search_brief(
            raw_topic="returns are killing our ecommerce team",
            target_persona="small ecommerce operators",
            task_or_situation="track returns and refund status",
            current_friction="checking Shopify warehouse emails and spreadsheets manually",
            desired_outcome="know which customers are waiting for refunds",
            must_include_terms=["Shopify", "returns"],
            avoid_terms=["dropshipping"],
        )

        self.assertIn("small ecommerce operators", brief.focused_query)
        self.assertIn("Shopify", brief.focused_query)
        self.assertIn("dropshipping", brief.avoid_terms)
        self.assertGreater(len(brief.alternative_queries), 0)

    def test_focused_query_always_anchors_to_raw_topic(self):
        """
        build_focused_query always includes raw_topic even when structured
        fields are only partially filled.

        Previously, if only task_or_situation was provided, the raw topic was
        silently dropped from the query.
        """
        query = build_focused_query(
            raw_topic="teams can't track customer refunds",
            task_or_situation="track refund status",
        )
        self.assertIn("track customer refunds", query)
        self.assertIn("track refund status", query)

    def test_focused_query_raw_topic_only_when_no_structured_fields(self):
        """When no structured fields are given, focused query equals the raw topic."""
        query = build_focused_query(raw_topic="small teams struggling with SOC2 audits")
        self.assertIn("SOC2", query)
        self.assertIn("small teams", query)

    def test_focused_query_includes_must_include_terms(self):
        """Must-include terms appear in the focused query."""
        query = build_focused_query(
            raw_topic="finding leads on social media",
            must_include_terms=["LinkedIn", "outreach"],
        )
        self.assertIn("LinkedIn", query)
        self.assertIn("outreach", query)


class SecurityModuleTests(unittest.TestCase):
    """Verify Arctic Shift HTTP response validation."""

    def test_validate_response_rejects_non_dict(self):
        """validate_arctic_shift_response rejects non-dict responses."""
        from reddit_thread_finder_core.security import validate_arctic_shift_response
        with self.assertRaises(ValueError) as ctx:
            validate_arctic_shift_response(["not", "a", "dict"], "/test")
        self.assertIn("not a JSON object", str(ctx.exception))

    def test_validate_response_rejects_missing_data_key(self):
        """validate_arctic_shift_response rejects responses without data key."""
        from reddit_thread_finder_core.security import validate_arctic_shift_response
        with self.assertRaises(ValueError) as ctx:
            validate_arctic_shift_response({"error": "something went wrong"}, "/test")
        self.assertIn("missing 'data' field", str(ctx.exception))

    def test_validate_response_rejects_non_list_data(self):
        """validate_arctic_shift_response rejects non-list data field."""
        from reddit_thread_finder_core.security import validate_arctic_shift_response
        with self.assertRaises(ValueError):
            validate_arctic_shift_response({"data": {"not": "a list"}}, "/test")

    def test_validate_response_accepts_valid_response(self):
        """validate_arctic_shift_response accepts a well-formed response."""
        from reddit_thread_finder_core.security import validate_arctic_shift_response
        result = validate_arctic_shift_response({"data": []}, "/test")
        self.assertEqual(result["data"], [])

    def test_validate_post_fields_rejects_missing_required(self):
        """validate_post_fields rejects posts missing required fields."""
        from reddit_thread_finder_core.security import validate_post_fields
        with self.assertRaises(ValueError) as ctx:
            validate_post_fields({"title": "hello"}, "/posts/search")
        self.assertIn("missing required fields", str(ctx.exception))

    def test_validate_post_fields_accepts_valid_post(self):
        """validate_post_fields accepts a post with all required fields."""
        from reddit_thread_finder_core.security import validate_post_fields
        post = {"id": "abc123", "title": "Test post", "subreddit": "test"}
        result = validate_post_fields(post, "/posts/search")
        self.assertEqual(result["id"], "abc123")

    def test_no_credentials_in_security_module(self):
        """Verify the security module has no credential-handling code."""
        import inspect
        from reddit_thread_finder_core import security
        source = inspect.getsource(security)
        # These strings should not appear as functional code (imports/assignments/calls)
        self.assertNotIn("REDDIT_CLIENT_ID", source)
        self.assertNotIn("REDDIT_CLIENT_SECRET", source)
        self.assertNotIn("load_dotenv", source)
        self.assertNotIn("import praw", source)
        self.assertNotIn("praw.Reddit(", source)


class DiscoveryModuleTests(unittest.TestCase):
    """Verify subreddit discovery validation logic."""

    def test_valid_subreddit_names_accepted(self):
        """Valid subreddit names pass the validation pattern."""
        from reddit_thread_finder_core.discovery import _is_valid_subreddit_name
        valid = ["startups", "sysadmin", "ITManagers", "CustomerService_2", "r_place"]
        for name in valid:
            with self.subTest(name=name):
                self.assertTrue(_is_valid_subreddit_name(name))

    def test_invalid_subreddit_names_rejected(self):
        """Invalid subreddit names are rejected to prevent injection."""
        from reddit_thread_finder_core.discovery import _is_valid_subreddit_name
        invalid = [
            "r/startups",          # has slash
            "has spaces",          # has space
            "has-hyphen",          # has hyphen (not allowed in Reddit names)
            "../etc/passwd",       # path traversal attempt
            "a" * 51,              # too long
            "",                    # empty
        ]
        for name in invalid:
            with self.subTest(name=name):
                self.assertFalse(_is_valid_subreddit_name(name))

    def test_parse_manual_subreddit_input_validates_names(self):
        """Manual subreddit input is validated and cleaned."""
        from reddit_thread_finder_core.discovery import _parse_manual_subreddit_input
        result = _parse_manual_subreddit_input("startups, r/sysadmin, bad/name, valid_one", 10)
        self.assertIn("startups", result)
        self.assertIn("sysadmin", result)
        self.assertIn("valid_one", result)
        self.assertNotIn("bad/name", result)


if __name__ == "__main__":
    unittest.main()
