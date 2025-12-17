# AI Models

This directory contains AI model configurations, fine-tuning data, and custom model integrations.

## Structure

- **configs/**: Model configuration files
- **training/**: Training data and scripts
- **weights/**: Model weights and checkpoints (if applicable)
- **embeddings/**: Vector embeddings and indexes

## Supported Models

### Gemini (Default)
- gemini-pro: General purpose text generation
- gemini-pro-vision: Multimodal (text + image)

### OpenAI
- gpt-4: Advanced reasoning and generation
- gpt-4-turbo: Faster, cost-effective GPT-4
- gpt-3.5-turbo: Fast, efficient for simpler tasks

## Model Selection

The default provider is configured in `ctb/ai/ai.config.json`. Models can be selected per-request based on task requirements.

## Fine-tuning

Custom fine-tuned models can be added here with appropriate configuration files.

## Performance Monitoring

Track model performance metrics:
- Response time
- Token usage
- Error rates
- Quality scores
