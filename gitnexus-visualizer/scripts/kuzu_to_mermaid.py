"""
Kuzu to Mermaid Graph Converter
Converts GitNexus Kuzu graph databases to Mermaid diagram files.
"""

import kuzu
from collections import defaultdict
import os
import sys


def get_output_dir():
    """Determine output directory - use argument or default to .gitnexus/mermaid图"""
    if len(sys.argv) > 1:
        return sys.argv[1]
    # Default: find .gitnexus directory and create output subdirectory
    cwd = os.getcwd()
    if '.gitnexus' in cwd:
        # We're inside or at .gitnexus level
        gitnexus_dir = cwd if cwd.endswith('.gitnexus') else os.path.join(cwd, '.gitnexus')
        return os.path.join(gitnexus_dir, 'mermaid图')
    # Check if .gitnexus exists in parent
    parent_dir = os.path.dirname(cwd)
    if os.path.exists(os.path.join(parent_dir, '.gitnexus')):
        return os.path.join(parent_dir, '.gitnexus', 'mermaid图')
    # Fallback to current directory
    return os.path.join(cwd, 'mermaid输出')


def find_kuzu_db():
    """Find the Kuzu database file"""
    cwd = os.getcwd()
    # Check current directory first
    if os.path.exists(os.path.join(cwd, 'kuzu')):
        return os.path.join(cwd, 'kuzu')
    # Check parent directories for .gitnexus
    for path in [cwd, os.path.dirname(cwd)]:
        gitnexus_path = os.path.join(path, '.gitnexus', 'kuzu')
        if os.path.exists(gitnexus_path):
            return gitnexus_path
    return 'kuzu'  # Default fallback


OUTPUT_DIR = get_output_dir()


def generate_calls_graph(db_path='kuzu', output_file='graph_core.mmd', max_nodes=30):
    """Generate function call relationship graph"""
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)

    lines = ['%%{init: {\'theme\': \'base\'}}%%']
    lines.append('graph TD')

    result = conn.execute('''
        MATCH (f1:Function)-[r]->(f2:Function)
        WHERE r.type = 'CALLS'
        RETURN f1.name as from_name, f2.name as to_name
    ''')

    connection_count = defaultdict(int)
    all_edges = []

    for from_name, to_name in result:
        connection_count[from_name] += 1
        connection_count[to_name] += 1
        all_edges.append((from_name, to_name))

    top_nodes = set(sorted(connection_count.items(), key=lambda x: x[1], reverse=True)[:max_nodes])
    top_node_names = set([n[0] for n in top_nodes])
    edges = [(f, t) for f, t in all_edges if f in top_node_names and t in top_node_names]

    nodes = {}
    for name in sorted(top_node_names):
        nodes[name] = f'n{len(nodes)}'

    for name, count in top_nodes:
        node_id = nodes[name]
        safe_name = name.replace('"', '\\"')[:35]
        lines.append(f'    {node_id}(["{safe_name}<br/><sub>{count} conn</sub>"])')

    for from_name, to_name in edges:
        lines.append(f'    {nodes[from_name]} -->|CALLS| {nodes[to_name]}')

    lines.append('    classDef node fill:#e1f5fe,stroke:#0277bd,stroke-width:2px')
    lines.append('    class ' + ','.join(nodes.values()) + ' node')

    content = '\n'.join(lines)
    output_path = os.path.join(OUTPUT_DIR, output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  [OK] CALLS - {len(top_node_names)} nodes, {len(edges)} edges")


def generate_extends_graph(db_path='kuzu'):
    """Generate class inheritance relationship graph"""
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)

    lines = ['%%{init: {\'theme\': \'base\'}}%%']
    lines.append('graph TD')

    result = conn.execute('''
        MATCH (c1)-[r]->(c2)
        WHERE r.type = 'EXTENDS'
        RETURN c1.name as child, c2.name as parent
    ''')

    edges = []
    nodes = set()

    for child, parent in result:
        nodes.add(child)
        nodes.add(parent)
        edges.append((child, parent))

    node_ids = {name: f'n{i}' for i, name in enumerate(sorted(nodes))}

    for name in sorted(nodes):
        node_id = node_ids[name]
        safe_name = name.replace('"', '\\"')[:35]
        lines.append(f'    {node_id}(["{safe_name}"])')

    for child, parent in edges:
        lines.append(f'    {node_ids[child]} -->|EXTENDS| {node_ids[parent]}')

    lines.append('    classDef cls fill:#fff9c4,stroke:#f57f17,stroke-width:2px')
    lines.append('    class ' + ','.join(node_ids.values()) + ' cls')

    content = '\n'.join(lines)
    output_path = os.path.join(OUTPUT_DIR, '02_EXTENDS_classes.mmd')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  [OK] EXTENDS - {len(nodes)} classes, {len(edges)} inheritance relationships")


