#!/usr/bin/env python3
"""
Process Baserow snapshots into web-ready JSON files.
Denormalizes relationships between companies, tools, and libraries.
"""

import json
from pathlib import Path
from typing import Dict, List, Any


def load_snapshots() -> tuple:
    """Load all Baserow snapshot files."""
    data_dir = Path(__file__).parent.parent / 'data' / 'snapshots'
    
    with open(data_dir / 'companies.json', encoding='utf-8') as f:
        companies = json.load(f)
    
    with open(data_dir / 'tools.json', encoding='utf-8') as f:
        tools = json.load(f)
    
    with open(data_dir / 'libraries.json', encoding='utf-8') as f:
        libraries = json.load(f)
    
    return companies, tools, libraries


def create_web_companies(companies: List[Dict], tools_by_id: Dict) -> List[Dict]:
    """
    Create web-ready company data with enriched tool information.
    
    Args:
        companies: Raw company data from Baserow
        tools_by_id: Lookup dictionary of tools by ID
        
    Returns:
        List of companies with full tool details
    """
    web_companies = []
    
    for company in companies:
        # Extract and enrich tool data
        company_tools = []
        for tool_ref in company.get('Tools', []):
            tool = tools_by_id.get(tool_ref['id'])
            if tool:
                company_tools.append({
                    'id': tool['UUID'],
                    'name': tool['ToolName'],
                    'description_short': tool.get('Tool Description Short', ''),
                    'description_long': tool.get('ToolDescription_long', ''),
                    'tags': [t['value'] for t in tool.get('Tool Tags', [])],
                    'rating': tool.get('Overall Rating', '0'),
                    'cost': tool.get('Annual License Cost'),
                    'url': tool.get('URL', '')
                })
        
        web_companies.append({
            'id': company['UUID'],
            'name': company['Company Name'],
            'url': company.get('URL', ''),
            'notes': company.get('Notes', ''),
            'tools': company_tools,
            'tool_count': len(company_tools)
        })
    
    return web_companies


def create_web_tools(tools: List[Dict], companies_by_id: Dict) -> List[Dict]:
    """
    Create web-ready tool data with enriched company information.
    
    Args:
        tools: Raw tool data from Baserow
        companies_by_id: Lookup dictionary of companies by ID
        
    Returns:
        List of tools with full company details
    """
    web_tools = []
    
    for tool in tools:
        # Extract and enrich company data
        tool_companies = []
        for comp_ref in tool.get('ToolCompany', []):
            comp = companies_by_id.get(comp_ref['id'])
            if comp:
                tool_companies.append({
                    'id': comp['UUID'],
                    'name': comp['Company Name'],
                    'url': comp.get('URL', '')
                })
        
        # Extract tag information
        tags = []
        tag_colors = {}
        for tag in tool.get('Tool Tags', []):
            tag_name = tag['value']
            tags.append(tag_name)
            if 'color' in tag:
                tag_colors[tag_name] = tag['color']
        
        web_tools.append({
            'id': tool['UUID'],
            'name': tool['ToolName'],
            'description_short': tool.get('Tool Description Short', ''),
            'description_long': tool.get('ToolDescription_long', ''),
            'tags': tags,
            'tag_colors': tag_colors,
            'companies': tool_companies,
            'rating': tool.get('Overall Rating', '0'),
            'cost': tool.get('Annual License Cost'),
            'url': tool.get('URL', ''),
            'last_modified': tool.get('Last modified', '')
        })
    
    return web_tools


def create_search_index(companies: List[Dict], tools: List[Dict]) -> List[Dict]:
    """
    Create a search index for frontend autocomplete/search.
    
    Args:
        companies: Processed company data
        tools: Processed tool data
        
    Returns:
        Flat list of searchable items
    """
    index = []
    
    # Add companies to index
    for company in companies:
        index.append({
            'type': 'company',
            'id': company['id'],
            'name': company['name'],
            'url': company['url'],
            'search_text': company['name'].lower(),
            'tool_count': company['tool_count']
        })
    
    # Add tools to index
    for tool in tools:
        tags_text = ' '.join(tool['tags']).lower()
        companies_text = ' '.join([c['name'] for c in tool['companies']]).lower()
        
        index.append({
            'type': 'tool',
            'id': tool['id'],
            'name': tool['name'],
            'url': tool['url'],
            'tags': tool['tags'],
            'search_text': f"{tool['name']} {tags_text} {companies_text}".lower(),
            'company_count': len(tool['companies'])
        })
    
    return index


def extract_all_tags(tools: List[Dict]) -> List[Dict]:
    """Extract unique list of all tags with their colors."""
    tags_dict = {}
    
    for tool in tools:
        for tag_name, color in tool.get('tag_colors', {}).items():
            if tag_name not in tags_dict:
                tags_dict[tag_name] = color
    
    return [
        {'name': name, 'color': color}
        for name, color in sorted(tags_dict.items())
    ]


def calculate_stats(companies: List[Dict], tools: List[Dict]) -> Dict[str, Any]:
    """Calculate summary statistics."""
    return {
        'total_companies': len(companies),
        'total_tools': len(tools),
        'companies_with_tools': sum(1 for c in companies if c['tool_count'] > 0),
        'tools_with_companies': sum(1 for t in tools if len(t['companies']) > 0),
        'total_tags': len(extract_all_tags(tools))
    }


def main():
    """Main processing pipeline."""
    print("Loading Baserow snapshots...")
    companies, tools, libraries = load_snapshots()
    
    # Create lookup dictionaries
    tools_by_id = {t['id']: t for t in tools}
    companies_by_id = {c['id']: c for c in companies}
    
    print("Processing data...")
    
    # Create web-ready data
    web_companies = create_web_companies(companies, tools_by_id)
    web_tools = create_web_tools(tools, companies_by_id)
    search_index = create_search_index(web_companies, web_tools)
    all_tags = extract_all_tags(web_tools)
    stats = calculate_stats(web_companies, web_tools)
    
    # Prepare output directory
    output_dir = Path(__file__).parent.parent / 'data' / 'web'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save individual files
    print(f"Saving to {output_dir}...")
    
    with open(output_dir / 'companies.json', 'w', encoding='utf-8') as f:
        json.dump(web_companies, f, indent=2, ensure_ascii=False)
    
    with open(output_dir / 'tools.json', 'w', encoding='utf-8') as f:
        json.dump(web_tools, f, indent=2, ensure_ascii=False)
    
    with open(output_dir / 'search_index.json', 'w', encoding='utf-8') as f:
        json.dump(search_index, f, indent=2, ensure_ascii=False)
    
    with open(output_dir / 'tags.json', 'w', encoding='utf-8') as f:
        json.dump(all_tags, f, indent=2, ensure_ascii=False)
    
    with open(output_dir / 'stats.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    # Save combined file
    combined = {
        'companies': web_companies,
        'tools': web_tools,
        'tags': all_tags,
        'stats': stats
    }
    
    with open(output_dir / 'all_data.json', 'w', encoding='utf-8') as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n✅ Processing complete!")
    print(f"   Companies: {stats['total_companies']}")
    print(f"   Tools: {stats['total_tools']}")
    print(f"   Tags: {stats['total_tags']}")
    print(f"   Companies with tools: {stats['companies_with_tools']}")
    print(f"   Tools with companies: {stats['tools_with_companies']}")
    print(f"\n📁 Output saved to: {output_dir.absolute()}")


if __name__ == '__main__':
    main()
