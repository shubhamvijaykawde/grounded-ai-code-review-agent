import streamlit as st
import json
from urllib.parse import urlparse
from app.pipeline import run_code_review


st.set_page_config(
    page_title="CodeRoast",
    page_icon="🔥",
    layout="wide",
)


# =========================================================
# Header
# =========================================================

st.title("🔥 CodeRoast")

st.markdown(
    """
**Grounded AI Code Review**

Static analysis finds the problems.  
AST parsing identifies the exact code.  
The LLM explains and roasts the evidence.
"""
)
st.caption(
    "🐍 Currently supports **Python repositories only**. "
    "Other languages will run, but will return no findings."
)


# =========================================================
# Helpers
# =========================================================

def is_github_url(url: str) -> bool:
    try:
        parsed = urlparse(url.strip())

        return (
            parsed.scheme in {"http", "https"}
            and parsed.netloc.lower() == "github.com"
        )
    except Exception:
        return False


# =========================================================
# Sidebar
# =========================================================

st.sidebar.header("Review Settings")

persona = st.sidebar.selectbox(
    "Reviewer Persona",
    options=[
        "sarcastic",
        "brutally_honest",
        "overly_enthusiastic",
    ],
    format_func=lambda value: {
        "sarcastic": "😏 Sarcastic",
        "brutally_honest": "🧑‍💻 Brutally Honest",
        "overly_enthusiastic": "🤩 Overly Enthusiastic",
    }[value],
)

st.sidebar.caption(
    "LLM: Groq • openai/gpt-oss-120b"
)


max_findings = st.sidebar.slider(
    "Number of AI Reviews",
    min_value=1,
    max_value=10,
    value=5,
    step=1,
    help="More reviews require more LLM calls.",
)


# =========================================================
# Repository input
# =========================================================

st.subheader("Analyze a GitHub Repository")

github_url = st.text_input(
    "GitHub Repository URL",
    placeholder="https://github.com/pallets/flask",
)


analyze_clicked = st.button(
    "🔥 Roast My Code",
    type="primary",
    use_container_width=True,
)


# =========================================================
# Run pipeline
# =========================================================

if analyze_clicked:

    if not github_url.strip():
        st.error(
            "Please enter a GitHub repository URL."
        )
        st.stop()

    if not is_github_url(github_url):
        st.error(
            "Please enter a valid GitHub repository URL, "
            "for example https://github.com/psf/requests"
        )
        st.stop()

    try:

        with st.spinner(
            "Cloning repository, running analysis, mapping AST "
            "chunks, and generating grounded critiques..."
        ):

            result = run_code_review(
                repo_url=github_url,
                persona=persona,
                max_findings=max_findings,
                save_results=True,
            )

        st.session_state["review_result"] = result

        st.success(
            "Repository review completed."
        )

    except Exception as exc:

        st.error(
            "CodeRoast could not complete the review."
        )

        st.exception(exc)

        st.stop()


# =========================================================
# Display result
# =========================================================
with st.expander("ℹ️ How CodeRoast works", expanded=False):

    st.markdown("**Pipeline**")

    st.code(
        "GitHub URL\n"
        "    ↓\n"
        "Safe repository ingestion\n"
        "    ↓\n"
        "Ruff + Bandit + Radon\n"
        "    ↓\n"
        "Python AST parsing\n"
        "    ↓\n"
        "Exact Finding → Code mapping\n"
        "    ↓\n"
        "Grounded LLM critique\n"
        "    ↓\n"
        "Roasted review",
        language="text",
    )


result = st.session_state.get(
    "review_result"
)


if result is None:
    st.info("Enter a GitHub repository and click **Roast My Code** to begin.")

    st.stop()


# =========================================================
# Repository information
# =========================================================

repository = result["repository"]
summary = result["summary"]
reviews = result["reviewed_findings"]

st.header(
    repository.get(
        "full_name"
    )
    or repository.get(
        "name"
    )
)

if repository.get("description"):
    st.caption(
        repository["description"]
    )


# =========================================================
# Overview metrics
# =========================================================

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Production Findings",
    summary.get(
        "production_findings",
        0,
    ),
)

col2.metric(
    "Raw Findings",
    summary.get(
        "raw_findings",
        0,
    ),
)

