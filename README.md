# 🔥 CodeRoast

### Grounded AI Code Review Agent

CodeRoast is an AI-assisted code review system that combines **deterministic static analysis, Python AST parsing, retrieval, and LLM-generated critiques**.

Instead of asking an LLM to independently decide whether code is "bad", CodeRoast first collects concrete findings from static-analysis tools, maps each finding to the relevant source-code structure, and then asks the LLM to explain and roast that verified evidence.

> **Static analysis finds the problem. AST parsing finds the code. The LLM explains it.**

---

## ✨ Features

* 🔍 **Static analysis** with Ruff, Bandit, and Radon
* 🌳 **Python AST parsing** for deterministic code-structure extraction
* 📌 **Finding → exact code mapping** using file and line information
* 🧠 **Dense and hybrid retrieval** for additional semantic context
* 🤖 **Grounded LLM critiques** using Groq
* 🎭 Three reviewer personas:

  * 😏 Sarcastic
  * 🧑‍💻 Brutally Honest
  * 🤩 Overly Enthusiastic
* 📊 **Code Health score** based on static-analysis severity
* 🔥 Repository-level CodeRoast reports
* 🖥️ Interactive **Streamlit UI**
* 📄 Downloadable JSON review reports
* 🛡️ Target repositories are analyzed as source code and are **never executed**
* 🐍 Current MVP supports **Python repositories**

---

## 🏗️ Architecture

```text
                     GitHub Repository URL
                              │
                              ▼
                    ┌─────────────────────┐
                    │   Safe Ingestion    │
                    │ shallow clone       │
                    │ size/file limits    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Static Analysis   │
                    │                     │
                    │ Ruff  Bandit  Radon│
                    └──────────┬──────────┘
                               │
                               ▼
                         Findings
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Python AST       │
                    │      Parsing        │
                    └──────────┬──────────┘
                               │
                               ▼
                  Exact Finding → CodeChunk
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
             Exact evidence        Retrieval context
                    │                     │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │    Grounded LLM     │
                    │      Critic         │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┼─────────────┐
                 ▼             ▼             ▼
             Sarcastic      Honest      Enthusiastic
                 │
                 ▼
                    Structured Review
                 │
                 ▼
              Streamlit UI
```

---

## 🎯 Grounding Design

The most important design principle in CodeRoast is **grounded generation**.

The LLM is not responsible for discovering what is wrong.

Instead:

```text
Static Analyzer
      ↓
Verified Finding
      ↓
AST Mapping
      ↓
Exact Source Code
      ↓
LLM Explanation
```

Each critique receives:

* the original static-analysis finding
* the exact file and line information
* the matched Python AST chunk
* the relevant source-code content
* optional retrieved context

The generated response must return evidence references pointing back to the supplied evidence.

This reduces the risk of an LLM inventing unrelated code problems.

---

## 🔍 Static Analysis

CodeRoast currently combines three analysis tools.

### Ruff

Used for Python linting and code-quality findings such as:

* unused imports
* exception handling
* simplification opportunities
* code-style issues

### Bandit

Used for security-oriented findings such as:

* dangerous function usage
* weak cryptographic algorithms
* shell execution
* unsafe patterns

### Radon

Used for maintainability and complexity analysis, including:

* cyclomatic complexity
* maintainability-related metrics

The raw findings are preserved before the review layer filters them for the user-facing review.

---

## 🌳 AST-Based Code Mapping

Static-analysis tools provide file and line information, but line-level information alone is not always enough for an LLM.

CodeRoast therefore parses Python source files using the standard Python `ast` module.

It extracts structures such as:

* modules
* module sections
* classes
* functions
* methods
* nested functions
* nested classes

Each chunk receives a deterministic identifier such as:

```text
src/example.py::MyClass.my_method::42
```

A finding is then mapped to the smallest relevant AST structure containing the finding location.

This allows CodeRoast to provide the LLM with the actual function or method surrounding the reported issue.

---

## 🧠 Retrieval

CodeRoast includes a retrieval layer using:

* SentenceTransformer embeddings
* FAISS
* TF-IDF lexical retrieval
* Reciprocal Rank Fusion

The retrieval system is used as **supporting semantic context**.

It is intentionally not the primary mechanism for locating the offending code.

The deterministic AST mapping remains the source of truth for the finding being reviewed.

Retrieval experiments and benchmark scripts are included under `examples/`.

---

## 🤖 LLM Critic

The current application uses a configurable Groq client.

The LLM receives structured evidence and produces:

```text
Verdict
Explanation
Roast
Suggested improvement
Backhanded compliment
Evidence references
```

The output is returned as structured JSON and checked for valid evidence references.

Example:

```json
{
  "verdict": "The method catches the broad Exception class.",
  "explanation": "The static-analysis finding flags the broad exception handler...",
  "roast": "Catching everything? That's one way to avoid choosing.",
  "suggestion": "Catch specific exception types where appropriate.",
  "compliment": "The method has a clear docstring.",
  "evidence_refs": [
    "finding",
    "target_chunk"
  ]
}
```

---

## 🎭 Reviewer Personas

The same technical evidence can be presented using different reviewer personalities.

### 😏 Sarcastic

Witty, dry, and playful.

### 🧑‍💻 Brutally Honest

Direct, concise, and technically focused.

