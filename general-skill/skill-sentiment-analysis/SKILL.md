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
1. **Which file** contains the text to analyze? (Usually CSV, XLSX, or TXT in `your-project/project-{name}/data/`)
2. **Which column** contains the text? (If it's a tabular file)
3. **What is the rigorous coding scheme?** 
   - DO NOT default to a simple 3-way (Positive/Negative/Neutral) scale unless the user explicitly requests a basic overview.
   - Ask the user to clarify their theoretical framework or specific coding scheme.
   - **CRITICAL REQUIREMENT**: If the user does not have a codebook or coding scheme, you MUST proactively draft a professional, academic Codebook for them based on Ekman's Basic Emotions (Anger, Disgust, Fear, Happiness, Sadness, Surprise) or another relevant communication/psychology theory. Present the draft codebook (with definitions and examples) to the user and ask for their confirmation or modification before proceeding to write any scripts.

### 2. Prepare the Processing Strategy

- *Crucial Note*: The user DOES NOT want to use an external API key. You MUST process the data entirely within this session, regardless of the dataset size.
- **For Large Datasets (> 500 rows)**: Since a single LLM response has an output token limit and will time out if you try to process thousands of rows at once, you MUST adopt a **Chunking and Appending Strategy**:
  1. Write a Python script (`extract_chunk.py`) or use the `Read`/`Bash` tools to extract the data in chunks of 50-100 rows.
  2. Analyze the current chunk in-session (using your own LLM capabilities).
  3. Write/append the annotated chunk directly to the final output CSV file using the `Bash` or `Edit` tools.
  4. Repeat this loop until the entire dataset is processed. Use the `TaskStop` / `/loop` or recursive tool calls to keep iterating without waiting for the user to prompt you for every chunk.
  
- Do NOT ask the user for an Anthropic API Key. Take full responsibility for processing the dataset line-by-line within the chat context, managing the batching process yourself.

### 3. Execute the Coding

- **Execute the batching loop**: Read a chunk, code it according to the agreed-upon codebook, append the results to `{original_filename}_sentiment.csv`, and move to the next chunk. Ensure the output format is strict (e.g., CSV rows) so it can be cleanly appended.

### 4. Generate the Statistical Report

Once the coding is complete and the new dataset is saved, you must generate a statistical report.
Write a second Python script `generate_sentiment_report.py` (or do it in one script) that:
1. Loads the newly annotated dataset.
2. Calculates the frequencies and percentages of each sentiment category.
3. Generates visualizations using `matplotlib` and `seaborn`:
   - A Pie chart or Bar chart showing the overall sentiment distribution.
   - **CRITICAL**: If a `date` or `time` column exists, it MUST generate a Line chart showing sentiment trends over time.
4. Saves the charts as `.png` files in `your-project/project-{name}/output/sentiment-analysis/`.
5. Prints a markdown summary report (total analyzed, dominant sentiment, etc.) directly in the chat.
6. **Execution**: If the user tells you to run the script, or if the dataset is small enough, you MUST actually run `generate_sentiment_report.py` via your Bash tool so that the PNG files are physically created. Do not just output the code and stop.

## Coding Prompt Guidelines (For the LLM)

When setting up the LLM prompt for coding, ensure it enforces a strict output format (e.g., asking the LLM to output *only* "Positive", "Negative", or "Neutral" without conversational filler) so the data can be parsed easily into a dataframe.

### Statistical KPIs to Report
- **Sentiment Distribution (Pie/Bar Chart)**: The proportion of each sentiment category.
- **Sentiment Over Time (Line Chart)**: If a date/time column is provided, show how the sentiment distribution evolves (e.g., daily sentiment volume).
- **Sentiment Polarity Index**: A calculated score (e.g., `(Positive - Negative) / Total`) indicating the overall sentiment leaning.
- **Top Emotional/Sentiment Extremes**: Optional extraction of the top 3 most "extreme" or confident predictions if probabilities/confidence scores are available.
