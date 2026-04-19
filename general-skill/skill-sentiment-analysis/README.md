# LLM-Based Sentiment & Emotion Analysis

> **v0.1.0** · Updated 2026-04-18 · `analysis`

A rigorous sentiment and emotion analysis skill designed for communication studies. This skill utilizes Large Language Models (LLMs) to read and annotate text data (CSV, XLSX, TXT) line-by-line, moving beyond basic sentiment classification to support academic theoretical frameworks.

## Overview

Traditional lexicon-based tools (like `SnowNLP` or `TextBlob`) often fail to capture sarcasm, context, and complex emotional nuance. This skill uses the power of LLMs directly in-session to act as a highly accurate, automated human coder. It then takes the annotated results and generates publication-ready visualizations and statistical summaries.

### Key Features

1. **Academic Coding Schemes**: Refuses to default to a basic positive/negative/neutral split unless asked. Proactively prompts users to adopt rigorous frameworks like:
   - *Ekman's Basic Emotions* (Anger, Disgust, Fear, Happiness, Sadness, Surprise)
   - *Plutchik's Wheel of Emotions*
   - *Moral Foundation Theory (MFT)*
   - *Stance Analysis* (Support vs. Oppose)
2. **Automated Codebook Drafting**: If you don't have a pre-existing codebook, the skill will draft a professional academic codebook (complete with operational definitions and examples) for your approval before coding begins.
3. **In-Session Chunked Processing**: No API keys required. The agent reads and processes large datasets (thousands of rows) in chunks directly within the chat session, automatically appending annotated data to the final CSV output.
4. **Data Visualization**: Generates analytical outputs using Python (`pandas`/`matplotlib`), including:
   - Sentiment Distribution Pie/Bar Charts
   - Sentiment Trend Line Charts over time (if a timestamp column exists)
   - Sentiment Polarity Index calculations

## Setup

No setup or external API keys are required. The skill relies entirely on the underlying LLM's context window and local file reading/writing tools.

Ensure that Python along with `pandas`, `matplotlib`, and `seaborn` are installed on your system if you want to generate visualization charts.

## Usage

Simply point the agent to your data and state your goal:

> *"I have a large file 'tweets.csv' in my project data folder. Please do an emotion analysis on the 'TweetText' column based on Ekman's six basic emotions."*

The skill will handle drafting the codebook, extracting and chunking the data for coding, and plotting the final trend graphs.

## Author

**Yundi Zhang** (@Zhang-Yundi) · yd.yundi@gmail.com

## License

CC BY-NC-ND 4.0
