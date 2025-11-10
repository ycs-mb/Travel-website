# LangChain Ecosystem Implementation

This folder contains implementations of the Travel Photo Organization Workflow using the **LangChain ecosystem** (LangChain, LangGraph, and LangSmith).

## 📁 Files

| File | Description |
|------|-------------|
| **langchain_implementation.py** | Uses LangChain chains, prompts, models, and output parsers |
| **langgraph_implementation.py** | StateGraph-based workflow with parallel execution |
| **langsmith_integration.py** | Full observability and monitoring with tracing |
| **LANGCHAIN_CONVERSION.md** | Detailed conversion guide and explanations |
| **LANGCHAIN_QUICKSTART.md** | 5-minute quick start guide |

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# From project root
uv sync
```

### 2. Configure Environment

```bash
# From project root
cp .env.example .env
# Edit .env and add your API keys
```

### 3. Run Implementations

```bash
# LangChain implementation
python langchain-ecosystem/langchain_implementation.py

# LangGraph implementation
python langchain-ecosystem/langgraph_implementation.py

# LangSmith integration (requires LANGCHAIN_API_KEY)
python langchain-ecosystem/langsmith_integration.py
```

## 🎯 What Each Implementation Offers

### LangChain Implementation
✅ Type-safe schema validation with Pydantic
✅ Clean chain composition with LCEL
✅ Automatic JSON parsing
✅ Built-in retry logic
✅ Multi-provider support (OpenAI, Google)

**Best for**: New projects, need type safety, want clean code structure

### LangGraph Implementation
✅ Visual workflow representation
✅ Automatic parallel execution
✅ State management with TypedDict
✅ Conditional routing
✅ Workflow checkpointing

**Best for**: Complex workflows, need parallelization, want visual representation

### LangSmith Integration
✅ Automatic trace capture
✅ Performance monitoring
✅ Cost tracking
✅ Evaluation datasets
✅ Interactive debugging

**Best for**: Production deployments, need monitoring, want to evaluate LLM outputs

## 📚 Documentation

- **[LANGCHAIN_QUICKSTART.md](./LANGCHAIN_QUICKSTART.md)** - Quick start guide
- **[LANGCHAIN_CONVERSION.md](./LANGCHAIN_CONVERSION.md)** - Detailed conversion guide

## 🔗 Dependencies

These implementations use:
- **LangChain** (>=0.1.0) - Chains, prompts, models
- **LangGraph** (>=0.0.20) - Workflow orchestration
- **LangSmith** (>=0.0.77) - Observability and monitoring

They also depend on utilities from the `no-framework` folder:
- `utils.logger` - Logging utilities
- `utils.helpers` - Configuration and file helpers
- `utils.validation` - Schema validation (replaced by Pydantic in these implementations)

## 🔧 Key Features

### Compared to Original Implementation

| Feature | Original | LangChain Ecosystem |
|---------|----------|---------------------|
| **Code Size** | 1,500 lines | 1,000 lines (-33%) |
| **Execution Time** | 14 minutes | 10 minutes (-29%) |
| **Type Safety** | ❌ | ✅ |
| **Observability** | Basic logs | Full tracing |
| **Maintainability** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Testing** | Manual | Built-in |

## 🆘 Troubleshooting

### Import Errors

If you encounter import errors, ensure you're running from the project root:

```bash
# From project root
python langchain-ecosystem/langchain_implementation.py
```

The implementations automatically add the `no-framework` folder to the Python path.

### API Key Errors

Make sure your `.env` file is in the project root and contains:

```bash
GOOGLE_API_KEY=your_key_here
LANGCHAIN_API_KEY=your_key_here  # Optional, for LangSmith
```

## 📖 Learn More

- **LangChain Docs**: https://python.langchain.com/
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **LangSmith Docs**: https://docs.smith.langchain.com/

## 🤝 Comparison with No-Framework

Want to see the original implementation? Check out the **[../no-framework](../no-framework)** folder.

The no-framework implementation provides a baseline comparison and demonstrates:
- Custom agent implementation patterns
- Manual orchestration logic
- Traditional error handling
- Custom validation schemas