def generate_defines_graph(db_path='kuzu'):
    """Generate file definition relationships graph"""
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)

    lines = ['%%{init: {\'theme\': \'base\'}}%%']
    lines.append('graph TD')

    result = conn.execute('''
        MATCH (f:File)-[r]->(func:Function)
        WHERE r.type = 'DEFINES'
        RETURN f.name as file, func.name as func
        LIMIT 80
    ''')

    file_nodes = {}

    for file_name, func_name in result:
        if file_name not in file_nodes:
            file_nodes[file_name] = []
        file_nodes[file_name].append(func_name)

    for i, (file_name, funcs) in enumerate(sorted(file_nodes.items())[:15]):
        safe_file = file_name.replace('"', '\\"')[:25]
        lines.append(f'    subgraph file{i}["{{{{file}}}} {safe_file}"]')
        for func in funcs[:8]:
            safe_func = func.replace('"', '\\"')[:30]
            func_id = f'f{i}_{hash(func) % 10000}'
            lines.append(f'        {func_id}["{safe_func}"]')
        lines.append('    end')

    content = '\n'.join(lines)
    output_path = os.path.join(OUTPUT_DIR, '03_DEFINES_files.mmd')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  [OK] DEFINES - {len(file_nodes)} files define functions/classes")


def generate_member_of_graph(db_path='kuzu'):
    """Generate class member relationships graph"""
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)

    lines = ['%%{init: {\'theme\': \'base\'}}%%']
    lines.append('graph TD')

    result = conn.execute('''
        MATCH (func)-[r]->(c:Class)
        WHERE r.type = 'MEMBER_OF'
        RETURN c.name as cls, func.name as func
        ORDER BY cls
    ''')

    class_members = defaultdict(list)

    for cls_name, func_name in result:
        class_members[cls_name].append(func_name)

    for i, (cls_name, funcs) in enumerate(sorted(class_members.items())[:20]):
        safe_cls = cls_name.replace('"', '\\"')[:30]
        lines.append(f'    subgraph class{i}["{{{{class}}}} {safe_cls}"]')
        for func in funcs[:10]:
            safe_func = func.replace('"', '\\"')[:25]
            lines.append(f'        m{i}_{func}["{safe_func}"]')
        lines.append('    end')

    content = '\n'.join(lines)
    output_path = os.path.join(OUTPUT_DIR, '04_MEMBER_OF_classes.mmd')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  [OK] MEMBER_OF - {len(class_members)} classes and their members")


def generate_imports_graph(db_path='kuzu'):
    """Generate import dependency relationships graph"""
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)

    lines = ['%%{init: {\'theme\': \'base\'}}%%']
    lines.append('graph LR')

    result = conn.execute('''
        MATCH (f1)-[r]->(f2)
        WHERE r.type = 'IMPORTS'
        RETURN f1.name as from_file, f2.name as to_file
    ''')

    files = set()
    edges = []

    for from_file, to_file in result:
        files.add(from_file)
        files.add(to_file)
        edges.append((from_file, to_file))

    file_ids = {f: f'n{i}' for i, f in enumerate(sorted(files))}

    for file_name in sorted(files):
        node_id = file_ids[file_name]
        safe_name = file_name.replace('"', '\\"')[:30]
        lines.append(f'    {node_id}["{{{{file}}}} {safe_name}"]')

    for from_file, to_file in edges:
        lines.append(f'    {file_ids[from_file]} -->|imports| {file_ids[to_file]}')

    lines.append('    classDef file fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px')
    lines.append('    class ' + ','.join(file_ids.values()) + ' file')

    content = '\n'.join(lines)
    output_path = os.path.join(OUTPUT_DIR, '05_IMPORTS_files.mmd')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  [OK] IMPORTS - {len(files)} files, {len(edges)} import relationships")


