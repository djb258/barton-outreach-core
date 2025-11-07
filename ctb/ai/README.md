# AI Configuration - Barton Outreach Core

## Purpose

AI model configuration and prompt management, per IMO Creator global config.

## Configuration

From `global-config.yaml`:
- **Providers**: Gemini, OpenAI, Anthropic
- **Prompts Directory**: `ctb/ai/prompts/`
- **Models Directory**: `ctb/ai/models/`
- **Default Provider**: Anthropic (Claude)

## Enrichment Agents

Configured enrichment agents:
- **Apify** - LinkedIn scraping, profile enrichment
- **Abacus** - Data validation, enrichment
- **Firecrawl** - Web scraping, company data

### Agent Performance Monitoring

- **Tracking Table**: `marketing.data_enrichment_log`
- **Metrics**: Success rate, duration, cost per success
- **Timeout**: 10 minutes per job
- **Retry**: Failed jobs are automatically retried

## Status

- **Providers Configured**: Anthropic, OpenAI, Gemini ✅
- **Default Provider**: Anthropic ✅
- **Enrichment Agents**: Apify, Abacus, Firecrawl ✅
- **Performance Monitoring**: Enabled ✅
- **Prompts Directory**: Created ✅
- **Models Directory**: Created ✅
