/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/api
Barton ID: 04.04.12
Unique ID: CTB-902CA631
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

/**
 * Doctrine Spec:
 * - Barton ID: 04.04.12
 * - Altitude: 10000 (Execution Layer)
 * - Input: LLM prompt and model configuration
 * - Output: AI-generated response and metadata
 * - MCP: Composio (Neon integrated)
 */
export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', ['POST']);
    return res.status(405).end(`Method ${req.method} Not Allowed`);
  }

  const { prompt, provider = 'openai', model, system, json = false, max_tokens = 1024 } = req.body;

  if (!prompt) {
    return res.status(400).json({ error: 'Prompt is required' });
  }

  // Check for API keys from environment
  const anthropicKey = process.env.IMOCREATOR_ANTHROPIC_API_KEY || process.env.ANTHROPIC_API_KEY;
  const openaiKey = process.env.IMOCREATOR_OPENAI_API_KEY || process.env.OPENAI_API_KEY;

  // Determine which provider to use
  let selectedProvider = provider;
  if (!provider) {
    if (model?.startsWith('claude')) {
      selectedProvider = 'anthropic';
    } else if (model?.startsWith('gpt') || model?.startsWith('o')) {
      selectedProvider = 'openai';
    } else if (anthropicKey && !openaiKey) {
      selectedProvider = 'anthropic';
    } else if (openaiKey && !anthropicKey) {
      selectedProvider = 'openai';
    }
  }

  // Mock response for development
  if (!anthropicKey && !openaiKey) {
    return res.status(200).json({
      content: json 
        ? JSON.stringify({
            suggestion: "This is a mock response. Configure API keys for real LLM integration.",
            tasks: ["Task 1", "Task 2", "Task 3"]
          })
        : "This is a mock response. Configure IMOCREATOR_OPENAI_API_KEY or IMOCREATOR_ANTHROPIC_API_KEY environment variables for real LLM integration.",
      provider: 'mock',
      model: 'mock-1.0',
      usage: {
        prompt_tokens: 10,
        completion_tokens: 20,
        total_tokens: 30
      }
    });
  }

  try {
    let response;
    
    if (selectedProvider === 'anthropic' && anthropicKey) {
      // Anthropic API call
      const anthropicResponse = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': anthropicKey,
          'anthropic-version': '2023-06-01'
        },
        body: JSON.stringify({
          model: model || 'claude-3-sonnet-20240229',
          max_tokens: max_tokens,
          messages: [
            ...(system ? [{ role: 'system', content: system }] : []),
            { role: 'user', content: prompt }
          ]
        })
      });

      if (!anthropicResponse.ok) {
        throw new Error(`Anthropic API error: ${anthropicResponse.statusText}`);
      }

      const data = await anthropicResponse.json();
      response = {
        content: data.content[0].text,
        provider: 'anthropic',
        model: model || 'claude-3-sonnet-20240229',
        usage: data.usage
      };
    } else if (selectedProvider === 'openai' && openaiKey) {
      // OpenAI API call
      const openaiResponse = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${openaiKey}`
        },
        body: JSON.stringify({
          model: model || 'gpt-4-turbo-preview',
          messages: [
            ...(system ? [{ role: 'system', content: system }] : []),
            { role: 'user', content: prompt }
          ],
          max_tokens: max_tokens,
          ...(json ? { response_format: { type: 'json_object' } } : {})
        })
      });

      if (!openaiResponse.ok) {
        throw new Error(`OpenAI API error: ${openaiResponse.statusText}`);
      }

      const data = await openaiResponse.json();
      response = {
        content: data.choices[0].message.content,
        provider: 'openai',
        model: model || 'gpt-4-turbo-preview',
        usage: data.usage
      };
    } else {
      return res.status(400).json({ 
        error: `No API key available for provider: ${selectedProvider}` 
      });
    }

    res.status(200).json(response);
  } catch (error) {
    console.error('LLM API error:', error);
    res.status(500).json({ 
      error: 'Failed to process LLM request',
      details: error.message 
    });
  }
}