def generate_contains_graph(db_path='kuzu'):
    """Generate containment relationships graph"""
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)

    lines = ['%%{init: {\'theme\': \'base\'}}%%']
    lines.append('graph TD')

    result = conn.execute('''
        MATCH (a)-[r]->(b)
        WHERE r.type = 'CONTAINS'
        RETURN labels(a)[0] as from_type, a.name as from_name, labels(b)[0] as to_type, b.name as to_name
        LIMIT 50
    ''')

    lines.append('    subgraph Contains["Contains CONTAINS"]')

    nodes = {}
    for from_type, from_name, to_type, to_name in result:
        if from_name not in nodes:
            nodes[from_name] = f'n{len(nodes)}'
        if to_name not in nodes:
            nodes[to_name] = f'n{len(nodes)}'

        safe_from = from_name.replace('"', '\\"')[:25]
        safe_to = to_name.replace('"', '\\"')[:25]
        lines.append(f'    {nodes[from_name]}["{safe_from}"] -->|contains| {nodes[to_name]}["{safe_to}"]')

    lines.append('    end')

    content = '\n'.join(lines)
    output_path = os.path.join(OUTPUT_DIR, '06_CONTAINS.mmd')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  [OK] CONTAINS - {len(nodes)} nodes")


def generate_process_graph(db_path='kuzu'):
    """Generate execution process flow graph"""
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)

    lines = ['%%{init: {\'theme\': \'base\'}}%%']
    lines.append('graph TD')

    result = conn.execute('''
        MATCH (p:Process)
        RETURN p.id as id, p.label as label
        ORDER BY p.id
    ''')

    processes = []
    for proc_id, label in result:
        processes.append((proc_id, label if label else 'unnamed'))

    for i, (proc_id, label) in enumerate(processes[:10]):
        result = conn.execute('''
            MATCH (p:Process {id: $proc_id})-[r]->(s)
            WHERE r.type = 'STEP_IN_PROCESS'
            RETURN s.name as step_name
        ''', {'proc_id': proc_id})

        steps = []
        for row in result:
            steps.append(row[0])

        if steps:
            safe_label = label.replace('"', '\\"')[:30]
            lines.append(f'    subgraph proc{i}["{{{{process}}}} {safe_label} ({len(steps)} steps)"]')

            for j, step in enumerate(steps[:8]):
                safe_step = step.replace('"', '\\"')[:30]
                lines.append(f'        s{i}_{j}["{safe_step}"]')
                if j > 0:
                    lines.append(f'        s{i}_{j-1} --> s{i}_{j}')

            lines.append('    end')

    content = '\n'.join(lines)
    output_path = os.path.join(OUTPUT_DIR, '07_STEP_IN_PROCESS.mmd')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  [OK] STEP_IN_PROCESS - {len(processes)} execution flows")


