#!/usr/bin/env python3
"""
Fix repository URLs in README.md and Smithery manifest
"""

# Fix README.md
with open('README.md', 'r') as f:
    readme_content = f.read()

# Fix Python version badge (3.10+ -> 3.8+)
readme_content = readme_content.replace(
    '[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)',
    '[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)'
)

# Fix repository URL placeholder
readme_content = readme_content.replace(
    'git clone <repository-url>',
    'git clone https://github.com/rainbowgore/stealthee-MCP-tools'
)

# Fix directory name in clone instructions
readme_content = readme_content.replace(
    'cd stealthed',
    'cd stealthee-MCP-tools'
)

# Fix project structure directory name
readme_content = readme_content.replace(
    'stealthed/',
    'stealthee-MCP-tools/'
)

# Fix Claude Desktop config paths
readme_content = readme_content.replace(
    '/path/to/stealthed/',
    '/path/to/stealthee-MCP-tools/'
)

# Fix GitHub issues link
readme_content = readme_content.replace(
    'Create an issue on GitHub',
    'Create an issue on [GitHub](https://github.com/rainbowgore/stealthee-MCP-tools/issues)'
)

with open('README.md', 'w') as f:
    f.write(readme_content)

# Fix Smithery manifest
with open('.smithery/manifest.json', 'r') as f:
    manifest_content = f.read()

# Fix repository URL in manifest
manifest_content = manifest_content.replace(
    '"url": "https://github.com/your-org/stealthed"',
    '"url": "https://github.com/rainbowgore/stealthee-MCP-tools"'
)

with open('.smithery/manifest.json', 'w') as f:
    f.write(manifest_content)

print("✅ Fixed: Python version badge (3.10+ -> 3.8+)")
print("✅ Fixed: Repository URL in README.md")
print("✅ Fixed: Directory names in README.md")
print("✅ Fixed: GitHub issues link")
print("✅ Fixed: Repository URL in Smithery manifest")
