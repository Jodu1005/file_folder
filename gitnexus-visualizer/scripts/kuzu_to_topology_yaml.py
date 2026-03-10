#!/usr/bin/env python3
"""
Kuzu Database to System Topology YAML Converter
Converts GitNexus Kuzu graph database to System Topology YAML format.
"""

import kuzu
import yaml
import sys
from pathlib import Path
from collections import defaultdict, Counter


def analyze_module_responsibilities(db_path):
    """Analyze codebase to infer module responsibilities from structure"""
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)

    # Get file structure
    result = conn.execute('''
        MATCH (f:File)
        RETURN f.name as name, f.filePath as path
        ORDER BY path
    ''')

    files = {}
    for row in result:
        name, path = row
        if name and path:
            files[name] = path

    # Get function definitions per file
    result = conn.execute('''
        MATCH (f:File)-[r:CodeRelation]->(fn:Function)
        WHERE r.type = 'DEFINES'
        RETURN f.name as file_name, fn.name as func_name
        ORDER BY file_name, func_name
    ''')

    file_functions = defaultdict(list)
    for row in result:
        file_name, func_name = row
        if file_name and func_name:
            file_functions[file_name].append(func_name)

    # Get class definitions per file
    result = conn.execute('''
        MATCH (f:File)-[r:CodeRelation]->(c:Class)
        WHERE r.type = 'DEFINES'
        RETURN f.name as file_name, c.name as class_name
        ORDER BY file_name, class_name
    ''')

    file_classes = defaultdict(list)
    for row in result:
        file_name, class_name = row
        if file_name and class_name:
            file_classes[file_name].append(class_name)

    # Get import relationships
    result = conn.execute('''
        MATCH (f1:File)-[r:CodeRelation]->(f2:File)
        WHERE r.type = 'IMPORTS'
        RETURN f1.name as from_file, f2.name as to_file
    ''')

    imports = defaultdict(list)
    for row in result:
        from_file, to_file = row
        if from_file and to_file:
            imports[from_file].append(to_file)

    conn.close()
    db.close()

    return files, file_functions, file_classes, imports


def infer_responsibilities(file_name, functions, classes):
    """Infer responsibilities from function and class names"""
    responsibilities = []

    # Analyze function names
    for func in functions:
        func_lower = func.lower()
        if any(word in func_lower for word in ['validate', 'check', 'verify']):
            responsibilities.append(f"验证逻辑: {func}")
        elif any(word in func_lower for word in ['parse', 'load', 'read']):
            responsibilities.append(f"解析与加载: {func}")
        elif any(word in func_lower for word in ['execute', 'run', 'perform']):
            responsibilities.append(f"执行逻辑: {func}")
        elif any(word in func_lower for word in ['render', 'display', 'show', 'ui']):
            responsibilities.append(f"UI渲染: {func}")

    # Analyze class names
    for cls in classes:
        cls_lower = cls.lower()
        if 'manager' in cls_lower:
            responsibilities.append(f"管理器: {cls}")
        elif 'controller' in cls_lower:
            responsibilities.append(f"控制器: {cls}")
        elif 'model' in cls_lower or 'schema' in cls_lower:
            responsibilities.append(f"数据模型: {cls}")
        elif 'executor' in cls_lower:
            responsibilities.append(f"执行器: {cls}")

    # File-based inference
    file_lower = file_name.lower()
    if 'test' in file_lower:
        responsibilities.insert(0, "单元测试与验证")
    elif 'main' in file_lower or 'app' in file_lower:
        responsibilities.insert(0, "应用入口与初始化")
    elif 'config' in file_lower:
        responsibilities.insert(0, "配置管理与参数解析")
    elif 'exception' in file_lower or 'error' in file_lower:
        responsibilities.insert(0, "异常处理与错误定义")

    return responsibilities if responsibilities else ["通用功能模块"]


def categorize_component(file_name, functions, classes):
    """Categorize component into process_type"""
    file_lower = file_name.lower()

    if 'test' in file_lower:
        return "Test_Module"
    elif 'main' in file_lower or 'app' in file_lower:
        return "Application_Entry_Point"
    elif any(x in file_lower for x in ['model', 'schema', 'result']):
        return "Data_Model_Layer"
    elif any(x in file_lower for x in ['controller', 'executor', 'orchestrator']):
        return "Business_Logic_Layer"
    elif any(x in file_lower for x in ['validator', 'parser']):
        return "Validation_Parsing_Layer"
    elif any(x in file_lower for x in ['config', 'setting']):
        return "Configuration_Layer"
    elif 'exception' in file_lower or 'error' in file_lower:
        return "Exception_Handling_Layer"
    else:
        return "Utility_Module"