def generate_community_graph(db_path='kuzu'):
    """Generate functional module/community graph"""
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)

    lines = ['%%{init: {\'theme\': \'base\'}}%%']
    lines.append('graph TD')

    result = conn.execute('''
        MATCH (c:Community)
        RETURN c.id as id, c.label as label, c.cohesion as cohesion, c.symbolCount as count
        ORDER BY cohesion DESC
    ''')

    communities = []
    for comm_id, label, cohesion, count in result:
        communities.append((comm_id, label if label else 'unnamed', cohesion, count))

    for i, (comm_id, label, cohesion, count) in enumerate(communities[:12]):
        result = conn.execute('''
            MATCH (s)-[r]->(c:Community {id: $cid})
            WHERE r.type = 'MEMBER_OF'
            RETURN s.name as symbol
            LIMIT 10
        ''', {'cid': comm_id})

        members = []
        for row in result:
            members.append(row[0])

        safe_label = label.replace('"', '\\"')[:25]
        lines.append(f'    subgraph comm{i}["{{{{module}}}} {safe_label}<br/>{cohesion:.2f} cohesion, {count} symbols"]')

        for member in members:
            safe_member = member.replace('"', '\\"')[:30]
            lines.append(f'        m{i}_{member}["{safe_member}"]')

        lines.append('    end')

    content = '\n'.join(lines)
    output_path = os.path.join(OUTPUT_DIR, '08_COMMUNITY_modules.mmd')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  [OK] COMMUNITY - {len(communities)} functional modules")


def generate_all_relations_graph(db_path='kuzu'):
    """Generate complete all-in-one relationship graph"""
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)

    lines = ['%%{init: {\'theme\': \'base\'}}%%']
    lines.append('graph TD')

    result = conn.execute('''
        MATCH (f1:Function)-[r]->(f2:Function)
        WHERE r.type = 'CALLS'
        RETURN f1.name as from_name, f2.name as to_name
        LIMIT 50
    ''')
    calls_edges = list(result)

    result = conn.execute('''
        MATCH (c1)-[r]->(c2)
        WHERE r.type = 'EXTENDS'
        RETURN c1.name as child, c2.name as parent
    ''')
    extends_edges = list(result)

    result = conn.execute('''
        MATCH (f:File)-[r]->(func)
        WHERE r.type = 'DEFINES'
        RETURN f.name as file, func.name as func
        LIMIT 30
    ''')
    defines_edges = list(result)

    result = conn.execute('''
        MATCH (f1)-[r]->(f2)
        WHERE r.type = 'IMPORTS'
        RETURN f1.name as from_file, f2.name as to_file
    ''')
    imports_edges = list(result)

    func_nodes = set()
    class_nodes = set()
    file_nodes = set()
    node_to_id = {}
    node_id = 0

    for from_name, to_name in calls_edges:
        if from_name not in node_to_id:
            node_to_id[from_name] = f'n{node_id}'
            func_nodes.add(from_name)
            node_id += 1
        if to_name not in node_to_id:
            node_to_id[to_name] = f'n{node_id}'
            func_nodes.add(to_name)
            node_id += 1

    for child, parent in extends_edges:
        if child not in node_to_id:
            node_to_id[child] = f'n{node_id}'
            class_nodes.add(child)
            node_id += 1
        if parent not in node_to_id:
            node_to_id[parent] = f'n{node_id}'
            class_nodes.add(parent)
            node_id += 1

    for file_name, func_name in defines_edges:
        if file_name not in node_to_id:
            node_to_id[file_name] = f'n{node_id}'
            file_nodes.add(file_name)
            node_id += 1
        if func_name not in node_to_id:
            node_to_id[func_name] = f'n{node_id}'
            func_nodes.add(func_name)
            node_id += 1

    for from_file, to_file in imports_edges:
        if from_file not in node_to_id:
            node_to_id[from_file] = f'n{node_id}'
            file_nodes.add(from_file)
            node_id += 1
        if to_file not in node_to_id:
            node_to_id[to_file] = f'n{node_id}'
            file_nodes.add(to_file)
            node_id += 1

    lines.append('')
    lines.append('    %% Nodes')
    for name, nid in sorted(node_to_id.items(), key=lambda x: x[1]):
        safe_name = name.replace('"', '\\"')[:30]
        lines.append(f'    {nid}["{safe_name}"]')

    lines.append('')
    lines.append('    %% Relationships')
    for from_name, to_name in calls_edges:
        lines.append(f'    {node_to_id[from_name]} -->|CALLS| {node_to_id[to_name]}')

    for child, parent in extends_edges:
        lines.append(f'    {node_to_id[child]} -->|EXTENDS| {node_to_id[parent]}')

    for file_name, func_name in defines_edges:
        lines.append(f'    {node_to_id[file_name]} -.->|DEFINES| {node_to_id[func_name]}')

    for from_file, to_file in imports_edges:
        lines.append(f'    {node_to_id[from_file]} ==>|IMPORTS| {node_to_id[to_file]}')

    lines.append('')
    lines.append('    %% Styles')
    lines.append('    classDef func fill:#e1f5fe,stroke:#0277bd,stroke-width:2px')
    lines.append('    classDef cls fill:#fff9c4,stroke:#f57f17,stroke-width:2px')
    lines.append('    classDef file fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px')

    func_ids = [node_to_id[n] for n in func_nodes]
    class_ids = [node_to_id[n] for n in class_nodes]
    file_ids = [node_to_id[n] for n in file_nodes]

    if func_ids:
        lines.append(f'    class {",".join(func_ids)} func')
    if class_ids:
        lines.append(f'    class {",".join(class_ids)} cls')
    if file_ids:
        lines.append(f'    class {",".join(file_ids)} file')

    content = '\n'.join(lines)
    output_path = os.path.join(OUTPUT_DIR, '99_COMPLETE_all_relations.mmd')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  [OK] ALL_RELATIONS - {len(node_to_id)} nodes, {len(calls_edges) + len(extends_edges) + len(defines_edges) + len(imports_edges)} edges")


