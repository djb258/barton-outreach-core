export async function fetchFromMCP(path: string, opts: RequestInit = {}) {
  const baseUrl = import.meta.env.VITE_API_BASE || 'https://mcpo-jte8.onrender.com';
  const mcpKey = import.meta.env.VITE_MCP_KEY || '';
  
  const res = await fetch(`${baseUrl}${path}`, {
    headers: {
      Authorization: `Bearer ${mcpKey}`,
      "Content-Type": "application/json",
    },
    ...opts,
  });
  
  if (!res.ok) {
    const error = await res.text();
    throw new Error(error || `MCP request failed: ${res.status}`);
  }
  
  return res.json();
}
