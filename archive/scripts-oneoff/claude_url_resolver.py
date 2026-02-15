#!/usr/bin/env python3
"""
Test Claude for company URL resolution from name + address
Cost analysis: Claude Sonnet 3.5 pricing vs Google Places
"""
import anthropic
import os
import json

# Claude API pricing (as of 2024)
# Sonnet 3.5: $3/1M input tokens, $15/1M output tokens
# Haiku: $0.25/1M input, $1.25/1M output

# Typical prompt size: ~100 tokens input, ~50 tokens output
# Cost per lookup (Sonnet): ~$0.0003 + $0.00075 = ~$0.001
# Cost per lookup (Haiku): ~$0.000025 + $0.0000625 = ~$0.0001

# Google Places: $0.017 per call
# Claude Sonnet: ~$0.001 per call (17x cheaper)
# Claude Haiku: ~$0.0001 per call (170x cheaper)

def resolve_url_with_claude(company_name: str, address: str, city: str, state: str, zip_code: str) -> dict:
    """Use Claude to infer company website URL"""
    
    client = anthropic.Anthropic()
    
    prompt = f"""Given this company information, provide the most likely website URL.

Company Name: {company_name}
Address: {address}
City: {city}
State: {state}
ZIP: {zip_code}

Respond with ONLY a JSON object:
{{"url": "https://example.com", "confidence": "high|medium|low", "reasoning": "brief explanation"}}

If you cannot determine the URL with reasonable confidence, respond:
{{"url": null, "confidence": "none", "reasoning": "why unknown"}}

Do not guess random URLs. Only provide URLs you have strong evidence for."""

    response = client.messages.create(
        model="claude-3-5-haiku-20241022",  # Use Haiku for cost efficiency
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}]
    )
    
    try:
        result = json.loads(response.content[0].text)
        result['input_tokens'] = response.usage.input_tokens
        result['output_tokens'] = response.usage.output_tokens
        return result
    except json.JSONDecodeError:
        return {
            "url": None,
            "confidence": "error",
            "reasoning": response.content[0].text,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens
        }


# Test cases - mix of well-known and obscure companies
TEST_CASES = [
    {
        "company_name": "MINUTEMEN STAFFING INC",
        "address": "1001 FALLS CREST DR",
        "city": "WEST CHESTER",
        "state": "OH",
        "zip": "45069"
    },
    {
        "company_name": "JOHN DEERE",
        "address": "ONE JOHN DEERE PLACE",
        "city": "MOLINE",
        "state": "IL",
        "zip": "61265"
    },
    {
        "company_name": "ACME STAFFING SOLUTIONS LLC",
        "address": "123 MAIN ST",
        "city": "CHARLOTTE",
        "state": "NC",
        "zip": "28202"
    },
    {
        "company_name": "PROSTAFF WORKFORCE SOLUTIONS",
        "address": "500 GRANT ST",
        "city": "PITTSBURGH",
        "state": "PA",
        "zip": "15219"
    },
]


if __name__ == "__main__":
    print("Claude URL Resolution Test")
    print("=" * 70)
    print()
    print("Cost Comparison:")
    print("  Google Places: $0.017 per call")
    print("  Claude Sonnet: ~$0.001 per call (17x cheaper)")
    print("  Claude Haiku:  ~$0.0001 per call (170x cheaper)")
    print()
    print("For 51,148 companies:")
    print("  Google Places: $869.52")
    print("  Claude Sonnet: ~$51.15")
    print("  Claude Haiku:  ~$5.11")
    print()
    print("-" * 70)
    
    total_input = 0
    total_output = 0
    
    for i, test in enumerate(TEST_CASES, 1):
        print(f"\nTest {i}: {test['company_name']}")
        print(f"  Location: {test['city']}, {test['state']} {test['zip']}")
        
        result = resolve_url_with_claude(
            test['company_name'],
            test['address'],
            test['city'],
            test['state'],
            test['zip']
        )
        
        print(f"  URL: {result.get('url')}")
        print(f"  Confidence: {result.get('confidence')}")
        print(f"  Reasoning: {result.get('reasoning')}")
        print(f"  Tokens: {result.get('input_tokens')} in / {result.get('output_tokens')} out")
        
        total_input += result.get('input_tokens', 0)
        total_output += result.get('output_tokens', 0)
    
    print()
    print("=" * 70)
    print(f"Total tokens: {total_input} input / {total_output} output")
    avg_in = total_input / len(TEST_CASES)
    avg_out = total_output / len(TEST_CASES)
    print(f"Avg per lookup: {avg_in:.0f} input / {avg_out:.0f} output")
    
    # Calculate actual cost
    haiku_cost = (total_input * 0.25 / 1_000_000) + (total_output * 1.25 / 1_000_000)
    print(f"This test cost (Haiku): ${haiku_cost:.6f}")
    
    projected = haiku_cost / len(TEST_CASES) * 51148
    print(f"Projected cost for 51,148 companies: ${projected:.2f}")
