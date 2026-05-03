from langgraph.graph import StateGraph, END

from src.graph.state import BacklogGraphState
from src.graph.nodes import (
    analyze_requirement_node,
    generate_backlog_items_node,
    parse_response_node,
)


def build_backlog_graph():
    graph = StateGraph(BacklogGraphState)

    graph.add_node("analyze_requirement", analyze_requirement_node)
    graph.add_node("generate_backlog_items", generate_backlog_items_node)
    graph.add_node("parse_response", parse_response_node)

    graph.set_entry_point("analyze_requirement")

    graph.add_edge("analyze_requirement", "generate_backlog_items")
    graph.add_edge("generate_backlog_items", "parse_response")
    graph.add_edge("parse_response", END)

    return graph.compile()


backlog_graph = build_backlog_graph()