col3.metric(
    "AI Reviews",
    len(reviews),
)

col4.metric(
    "Code Health",
    f"{summary.get('score', 'N/A')}/100",
)

st.caption(
    "Code Health is a CodeRoast heuristic based on the severity "
    "of static-analysis findings; it is not a universal code-quality standard."
)

st.divider()

report_json = json.dumps(
    result,
    indent=2,
    ensure_ascii=False,
    default=str,
)

st.download_button(
    label="⬇️ Download Review Report",
    data=report_json,
    file_name="code_roast_report.json",
    mime="application/json",
)


# =========================================================
# Analysis summary
# =========================================================

st.subheader("Analysis Summary")

summary_col1, summary_col2 = st.columns(2)

with summary_col1:

    st.markdown("### Severity")

    severity_counts = summary.get(
        "severity_counts",
        {},
    )

    if severity_counts:

        for severity, count in sorted(
            severity_counts.items()
        ):

            st.write(
                f"**{severity.title()}**: {count}"
            )

    else:

        st.write(
            "No production findings."
        )

with summary_col2:

    st.markdown("### Tools")

    tool_counts = summary.get(
        "tool_counts",
        {},
    )

    for tool, count in sorted(
        tool_counts.items()
    ):

        st.write(
            f"**{tool.upper()}**: {count}"
        )

st.divider()


# =========================================================
# AI reviews
# =========================================================

st.header("🔥 CodeRoasts")

if not reviews:
    st.success(
        "🎉 No production findings were selected for AI review."
    )
    st.info(
        "The static-analysis tools did not produce any reviewable "
        "production findings for this repository."
    )

for index, item in enumerate(
    reviews,
    start=1,
):

    finding = item["finding"]
    chunk = item["target_chunk"]
    critique = item["critique"]

    title = (
        f"Roast #{index} — "
        f"{finding.get('tool', '').upper()} "
        f"{finding.get('rule_id') or ''}"
    )

    with st.expander(
        title,
        expanded=index == 1,
    ):

        # -------------------------------------------------
        # Evidence
        # -------------------------------------------------

        evidence_col, code_col = st.columns(
            [1, 2]
        )

        with evidence_col:

            st.markdown("### Finding")

            st.write(
                finding.get(
                    "message",
                    "",
                )
            )

            st.caption(
                f"{finding.get('file')}:{finding.get('line')}"
            )

            st.write(
                f"**Tool:** {finding.get('tool')}"
            )

            st.write(
                f"**Severity:** {finding.get('severity')}"
            )

            if finding.get("rule_id"):

                st.write(
                    f"**Rule:** {finding.get('rule_id')}"
                )

            if finding.get("metric_name"):

                st.write(
                    f"**Metric:** "
                    f"{finding.get('metric_name')} = "
                    f"{finding.get('metric_value')}"
                )

        with code_col:

            st.markdown(
                f"### `{chunk.get('qualified_name')}`"
            )

            st.caption(
                f"{chunk.get('file')}:"
                f"{chunk.get('start_line')}-"
                f"{chunk.get('end_line')}"
            )

            st.code(
                chunk.get(
                    "content",
                    "",
                ),
                language="python",
            )

        st.divider()

        # -------------------------------------------------
        # AI critique
        # -------------------------------------------------

        st.markdown("### Verdict")

        st.write(
            critique.get(
                "verdict",
                "",
            )
        )

        st.markdown("### 🔥 Roast")

        st.write(
            critique.get(
                "roast",
                "",
            )
        )

        st.markdown("### Why it matters")

        st.write(
            critique.get(
                "explanation",
                "",
            )
        )

        st.markdown("### Suggested improvement")

        st.write(
            critique.get(
                "suggestion",
                "",
            )
        )

        st.markdown("### Backhanded compliment")

        st.write(
            critique.get(
                "compliment",
                "",
            )
        )

        # -------------------------------------------------
        # Grounding
        # -------------------------------------------------

        grounding = critique.get(
            "grounding_status",
            "unknown",
        )

        if grounding == "reference_validated":

            st.success(
                "✓ Evidence references validated"
            )

        else:

            st.warning(
                f"Grounding status: {grounding}"
            )