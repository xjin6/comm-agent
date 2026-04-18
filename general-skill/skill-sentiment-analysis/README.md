# LLM-Based Sentiment & Emotion Analysis

> **v0.1.0** · Updated 2026-04-18 · `analysis`

A rigorous sentiment and emotion analysis skill designed for communication studies. This skill utilizes Large Language Models (LLMs) to read and annotate text data (CSV, XLSX, TXT) line-by-line, moving beyond basic sentiment classification to support academic theoretical frameworks.

## Overview

Traditional lexicon-based tools (like `SnowNLP` or `TextBlob`) often fail to capture sarcasm, context, and complex emotional nuance. This skill uses the power of LLMs via the Anthropic API (or directly in-session for small datasets) to act as a highly accurate, automated human coder. It then takes the annotated results and generates publication-ready visualizations and statistical summaries.

### Key Features

1. **Academic Coding Schemes**: Refuses to default to a basic positive/negative/neutral split unless asked. Proactively prompts users to adopt rigorous frameworks like:
   - *Ekman's Basic Emotions* (Anger, Disgust, Fear, Happiness, Sadness, Surprise)
   - *Plutchik's Wheel of Emotions*
   - *Moral Foundation Theory (MFT)*
   - *Stance Analysis* (Support vs. Oppose)
2. **Automated Codebook Drafting**: If you don't have a pre-existing codebook, the skill will draft a professional academic codebook (complete with operational definitions and examples) for your approval before coding begins.
3. **Automated Python Workflows**: Writes, customizes, and executes Python scripts (`run_sentiment.py` and `generate_sentiment_report.py`) to process thousands of rows via API.
4. **Data Visualization**: Generates analytical outputs, including:
   - Sentiment Distribution Pie/Bar Charts
   - Sentiment Trend Line Charts over time (if a timestamp column exists)
   - Sentiment Polarity Index calculations

## Setup

For datasets over 100 rows, this skill will generate a Python script that requires an Anthropic API Key to process the text in batches.

Ensure you have your key exported in your environment before running the generated scripts:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Usage

Simply point the agent to your data and state your goal:

> *"I have a large file 'tweets.csv' in my project data folder. Please do an emotion analysis on the 'TweetText' column based on Ekman's six basic emotions."*

The skill will handle drafting the codebook, generating the annotation scripts, and plotting the final trend graphs.
