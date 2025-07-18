# DB-GPT: BabyAGI with Database Integration

## Description
DB-GPT: Extends BabyAGI with LLM-driven database queries, Text-to-SQL, and multi-agent analytics. Python-based for AGI research.

## Features
- **Natural Language Queries**: Query databases using plain English.
- **Text-to-SQL**: Generates accurate SQL from natural language inputs.
- **Multi-Agent System**: Role-based agents (e.g., analyst, engineer) for collaborative tasks.
- **Generative Analytics**: Produces data insights and reports via LLMs.
- **Privacy-Focused**: Supports local LLMs for secure data processing.
- **Task Management**: Inherits BabyAGI’s task creation, prioritization, and execution.

## Installation
1. **Clone the Repository**:
   ```sh
   git clone https://github.com/makalin/babyagi.git
   cd babyagi
   ```

2. **Install Dependencies**:
   Requires Python 3.8+. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. **Set Up Environment**:
   Create a `.env` file with LLM and database credentials:
   ```plaintext
   LLM_MODEL_PATH=/path/to/local/llm
   PINECONE_API_KEY=your-pinecone-key
   DATABASE_URL=your-database-url
   OPENAI_API_KEY=your-openai-api-key
   ```

4. **Run DB-GPT**:
   Start the system:
   ```sh
   python main.py
   ```

## Usage
DB-GPT extends BabyAGI by enabling database interactions and analytics via natural language. Example:

```sh
> python main.py --objective "Analyze Q1 2025 sales data"
[INFO] Generating SQL query...
[INFO] Executing: SELECT SUM(revenue) FROM sales WHERE quarter = 'Q1 2025'
[OUTPUT] Total revenue: $1,234,567
[INFO] Generating report: Q1 sales trends...
```

## Configuration
Customize settings in `config.yaml`:
```yaml
llm:
  model: "local-llm"
  max_tokens: 512
database:
  type: "postgresql"
  url: "your-database-url"
agent:
  roles: ["analyst", "engineer"]
vector_store:
  provider: "pinecone"
  index: "db-gpt-tasks"
```

## Contributing
Contributions are welcome! Fork the repo, create a branch, and submit a pull request. Focus areas:
- Enhance Text-to-SQL accuracy.
- Add support for NoSQL or cloud databases.
- Improve multi-agent workflows.
See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License
MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments
- [BabyAGI](https://github.com/makalin/babyagi) for the foundational framework.
- [DB-GPT](https://github.com/eosphoros-ai/DB-GPT) for database integration inspiration.
- [LangChain](https://github.com/hwchase17/langchain) for agent orchestration.
- [Pinecone](https://www.pinecone.io/) for vector storage.
- [Hugging Face](https://github.com/huggingface/transformers) for LLM support.
  