def generate_complete_graph(db_path='kuzu'):
    """Generate overview summary with all relationship types"""
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)

    lines = ['%%{init: {\'theme\': \'base\', \'themeVariables\': { \'fontSize\': \'14px\'}}}%%']
    lines.append('graph TD')

    stats = {}

    for node_type in ['Function', 'Class', 'File', 'Community', 'Process']:
        result = conn.execute(f'MATCH (n:{node_type}) RETURN count(n)')
        count = result.get_next()[0]
        stats[node_type] = count

    result = conn.execute('''
        MATCH ()-[r]->()
        RETURN r.type as type, count(*) as cnt
        ORDER BY cnt DESC
    ''')
    rel_stats = {}
    for rel_type, cnt in result:
        rel_stats[rel_type] = cnt

    lines.append('    subgraph Nodes["{{{{chart}}}} Node Types"]')

    colors = {
        'Function': '#e1f5fe',
        'Class': '#fff9c4',
        'File': '#f3e5f5',
        'Community': '#e8f5e9',
        'Process': '#fff3e0'
    }

    for i, (node_type, count) in enumerate(stats.items()):
        color = colors.get(node_type, '#eeeeee')
        lines.append(f'        n{node_type}["{node_type}<br/>{count} nodes"]:::{node_type}')

    lines.append('    end')

    lines.append('    subgraph Relations["{{{{link}}}} Relation Types"]')

    rel_colors = {
        'CALLS': '#ffcdd2',
        'DEFINES': '#c8e6c9',
        'EXTENDS': '#bbdefb',
        'MEMBER_OF': '#ffe0b2',
        'IMPORTS': '#e1bee7',
        'CONTAINS': '#b2dfdb',
        'STEP_IN_PROCESS': '#ffccbc'
    }

    for i, (rel_type, count) in enumerate(rel_stats.items()):
        color = rel_colors.get(rel_type, '#eeeeee')
        lines.append(f'        r{rel_type.replace("_", "")}["{rel_type}<br/>{count} edges"]:::rel_{i}')

    lines.append('    end')

    lines.append('    subgraph Legend["{{{{book}}}} Legend"]')
    lines.append('        l1["CALLS - function calls"]')
    lines.append('        l2["DEFINES - definitions"]')
    lines.append('        l3["EXTENDS - inheritance"]')
    lines.append('        l4["MEMBER_OF - membership"]')
    lines.append('        l5["IMPORTS - imports"]')
    lines.append('        l6["CONTAINS - containment"]')
    lines.append('        l7["STEP_IN_PROCESS - process steps"]')
    lines.append('    end')

    lines.append('\n    %% Node styles')
    for node_type, color in colors.items():
        lines.append(f'    classDef {node_type} fill:{color},stroke:#333,stroke-width:2px')

    lines.append('    classDef rel fill:#ffffff,stroke:#333,stroke-width:1px')
    lines.append('    class rel_' + ',rel_'.join([str(i) for i in range(len(rel_stats))]) + ' rel')
    lines.append('    classDef legend fill:#fafafa,stroke:#999,stroke-width:1px,stroke-dasharray: 5 5')
    lines.append('    class l1,l2,l3,l4,l5,l6,l7 legend')

    content = '\n'.join(lines)
    output_path = os.path.join(OUTPUT_DIR, '00_OVERVIEW_summary.mmd')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  [OK] OVERVIEW - summary graph")

    index_lines = ['# GitNexus Kuzu Database - Mermaid Charts', '']
    index_lines.append(f'Generated: {os.path.basename(OUTPUT_DIR)}')
    index_lines.append('')
    index_lines.append('## {{{{chart}}}} Chart List')
    index_lines.append('')
    index_lines.append('| File | Description | Nodes/Edges |')
    index_lines.append('|------|-------------|-------------|')
    index_lines.append('| 00_OVERVIEW_summary.mmd | Overview summary | Stats |')
    index_lines.append(f'| 01_CALLS_functions.mmd | Function calls | - |')
    index_lines.append(f'| 02_EXTENDS_classes.mmd | Class inheritance | - |')
    index_lines.append(f'| 03_DEFINES_files.mmd | File definitions | - |')
    index_lines.append(f'| 04_MEMBER_OF_classes.mmd | Class members | - |')
    index_lines.append(f'| 05_IMPORTS_files.mmd | Import dependencies | - |')
    index_lines.append(f'| 06_CONTAINS.mmd | Containment | - |')
    index_lines.append(f'| 07_STEP_IN_PROCESS.mmd | Execution flows | - |')
    index_lines.append(f'| 08_COMMUNITY_modules.mmd | Functional modules | - |')
    index_lines.append(f'| 99_COMPLETE_all_relations.mmd | All relations | - |')
    index_lines.append('')
    index_lines.append('## How to View')
    index_lines.append('')
    index_lines.append('1. Visit https://mermaid.live')
    index_lines.append('2. Copy paste the .mmd file content')
    index_lines.append('')
    index_lines.append('## Database Statistics')
    index_lines.append('')
    index_lines.append('### Node Types')
    for node_type, count in stats.items():
        index_lines.append(f'- **{node_type}**: {count} nodes')
    index_lines.append('')
    index_lines.append('### Relation Types')
    for rel_type, count in rel_stats.items():
        index_lines.append(f'- **{rel_type}**: {count} edges')

    index_path = os.path.join(OUTPUT_DIR, 'README.md')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(index_lines))

    print(f"  [OK] README.md - index file")