### 🤩 Overly Enthusiastic

Positive, energetic, and excited about improvements.

The persona changes the communication style without changing the underlying evidence.

---

## 📊 Code Health

CodeRoast provides a **Code Health score** based on the severity distribution of static-analysis findings.

The score is intentionally a heuristic for this application.

It should not be interpreted as a universal software-quality metric.

For example:

```text
Code Health: 86/100
Grade: B
```

The UI also shows:

* production findings
* raw findings
* AI-reviewed findings
* findings by severity
* findings by analysis tool

---

## 🖥️ Streamlit Application

The application provides a simple workflow:

```text
1. Enter a GitHub repository URL
2. Select a reviewer persona
3. Select the number of AI reviews
4. Click "Roast My Code"
5. Review the findings and AI critiques
6. Download the JSON report
```

The interface displays:

* repository metadata
* analysis statistics
* severity distribution
* tools used
* exact source code
* AI verdicts
* roasts
* explanations
* suggested improvements
* grounding status

---

## 🔐 Security Considerations

CodeRoast treats external GitHub repositories as **untrusted input**.

The current ingestion layer uses a shallow clone and applies repository limits before analysis.

The application does **not execute the target repository's code**.

This is important because a code-review system should inspect source code rather than run arbitrary repository code.

API credentials are loaded through environment variables and should never be committed to Git.

---

## 🐍 Current Limitations

The current MVP has several deliberate limitations:

* Python repositories only
* Static analysis is currently Python-focused
* AST mapping is Python-specific
* AI review quality depends on the selected LLM
* Static-analysis findings can contain false positives
* The Code Health score is heuristic
* Large repositories can take longer to analyze
* AI reviews are intentionally limited to a small number of high-priority findings
* The LLM explains verified findings; it is not intended to independently discover arbitrary bugs

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/grounded-ai-code-review-agent.git
cd grounded-ai-code-review-agent
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the LLM

Copy the example environment file:

```text
.env.example
```

to:

```text
.env
```

Then configure:

```text
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

Never commit `.env`.

---

## ▶️ Running CodeRoast

Start the Streamlit application:

```bash
streamlit run streamlit_app.py
```

Then open the local Streamlit URL shown in the terminal.

Enter a public GitHub repository URL such as:

```text
https://github.com/psf/requests
```

and click:

```text
🔥 Roast My Code
```

---

## 🧪 Testing

Run the automated tests:

```bash
pytest -q
```

Compile-check the application:

```bash
python -m compileall app
```

The repository also includes development and benchmark scripts under:

```text
examples/
```

including ingestion, AST mapping, retrieval, and agent tests.

---

## 📁 Project Structure

```text
code-roaster/
│
├── app/
│   ├── agent/
│   │   ├── adapters.py
│   │   ├── critic.py
│   │   ├── groq_client.py
│   │   ├── models.py
│   │   ├── ollama_client.py
│   │   ├── prompts.py
│   │   ├── reviewer.py
│   │   └── scoring.py
│   │
│   ├── analysis/
│   │   ├── aggregator.py
│   │   ├── bandit.py
│   │   ├── dedup.py
│   │   ├── models.py
│   │   ├── radon.py
│   │   ├── review.py
│   │   ├── ruff.py
│   │   ├── scope.py
│   │   └── ...
│   │
│   ├── ingestion/
│   │   ├── github.py
│   │   ├── github_api.py
│   │   └── models.py
│   │
│   ├── parsing/
│   │   ├── matcher.py
│   │   ├── models.py
│   │   ├── python_ast.py
│   │   └── scope.py
│   │
│   ├── retrieval/
│   │   ├── embeddings.py
│   │   ├── evaluation.py
│   │   ├── faiss_store.py
│   │   ├── hybrid.py
│   │   ├── lexical.py
│   │   └── ...
│   │
│   └── pipeline.py
│
├── examples/
│   ├── build_index.py
│   ├── build_retrieval_benchmark.py
│   ├── run_agent_smoke_test.py
│   ├── run_analysis.py
│   ├── run_ast.py
│   ├── run_hybrid_benchmark.py
│   ├── run_retrieval_benchmark.py
│   └── ...
│
├── tests/
│   ├── test_analysis.py
│   ├── test_ast.py
│   ├── test_github.py
│   ├── test_retrieval.py
│   └── test_retrieval_evaluation.py
│
├── streamlit_app.py
├── requirements.txt
├── pytest.ini
├── .gitignore
└── .env.example
```

---

## 💡 Design Philosophy

CodeRoast is intentionally designed around a simple separation of responsibilities:

```text
Static analysis
    = What was detected?

AST
    = Where exactly is it?

Retrieval
    = What related code may provide useful context?

LLM
    = How should we explain it?

Streamlit
    = How should we present it?
```

This makes the system easier to reason about than an agent that asks an LLM to independently inspect a repository and invent its own findings.

---

## 📌 Future Work

Potential extensions include:

* support for additional programming languages
* richer AST and dependency relationships
* stronger claim-level grounding validation
* improved retrieval/reranking
* pull-request review workflows
* inline GitHub comments
* repository history-aware analysis
* additional code-quality tools

---

## 👨‍💻 Author

**Shubham Vijay Kawde**

M.Sc. Data Science student focused on applied machine learning, AI systems, and data-driven applications.
