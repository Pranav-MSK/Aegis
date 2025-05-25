# cython: language_level=3
from markdown import markdown
from bs4 import BeautifulSoup, Tag
import re

TAG_STYLES = {
    'h1': 'text-4xl font-extrabold text-indigo-800 mb-6 mt-8 scroll-mt-24',
    'h2': 'text-3xl font-bold text-indigo-700 mb-5 mt-7 scroll-mt-24',
    'h3': 'text-2xl font-semibold text-indigo-600 mb-4 mt-6',
    'h4': 'text-xl font-medium text-indigo-500 mb-3 mt-5',
    'h5': 'text-lg font-medium text-indigo-400 mb-2 mt-4',
    'h6': 'text-base font-medium text-indigo-300 mb-1 mt-3',
    'p': 'mb-4 text-gray-800 leading-relaxed tracking-normal',
    'ul': 'list-disc list-inside pl-6 mb-4 text-gray-800',
    'ol': 'list-decimal list-inside pl-6 mb-4 text-gray-800',
    'li': 'mb-1',
    'blockquote': 'border-l-4 border-blue-400 pl-6 italic text-gray-700 bg-blue-50 py-3 px-4 rounded-md my-6',
    'hr': 'my-8 border-t border-gray-300',
    'a': 'text-blue-700 hover:text-blue-900 underline',
    'code': 'bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-purple-700',
    'pre': 'bg-gray-100 text-gray-800 p-5 rounded-lg overflow-x-auto text-sm shadow-inner my-6 whitespace-pre-wrap break-words',
    'table': 'table-auto w-full border-collapse border border-gray-300 shadow-sm my-8 text-sm',
    'thead': 'bg-gray-100',
    'th': 'border px-4 py-3 text-left bg-gray-200 text-gray-700 font-semibold',
    'td': 'border px-4 py-2 text-gray-800'
}

HEADING_TAGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']

def wrap_content(start_tag, wrapper_tag, soup):
    """
    Wraps all siblings following `start_tag` until the next heading of equal or higher level,
    inside a `wrapper_tag` element (<section>, <article>, etc.)
    """
    level = int(start_tag.name[1])
    wrapper = soup.new_tag(wrapper_tag, **{'class': 'mb-10'})
    next_sibling = start_tag.find_next_sibling()

    while next_sibling and (
        not isinstance(next_sibling, Tag)
        or next_sibling.name not in HEADING_TAGS
        or int(next_sibling.name[1]) > level
    ):
        temp = next_sibling
        next_sibling = next_sibling.find_next_sibling()
        wrapper.append(temp.extract())

    start_tag.insert_after(wrapper)


def fix_nested_lists(soup):
    """
    Properly structures nested lists by identifying indentation patterns in markdown
    """
    # Fix nested lists by finding list items with sub-lists
    for ul in soup.find_all(['ul', 'ol']):
        # Find list items that contain other list elements
        for li in ul.find_all('li', recursive=False):
            # Check if the list item has a nested list right after it
            next_elem = li.find_next_sibling()
            if next_elem and next_elem.name in ['ul', 'ol']:
                # Move the nested list inside the list item
                nested_list = next_elem.extract()
                li.append(nested_list)

def process_nested_items(soup):
    """
    Process items that should be nested based on special content markers
    """
    pattern = re.compile(r'^(\s{2,})-\s+(.+)$', re.MULTILINE)
    
    # Find all list items for inspection
    for li in soup.find_all('li'):
        if li.strong:
            # Handle indentation for items like "**Participants**:"
            if li.strong.text.strip().endswith(':') or li.strong.text.strip().endswith('s'):
                # This is likely a header for nested items
                next_sibling = li.find_next_sibling()
                
                # Create a new sublist
                sublist = soup.new_tag('ul')
                sublist['class'] = TAG_STYLES['ul'].split()
                
                # Process subsequent list items that should be nested
                while next_sibling and next_sibling.name == 'li' and not next_sibling.strong:
                    temp = next_sibling
                    next_sibling = next_sibling.find_next_sibling()
                    sublist.append(temp.extract())
                
                # Only add the sublist if it has children
                if sublist.find('li'):
                    li.append(sublist)

def handle_special_formatting(soup):
    """
    Apply special formatting for certain elements based on content patterns
    """
    # Handle special formatting for code blocks, etc.
    for code in soup.find_all('code'):
        if code.parent.name != 'pre':
            code['class'] = TAG_STYLES['code'].split()

    # Handle tasks lists with checkboxes
    for li in soup.find_all('li'):
        if li.get_text().strip().startswith('✔️'):
            li['class'] = li.get('class', []) + ['flex', 'items-start', 'task-completed']

def process_markdown_with_tailwind(md_text: str) -> str:
    # Convert markdown to HTML with extensions
    html = markdown(md_text, extensions=['fenced_code', 'codehilite', 'tables', 'nl2br', 'extra'])
    soup = BeautifulSoup(html, 'html.parser')

    # Apply structure processing
    fix_nested_lists(soup)
    process_nested_items(soup)
    handle_special_formatting(soup)

    # Wrap content under headings using semantic tags
    for tag in soup.find_all(HEADING_TAGS):
        level = int(tag.name[1])
        if level <= 2:
            wrap_content(tag, 'section', soup)
        elif level <= 4:
            wrap_content(tag, 'article', soup)
        else:
            wrap_content(tag, 'div', soup)

    # Apply Tailwind classes
    for tag_name, class_list in TAG_STYLES.items():
        for el in soup.find_all(tag_name):
            # Skip <code> inside <pre>
            if tag_name == 'code' and el.parent.name == 'pre':
                continue
            # Preserve existing classes and add new ones
            existing_classes = el.get('class', [])
            el['class'] = existing_classes + class_list.split()
            
            if tag_name == 'a':
                el['target'] = '_blank'
                el['rel'] = 'noopener noreferrer'

    return str(soup)
