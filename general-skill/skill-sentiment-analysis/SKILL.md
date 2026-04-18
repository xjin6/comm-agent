---
name: skill-sentiment-analysis
description: Run LLM-based sentiment analysis on a dataset (CSV, XLSX, TXT). It reads each row or line, uses a language model to code the sentiment polarity (Positive, Negative, Neutral) and optionally emotion categories, then appends the labels to the dataset. Finally, it generates an aggregated statistical report with charts. Make sure to use this skill whenever the user mentions "sentiment analysis", "emotion coding", "attitude analysis", or wants to label the sentiment of posts, comments, or texts.
---

# LLM-Based Sentiment Analysis

This skill guides the user through conducting rigorous, item-by-item sentiment analysis on text datasets using a large language model (LLM), and produces an aggregated statistical report suitable for research.

## 

When the user triggers this skill, follow these steps strictly:

### 1. Identify the Data and Scope

Ask the user:
1. **Which file** contains the text to analyze? (Usually CSV, XLSX, or TXT in `your-project/.../data/`)
2. **Which column** contains the text? (If it's a tabular file)
3. **What is the rigorous coding scheme?** 
   - DO NOT default to a simple 3-way (Positive/Negative/Neutral) scale unless the user explicitly requests a basic overview.
   - Ask the user to clarify their theoretical framework or specific coding scheme.
   - **CRITICAL REQUIREMENT**: If the user does not have a codebook or coding scheme, you MUST proactively draft a professional, academic Codebook for them based on Ekman's Basic Emotions (Anger, Disgust, Fear, Happiness, Sadness, Surprise) or another relevant communication/psychology theory. Present the draft codebook (with definitions and examples) to the user and ask for their confirmation or modification before proceeding to write any scripts.

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
   - **CRITICAL**: If a `date` or `time` column exists, it MUST generate a Line chart showing sentiment trends over time.
4. Saves the charts as `.png` files in the `output/` directory.
5. Prints a markdown summary report (total analyzed, dominant sentiment, etc.) directly in the chat.
6. **Execution**: If the user tells you to run the script, or if the dataset is small enough, you MUST actually run `generate_sentiment_report.py` via your Bash tool so that the PNG files are physically created. Do not just output the code and stop.

## Coding Prompt Guidelines (For the LLM)

When setting up the LLM prompt for coding, ensure it enforces a strict output format (e.g., asking the LLM to output *only* "Positive", "Negative", or "Neutral" without conversational filler) so the data can be parsed easily into a dataframe.

### Statistical KPIs to Report
- **Sentiment Distribution (Pie/Bar Chart)**: The proportion of each sentiment category.
- **Sentiment Over Time (Line Chart)**: If a date/time column is provided, show how the sentiment distribution evolves (e.g., daily sentiment volume).
- **Sentiment Polarity Index**: A calculated score (e.g., `(Positive - Negative) / Total`) indicating the overall sentiment leaning.
- **Top Emotional/Sentiment Extremes**: Optional extraction of the top 3 most "extreme" or confident predictions if probabilities/confidence scores are available.
