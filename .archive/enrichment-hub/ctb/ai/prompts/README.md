# AI Prompts

This directory contains prompt templates for AI operations.

## Prompt Structure

Each prompt should include:
- **Purpose**: What the prompt is designed to do
- **Input Variables**: Required and optional inputs
- **Output Format**: Expected response structure
- **Provider**: Which AI provider(s) it's optimized for

## Providers

- **Gemini**: Google's Gemini Pro models (default)
- **OpenAI**: GPT-4 and GPT-3.5 models

## Usage

Prompts can be loaded dynamically by the AI service layer and populated with context-specific variables.

## Best Practices

1. Use clear, specific instructions
2. Define expected output format
3. Include examples when possible
4. Version control prompt changes
5. Test with multiple providers