if __name__ == '__main__':
    # OUTPUT_DIR is already set at module level

    db_path = find_kuzu_db()

    print("="*60)
    print("Kuzu to Mermaid Graph Converter")
    print("="*60)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print(f"Database: {db_path}\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("[1/10] Generating overview summary...")
    generate_complete_graph(db_path)

    print("\n[2/10] Generating function call graph...")
    generate_calls_graph(db_path, output_file='01_CALLS_functions.mmd', max_nodes=25)

    print("\n[3/10] Generating class inheritance graph...")
    generate_extends_graph(db_path)

    print("\n[4/10] Generating definition relationships...")
    generate_defines_graph(db_path)

    print("\n[5/10] Generating member relationships...")
    generate_member_of_graph(db_path)

    print("\n[6/10] Generating import dependencies...")
    generate_imports_graph(db_path)

    print("\n[7/10] Generating containment relationships...")
    generate_contains_graph(db_path)

    print("\n[8/10] Generating execution flows...")
    generate_process_graph(db_path)

    print("\n[9/10] Generating functional modules...")
    generate_community_graph(db_path)

    print("\n[10/10] Generating complete all-relations graph...")
    generate_all_relations_graph(db_path)

    print("\n" + "="*60)
    print("[OK] All done!")
    print(f"Output: {OUTPUT_DIR}")
    print("="*60)
