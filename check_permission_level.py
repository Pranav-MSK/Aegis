import ast
import os
import pandas as pd

class FunctionVisitor(ast.NodeVisitor):
    def __init__(self):
        self.function_data = []

    def visit_FunctionDef(self, node):
        decorators = [d.id for d in node.decorator_list if isinstance(d, ast.Name)]
        
        # Check for docstring
        has_docstring = ast.get_docstring(node) is not None
        
        # Calculate total lines of code (excluding decorators)
        start_line = node.lineno
        end_line = node.end_lineno
        total_lines = end_line - start_line + 1

        function_info = {
            'function_name': node.name,
            'login_required': 'login_required' in decorators,
            'admin_required': 'admin_required' in decorators,
            'user_has_access_to_alert': 'user_has_access_to_alert' in decorators,
            'has_docstring': has_docstring,
            'total_lines': total_lines,
            'other_decorators': [d for d in decorators if d not in ['login_required', 'admin_required', 'user_has_access_to_alert']],
        }
        self.function_data.append(function_info)
        self.generic_visit(node)

def analyze_python_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        tree = ast.parse(file.read(), filename=file_path)
    visitor = FunctionVisitor()
    visitor.visit(tree)
    return visitor.function_data

def analyze_directory(directory):
    all_function_data = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                function_data = analyze_python_file(file_path)
                all_function_data.extend(function_data)
    return all_function_data

def create_dataframe(function_data):
    return pd.DataFrame(function_data)

def main(directory):
    function_data = analyze_directory(directory)
    df = create_dataframe(function_data)
    
    # Save the dataframe to a CSV file
    df.to_csv('permission_level.csv', index=False)
    
    # Print the dataframe in a tabular format
    print(df.to_string(index=False))

if __name__ == "__main__":
    directory_to_analyze = "src/routes"  # Change this to your target directory
    main(directory_to_analyze)
