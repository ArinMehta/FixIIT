"""
bplustree.py
------------
Full B+ Tree implementation with:
  - Insertion (with automatic node splitting)
  - Deletion  (with merging and redistribution)
  - Exact search
  - Range queries
  - Value (record) storage at leaf nodes
  - Graphviz visualisation
"""

from __future__ import annotations
from typing import Any, List, Optional, Tuple
import graphviz


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

class BPlusTreeNode:
    def __init__(self, order, is_leaf=True):
        self.order = order
        self.is_leaf = is_leaf
        self.keys = []
        self.values = []      # leaf nodes only — parallel to keys
        self.children = []    # internal nodes only — child pointers
        self.next = None
        self.parent = None    # parent pointer for O(1) parent lookup

    def is_full(self):
        return len(self.keys) >= self.order - 1


# ---------------------------------------------------------------------------
# B+ Tree
# ---------------------------------------------------------------------------

class BPlusTree:
    def __init__(self, order=8):
        self.order = order
        self.max_keys = order - 1           # max keys per node
        self.min_keys = (order - 1) // 2    # min keys per non-root node
        self.root = BPlusTreeNode(order)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def insert(self, key: Any, value: Any) -> None:
        """Insert a key-value pair into the tree."""
        leaf = self._find_leaf(self.root, key)

        # If key already exists → append value to existing list
        if key in leaf.keys:
            idx = leaf.keys.index(key)
            leaf.values[idx].append(value)   # FIX: was leaf.children[idx]
            return

        # Insert in sorted order
        self._insert_in_leaf(leaf, key, value)

        if len(leaf.keys) > self.max_keys:
            self._split_leaf(leaf)

    def delete(self, key: Any) -> bool:
        """
        Delete a key from the tree.
        Returns True if the key was found and deleted, False otherwise.
        """
        leaf = self._find_leaf(self.root, key)
        if key not in leaf.keys:
            return False

        idx = leaf.keys.index(key)
        leaf.keys.pop(idx)
        leaf.values.pop(idx)

        # Fix underflow
        if leaf is not self.root and len(leaf.keys) < self.min_keys:
            self._fix_leaf_underflow(leaf)
        elif leaf is self.root and len(leaf.keys) == 0:
            self.root = BPlusTreeNode(self.order, is_leaf=True)  # FIX: pass order

        return True

    def search(self, key: Any) -> Optional[List[Any]]:
        """
        Exact search. Returns the list of values stored under `key`,
        or None if the key does not exist.
        """
        leaf = self._find_leaf(self.root, key)
        if key in leaf.keys:
            idx = leaf.keys.index(key)
            return leaf.values[idx]
        return None

    def range_query(self, low: Any, high: Any) -> List[Tuple[Any, Any]]:
        """
        Return all (key, value_list) pairs where low <= key <= high.
        Uses the leaf linked list for efficiency.
        """
        results: List[Tuple[Any, Any]] = []
        leaf = self._find_leaf(self.root, low)
        while leaf is not None:
            for i, k in enumerate(leaf.keys):
                if k > high:
                    return results
                if k >= low:
                    results.append((k, leaf.values[i]))
            leaf = leaf.next
        return results

    def get_all(self) -> List[Tuple[Any, Any]]:
        """Return all (key, value_list) pairs in sorted order."""
        results: List[Tuple[Any, Any]] = []
        leaf = self._leftmost_leaf()
        while leaf is not None:
            for i, k in enumerate(leaf.keys):
                results.append((k, leaf.values[i]))
            leaf = leaf.next
        return results

    def update(self, key: Any, new_value: Any) -> bool:
        """
        Replace the entire value list for `key` with [new_value].
        Returns True on success, False if key not found.
        """
        leaf = self._find_leaf(self.root, key)
        if key not in leaf.keys:
            return False
        idx = leaf.keys.index(key)
        leaf.values[idx] = [new_value]
        return True

    # ------------------------------------------------------------------
    # Visualisation
    # ------------------------------------------------------------------

    def visualize_tree(self, filename=None):
        """
        Visualize the tree using Graphviz.
        Returns the Digraph object (caller can use .pipe(format='svg')).
        Optionally saves a PNG if filename is provided.
        """
        dot = graphviz.Digraph(
            "BPlusTree",
            node_attr={"shape": "record", "fontname": "Helvetica"},
            graph_attr={"rankdir": "TB", "splines": "line"},
        )

        def _node_name(n: BPlusTreeNode) -> str:
            return f"node{id(n)}"

        def _add_node(n: BPlusTreeNode) -> None:
            name = _node_name(n)
            if n.is_leaf:
                label = " | ".join(str(k) for k in n.keys)
                dot.node(name, label=label, shape="box",
                         style="filled", fillcolor="#fffacd")
            else:
                parts = []
                for i, k in enumerate(n.keys):
                    parts.append(f"<c{i}> ")
                    parts.append(f"<k{i}> {k}")
                parts.append(f"<c{len(n.keys)}> ")
                label = " | ".join(parts)
                dot.node(name, label=f"{{ {label} }}",
                         style="filled", fillcolor="#d0e8ff")

            if not n.is_leaf:
                for i, child in enumerate(n.children):
                    _add_node(child)
                    dot.edge(f"{name}:c{i}", _node_name(child))

        _add_node(self.root)

        # Draw linked list between leaves
        leaves = self._all_leaves()
        for i in range(len(leaves) - 1):
            dot.edge(
                _node_name(leaves[i]),
                _node_name(leaves[i + 1]),
                style="dashed",
                color="orange",
                constraint="false",
            )

        if filename:
            dot.render(filename, format="png", cleanup=True)
        return dot

    # ------------------------------------------------------------------
    # Internal helpers – traversal
    # ------------------------------------------------------------------

    def _find_leaf(self, node: BPlusTreeNode, key: Any) -> BPlusTreeNode:
        """Traverse down to the leaf that should contain `key`."""
        if node.is_leaf:
            return node
        for i, k in enumerate(node.keys):
            if key < k:
                return self._find_leaf(node.children[i], key)
        return self._find_leaf(node.children[-1], key)

    def _leftmost_leaf(self) -> BPlusTreeNode:
        node = self.root
        while not node.is_leaf:
            node = node.children[0]
        return node

    def _all_leaves(self) -> List[BPlusTreeNode]:
        leaves = []
        node = self._leftmost_leaf()
        while node is not None:
            leaves.append(node)
            node = node.next
        return leaves

    def _find_parent(
        self, current: BPlusTreeNode, target: BPlusTreeNode
    ) -> Optional[BPlusTreeNode]:
        if current.is_leaf:
            return None
        if target in current.children:
            return current
        for child in current.children:
            result = self._find_parent(child, target)
            if result:
                return result
        return None

    # ------------------------------------------------------------------
    # Internal helpers – insertion
    # ------------------------------------------------------------------

    def _insert_in_leaf(self, leaf: BPlusTreeNode, key: Any, value: Any) -> None:
        for i, k in enumerate(leaf.keys):
            if key < k:
                leaf.keys.insert(i, key)
                leaf.values.insert(i, [value])
                return
        leaf.keys.append(key)
        leaf.values.append([value])

    def _split_leaf(self, leaf: BPlusTreeNode) -> None:
        mid = (self.max_keys + 1) // 2      # FIX: was (self.order - 1) // 2
        new_leaf = BPlusTreeNode(self.order, is_leaf=True)
        new_leaf.keys = leaf.keys[mid:]
        new_leaf.values = leaf.values[mid:]
        leaf.keys = leaf.keys[:mid]
        leaf.values = leaf.values[:mid]

        # Maintain linked list
        new_leaf.next = leaf.next
        leaf.next = new_leaf

        push_up_key = new_leaf.keys[0]
        self._insert_in_parent(leaf, push_up_key, new_leaf)

    def _split_internal(self, node: BPlusTreeNode) -> None:
        mid = self.max_keys // 2
        push_up_key = node.keys[mid]

        new_node = BPlusTreeNode(self.order, is_leaf=False)  # FIX: pass order
        new_node.keys = node.keys[mid + 1:]
        new_node.children = node.children[mid + 1:]
        for child in new_node.children:
            child.parent = new_node

        node.keys = node.keys[:mid]
        node.children = node.children[:mid + 1]

        self._insert_in_parent(node, push_up_key, new_node)

    def _insert_in_parent(self, left: BPlusTreeNode, key: Any,
                           right: BPlusTreeNode) -> None:
        if left is self.root:
            new_root = BPlusTreeNode(self.order, is_leaf=False)  # FIX: pass order
            new_root.keys = [key]
            new_root.children = [left, right]
            left.parent = new_root
            right.parent = new_root
            self.root = new_root
            return

        parent = left.parent   # FIX: use stored pointer instead of _find_parent
        if parent is None:
            raise RuntimeError("Parent not found – tree is inconsistent")

        right.parent = parent
        for i, k in enumerate(parent.keys):
            if key < k:
                parent.keys.insert(i, key)
                parent.children.insert(i + 1, right)
                break
        else:
            parent.keys.append(key)
            parent.children.append(right)

        if len(parent.keys) > self.max_keys:
            self._split_internal(parent)

    # ------------------------------------------------------------------
    # Internal helpers – deletion
    # ------------------------------------------------------------------

    def _fix_leaf_underflow(self, leaf: BPlusTreeNode) -> None:
        parent = self._find_parent(self.root, leaf)
        if parent is None:
            return

        idx = parent.children.index(leaf)

        # Try to borrow from left sibling
        if idx > 0:
            left_sib = parent.children[idx - 1]
            if len(left_sib.keys) > self.min_keys:
                leaf.keys.insert(0, left_sib.keys.pop())
                leaf.values.insert(0, left_sib.values.pop())
                parent.keys[idx - 1] = leaf.keys[0]
                return

        # Try to borrow from right sibling
        if idx < len(parent.children) - 1:
            right_sib = parent.children[idx + 1]
            if len(right_sib.keys) > self.min_keys:
                leaf.keys.append(right_sib.keys.pop(0))
                leaf.values.append(right_sib.values.pop(0))
                parent.keys[idx] = right_sib.keys[0]
                return

        # Merge
        if idx > 0:
            left_sib = parent.children[idx - 1]
            left_sib.keys.extend(leaf.keys)
            left_sib.values.extend(leaf.values)
            left_sib.next = leaf.next
            parent.keys.pop(idx - 1)
            parent.children.pop(idx)
        else:
            right_sib = parent.children[idx + 1]
            leaf.keys.extend(right_sib.keys)
            leaf.values.extend(right_sib.values)
            leaf.next = right_sib.next
            parent.keys.pop(idx)
            parent.children.pop(idx + 1)

        if parent is self.root:
            if len(self.root.keys) == 0:
                self.root = parent.children[0]
        elif len(parent.keys) < self.min_keys:
            self._fix_internal_underflow(parent)

    def _fix_internal_underflow(self, node: BPlusTreeNode) -> None:
        parent = self._find_parent(self.root, node)
        if parent is None:
            return

        idx = parent.children.index(node)

        # Borrow from left sibling
        if idx > 0:
            left_sib = parent.children[idx - 1]
            if len(left_sib.keys) > self.min_keys:
                node.keys.insert(0, parent.keys[idx - 1])
                parent.keys[idx - 1] = left_sib.keys.pop()
                borrowed_child = left_sib.children.pop()
                borrowed_child.parent = node
                node.children.insert(0, borrowed_child)
                return

        # Borrow from right sibling
        if idx < len(parent.children) - 1:
            right_sib = parent.children[idx + 1]
            if len(right_sib.keys) > self.min_keys:
                node.keys.append(parent.keys[idx])
                parent.keys[idx] = right_sib.keys.pop(0)
                borrowed_child = right_sib.children.pop(0)
                borrowed_child.parent = node
                node.children.append(borrowed_child)
                return

        # Merge
        if idx > 0:
            left_sib = parent.children[idx - 1]
            left_sib.keys.append(parent.keys.pop(idx - 1))
            left_sib.keys.extend(node.keys)
            for child in node.children:
                child.parent = left_sib
            left_sib.children.extend(node.children)
            parent.children.pop(idx)
        else:
            right_sib = parent.children[idx + 1]
            node.keys.append(parent.keys.pop(idx))
            node.keys.extend(right_sib.keys)
            for child in right_sib.children:
                child.parent = node
            node.children.extend(right_sib.children)
            parent.children.pop(idx + 1)

        if parent is self.root:
            if len(self.root.keys) == 0:
                self.root = parent.children[0]
        elif len(parent.keys) < self.min_keys:
            self._fix_internal_underflow(parent)