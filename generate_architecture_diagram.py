
import graphviz

def generate_architecture_diagram():
    dot = graphviz.Digraph(comment='Multi-Agent Baseline Factory Architecture', format='png')
    dot.attr(rankdir='LR', size='12,8', dpi='300')
    
    # 1. Orchestration Layer
    with dot.subgraph(name='cluster_0') as c:
        c.attr(style='filled', color='lightgrey', label='Orchestration Layer')
        c.node('Orchestrator', 'Orchestrator Agent\n(Workflow Manager)', shape='hexagon', style='filled', color='white')
        
    # 2. Intake Layer
    with dot.subgraph(name='cluster_1') as c:
        c.attr(style='filled', color='#e1f5fe', label='Intake & Extraction Layer')
        c.node('Intake', 'Intake Agent\n(File Scanner)', shape='box', style='filled', color='white')
        c.node('Schema', 'Schema Agent\n(Header Mapper)', shape='box', style='filled', color='white')
        
    # 3. Standardization & Enrichment Layer
    with dot.subgraph(name='cluster_2') as c:
        c.attr(style='filled', color='#fff9c4', label='Standardization & Enrichment')
        c.node('Standardizer', 'Standardizer Agent\n(Canonical Record)', shape='box', style='filled', color='white')
        c.node('RateCard', 'Rate Card Agent\n(Cost Imputation)', shape='box', style='filled', color='white')
        c.node('QA', 'QA Agent\n(Anomaly Detection)', shape='box', style='filled', color='white')

    # 4. Analytics Layer
    with dot.subgraph(name='cluster_3') as c:
        c.attr(style='filled', color='#e0f2f1', label='Analytics Layer')
        c.node('Aggregator', 'Aggregator Agent\n(Baseline Table)', shape='box', style='filled', color='white')
        c.node('Analyst', 'Analyst Agent\n(Mix/Rate Analysis)', shape='box', style='filled', color='white')
        c.node('Benchmark', 'Benchmark Agent\n(Market Comp)', shape='box', style='filled', color='white')

    # 5. Strategic Layer
    with dot.subgraph(name='cluster_4') as c:
        c.attr(style='filled', color='#f3e5f5', label='Strategic Layer')
        c.node('Simulator', 'Simulator Agent\n(Whaf-If Scenarios)', shape='box', style='filled', color='white')
        c.node('Advisor', 'Advisor Agent\n(Recommendations)', shape='box', style='filled', color='white')
        c.node('Composer', 'Report Composer\n(Final Output)', shape='component', style='filled', color='gold')

    # Edges (Data Flow)
    dot.edge('Orchestrator', 'Intake', label='Start Job')
    dot.edge('Intake', 'Schema', label='Raw Data')
    dot.edge('Schema', 'Standardizer', label='Mapping')
    dot.edge('Standardizer', 'RateCard', label='Missing Cost?')
    dot.edge('RateCard', 'Standardizer', label='Imputed Rates')
    dot.edge('Standardizer', 'QA', label='Canonical Data')
    dot.edge('QA', 'Aggregator', label='Clean Records')
    dot.edge('Aggregator', 'Analyst', label='Baseline v1')
    dot.edge('Aggregator', 'Benchmark', label='Effective Rates')
    dot.edge('Analyst', 'Simulator', label='Trends/Mix')
    dot.edge('Benchmark', 'Simulator', label='Market Gaps')
    dot.edge('Simulator', 'Advisor', label='Savings Potential')
    dot.edge('Advisor', 'Composer', label='Oppty Register')
    
    output_path = r'c:\Users\John\.gemini\antigravity\playground\multiagent-baseline-lt\multi_agent_architecture_v2'
    dot.render(output_path, view=False)
    print(f"Architecture diagram generated at: {output_path}.png")

if __name__ == "__main__":
    try:
        generate_architecture_diagram()
    except Exception as e:
        print(f"Graphviz error: {e}")
        # Graphviz binary might not be in path, but let's try.
