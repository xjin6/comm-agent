---
name: skill-sentiment-analysis
description: Run LLM-based sentiment analysis on a dataset (CSV, XLSX, TXT). It reads each row or line, uses a language model to code the sentiment polarity (Positive, Negative, Neutral) and optionally emotion categories, then appends the labels to the dataset. Finally, it generates an aggregated statistical report with charts. Make sure to use this skill whenever the user mentions "sentiment analysis", "emotion coding", "attitude analysis", or wants to label the sentiment of posts, comments, or texts.
---

# LLM-Based Sentiment Analysis

This skill guides the user through conducting rigorous, item-by-item sentiment analysis on text datasets using a large language model (LLM), and produces an aggregated statistical report suitable for research.

## Workflow

When the user triggers this skill, follow these steps strictly:

### 1. Identify the Data and Scope

Ask the user:
1. **Which file** contains the text to analyze? (Usually CSV, XLSX, or TXT in `your-project/.../data/`)
2. **Which column** contains the text? (If it's a tabular file)
3. **What is the coding scheme?** (e.g., Simple 3-way: Positive/Negative/Neutral? Or do they need specific emotion categories like Joy, Anger, Fear, Sadness? If they don't specify, default to a 3-way polarity scale and ask for confirmation).

### 2. Prepare the Python Script

You will write a custom Python script to perform the analysis. 
- *Crucial Note*: Since we are doing item-by-item LLM analysis, passing thousands of rows sequentially in a single conversation prompt is impossible. Instead, write a Python script that uses the Anthropic API (or local processing if they prefer an offline library like `vaderSentiment`/`snownlp`, but the user requested LLM) to iterate through the data.
- However, to keep it simple and free for the user *within this session* without needing them to set up an API key, you can offer two modes:
  - **Mode A (In-session LLM Batching)**: If the dataset is small (< 100 items), you can read the file, process the items in batches within your own Claude context, and write the annotated data to a new file using the `Edit`/`Write` tools.
  - **Mode B (Python Script)**: For larger datasets, write a Python script that uses an open-source NLP library (like `TextBlob` for English or `SnowNLP` for Chinese) to do the heavy lifting locally, OR write a script that calls the Anthropic API (requires the user to provide their `ANTHROPIC_API_KEY`).

*Given the user prefers LLM line-by-line coding, you MUST ask the user:*
> "Since you prefer LLM-based line-by-line coding, the best approach for large datasets is for me to write a Python script that calls the Anthropic API to analyze each row. Do you have an Anthropic API key you can use for this script, or is the dataset small enough (under 100 rows) that I can just read it and code it manually right here in our chat?"

### 3. Execute the Coding

Based on their answer:
- **If they have an API key / large dataset**: Write a Python script `run_sentiment.py` that reads their CSV/XLSX, iterates through the target column, sends a zero-shot or few-shot prompt to the `anthropic` Python library to get the sentiment label, and saves the result to `{original_filename}_sentiment.csv`.
- **If it's a small dataset**: Read the file, code it yourself in a structured format, and write the output back to a new CSV file.

### 4. Generate the Statistical Report

Once the coding is complete and the new dataset is saved, you must generate a statistical report.
Write a second Python script `generate_sentiment_report.py` (or do it in one script) that:
1. Loads the newly annotated dataset.
2. Calculates the frequencies and percentages of each sentiment category.
3. Generates visualizations using `matplotlib` and `seaborn`:
   - A Pie chart or Bar chart showing the overall sentiment distribution.
   - If a `date` or `time` column exists, a Line chart showing sentiment trends over time.
4. Saves the charts as `.png` files in the `output/` directory.
5. Prints a markdown summary report (total analyzed, dominant sentiment, etc.) directly in the chat.

## Coding Prompt Guidelines (For the LLM)

When setting up the LLM prompt for coding, ensure it enforces a strict output format (e.g., asking the LLM to output *only* "Positive", "Negative", or "Neutral" without conversational filler) so the data can be parsed easily into a dataframe.

### Statistical KPIs to Report
- **Sentiment Distribution (Pie/Bar Chart)**: The proportion of each sentiment category.
- **Sentiment Over Time (Line Chart)**: If a date/time column is provided, show how the sentiment distribution evolves (e.g., daily sentiment volume).
- **Sentiment Polarity Index**: A calculated score (e.g., `(Positive - Negative) / Total`) indicating the overall sentiment leaning.
- **Top Emotional/Sentiment Extremes**: Optional extraction of the top 3 most "extreme" or confident predictions if probabilities/confidence scores are available.