def generate_topology_yaml(db_path, output_file):
    """Generate System Topology YAML from Kuzu database"""
    print("="*70)
    print("Kuzu to System Topology YAML Converter")
    print("="*70)

    print(f"\nAnalyzing: {db_path}")

    # Analyze codebase
    files, file_functions, file_classes, imports = analyze_module_responsibilities(db_path)

    print(f"Found {len(files)} files")
    print(f"Found {len(file_functions)} files with functions")
    print(f"Found {len(file_classes)} files with classes")

    # Build topology structure
    topology_data = {
        'system_context': {
            'platform': 'Python UI Automation Framework',
            'backend_language': 'Python 3.11+',
            'project_name': 'UI-Agent',
            'description': 'Intelligent UI automation agent using visual recognition and intent-based workflow execution'
        },
        'components': [],
        'architectural_constraints': []
    }

    # Identify key modules (files with most dependencies)
    dependency_count = Counter()
    for from_file, to_files in imports.items():
        dependency_count[from_file] += len(to_files)

    # Select top components by dependency importance
    top_files = [f for f, _ in dependency_count.most_common(30)]

    # Generate components
    for file_name in top_files:
        if file_name not in files:
            continue

        functions = file_functions.get(file_name, [])
        classes = file_classes.get(file_name, [])
        file_path = files.get(file_name, '')

        component = {
            'name': file_name.replace('.py', ''),
            'file_path': file_path,
            'layer': categorize_component(file_name, functions, classes),
            'type': categorize_component(file_name, functions, classes),
            'responsibilities': infer_responsibilities(file_name, functions, classes),
            'defines': {
                'functions': len(functions),
                'classes': len(classes)
            }
        }

        # Add dependencies (imports)
        if file_name in imports:
            component['dependencies'] = [
                f.replace('.py', '') for f in imports[file_name][:15]  # Limit to 15
            ]
            component['dependency_count'] = len(imports[file_name])

        topology_data['components'].append(component)

    # Generate architectural constraints based on patterns
    topology_data['architectural_constraints'] = [
        {
            'rule_1': 'Layer Isolation: Test modules MUST only import from production code, never vice versa.',
            'rule_2': 'Dependency Inversion: Business Logic Layer should depend on abstractions (interfaces) not concrete implementations.',
            'rule_3': 'Single Responsibility: Each module should have one clear purpose - validation, execution, or configuration.',
            'rule_4': 'Error Propagation: All exceptions must flow through the defined exception hierarchy, never use raw exceptions.'
        }
    ]

    # Write YAML
    print(f"\n{'='*70}")
    print(f"Writing to: {output_file}")
    print(f"{'='*70}")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# ---------------------------------------------------------------------------\n")
        f.write("# File: System_Topology.yaml\n")
        f.write("# Purpose: Define UI-Agent module boundaries, dependencies, and responsibilities.\n")
        f.write("# Target LLM Action: Use this to validate architecture when generating code.\n")
        f.write("# ---------------------------------------------------------------------------\n\n")
        yaml.dump(topology_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=1000)

    print(f"\n{'='*70}")
    print("Conversion complete!")
    print(f"{'='*70}")
    print(f"\nStatistics:")
    print(f"  Components: {len(topology_data['components'])}")
    print(f"  Architectural Rules: {len(topology_data['architectural_constraints'])}")
    print(f"\nOutput file: {output_file}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python kuzu_to_topology_yaml.py <kuzu_db_path> [output_yaml_file]")
        print("\nExamples:")
        print("  python kuzu_to_topology_yaml.py kuzu")
        print("  python kuzu_to_topology_yaml.py .gitnexus/kuzu System_Topology.yaml")
        print("  python kuzu_to_topology_yaml.py /path/to/kuzu_db custom_topology.yaml")
        sys.exit(1)

    input_path = Path(sys.argv[1]).resolve()

    # Handle different input formats
    if input_path.is_file():
        kuzu_path = str(input_path)
        base_dir = input_path.parent
    elif input_path.is_dir():
        kuzu_file = input_path / 'kuzu'
        if kuzu_file.exists():
            kuzu_path = str(kuzu_file)
            base_dir = input_path
        else:
            print(f"Error: Cannot find kuzu database file at {input_path}")
            sys.exit(1)
    else:
        print(f"Error: Path does not exist: {input_path}")
        sys.exit(1)

    # Determine output file
    if len(sys.argv) >= 3:
        output_file = Path(sys.argv[2])
    else:
        output_file = base_dir / 'System_Topology.yaml'

    try:
        generate_topology_yaml(kuzu_path, output_file)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
