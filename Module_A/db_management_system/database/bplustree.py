
import math
from graphviz import Digraph


class BPlusTreeNode:

    def __init__(self, order: int, is_leaf: bool = True):
        self.order     = order       
        self.is_leaf   = is_leaf    
        self.keys      = []         
        self.values    = []        
        self.children  = []         
        self.next      = None       

    def is_full(self) -> bool:
        return len(self.keys) >= self.order - 1

    def __repr__(self):
        kind = "Leaf" if self.is_leaf else "Internal"
        return f"{kind}Node(keys={self.keys})"



class BPlusTree:


    def __init__(self, order: int = 8):
        if order < 3:
            raise ValueError("B+ Tree order must be >= 3")
        self.order    = order
        self.root     = BPlusTreeNode(order, is_leaf=True)
        # Minimum keys a non-root node must hold
        self.min_keys = math.ceil(order / 2) - 1


    def search(self, key):
        #Time complexity: O(log n)
       
        leaf = self._find_leaf(self.root, key)
        for i, k in enumerate(leaf.keys):
            if k == key:
                return leaf.values[i]
        return None

    def _find_leaf(self, node: BPlusTreeNode, key) -> BPlusTreeNode:
 
        if node.is_leaf:
            return node
        i = 0
        while i < len(node.keys) and key >= node.keys[i]:
            i += 1
        return self._find_leaf(node.children[i], key)

    def _search(self, node: BPlusTreeNode, key):
        #Alias kept for compatibility.
        return self._find_leaf(node, key)

    #  Insert

    def insert(self, key, value):
  
        # If root is full, grow the tree upward
        if len(self.root.keys) == self.order - 1:
            old_root = self.root
            new_root = BPlusTreeNode(self.order, is_leaf=False)
            new_root.children.append(old_root)
            self._split_child(new_root, 0)
            self.root = new_root

        self._insert_non_full(self.root, key, value)

    def _insert_non_full(self, node: BPlusTreeNode, key, value):
        if node.is_leaf:
            # Binary-search insertion point
            i = 0
            while i < len(node.keys) and node.keys[i] < key:
                i += 1
            if i < len(node.keys) and node.keys[i] == key:
                node.values[i] = value        
                return
            node.keys.insert(i, key)
            node.values.insert(i, value)

        else:
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1
            if len(node.children[i].keys) == self.order - 1:
                self._split_child(node, i)
                if key >= node.keys[i]:
                    i += 1
            self._insert_non_full(node.children[i], key, value)

    def _split_child(self, parent: BPlusTreeNode, index: int):
        # Split a full child node and promote the median to parent
        # Leaf: copy-up , Internal: push-up
        child    = parent.children[index]
        new_node = BPlusTreeNode(self.order, is_leaf=child.is_leaf)

        if child.is_leaf:
            mid = self.order // 2                  
            new_node.keys   = child.keys[mid:]
            new_node.values = child.values[mid:]
            child.keys      = child.keys[:mid]
            child.values    = child.values[:mid]
            # Maintain leaf linked-list
            new_node.next = child.next
            child.next    = new_node
            promote_key   = new_node.keys[0]      

        else:
            mid = (self.order - 1) // 2            
            promote_key          = child.keys[mid]  
            new_node.keys        = child.keys[mid + 1:]
            new_node.children    = child.children[mid + 1:]
            child.keys           = child.keys[:mid]
            child.children       = child.children[:mid + 1]

        parent.keys.insert(index, promote_key)
        parent.children.insert(index + 1, new_node)


    #  Delete


    def delete(self, key):

        if self.root is None:
            return
        self._delete(self.root, key)
        # Shrink tree height when root becomes empty after a merge
        if not self.root.is_leaf and len(self.root.keys) == 0:
            self.root = self.root.children[0]

    def _delete(self, node: BPlusTreeNode, key):
       # Recursive helper for deletion.
        if node.is_leaf:
            if key in node.keys:
                idx = node.keys.index(key)
                node.keys.pop(idx)
                node.values.pop(idx)
            return

        # Find the child to descend into 
        i = 0
        while i < len(node.keys) and key >= node.keys[i]:
            i += 1

        # Ensure child has enough keys before descending 
        if len(node.children[i].keys) <= self.min_keys:
            self._fill_child(node, i)
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1

        self._delete(node.children[i], key)

        for j, k in enumerate(node.keys):
            if k == key:
                node.keys[j] = self._get_min_leaf_key(node.children[j + 1])
                break

    def _get_min_leaf_key(self, node: BPlusTreeNode):
        # Return the smallest key in the subtree rooted at `node`.
        while not node.is_leaf:
            node = node.children[0]
        return node.keys[0] if node.keys else None

    def _fill_child(self, node: BPlusTreeNode, index: int):
        left_sib  = node.children[index - 1] if index > 0 else None
        right_sib = node.children[index + 1] if index < len(node.children) - 1 else None

        if left_sib and len(left_sib.keys) > self.min_keys:
            self._borrow_from_prev(node, index)
        elif right_sib and len(right_sib.keys) > self.min_keys:
            self._borrow_from_next(node, index)
        else:
            # Merge: prefer merging with right sibling
            if right_sib is not None:
                self._merge(node, index)
            else:
                self._merge(node, index - 1)

    def _borrow_from_prev(self, node: BPlusTreeNode, index: int):
        # Rotate a key from the left sibling through the parent.
        child   = node.children[index]
        sibling = node.children[index - 1]

        if child.is_leaf:
            # Take the last key/value from left sibling
            child.keys.insert(0, sibling.keys[-1])
            child.values.insert(0, sibling.values[-1])
            sibling.keys.pop()
            sibling.values.pop()
            node.keys[index - 1] = child.keys[0]   
        else:
            # Bring parent separator down; push sibling's last key up
            child.keys.insert(0, node.keys[index - 1])
            child.children.insert(0, sibling.children[-1])
            node.keys[index - 1] = sibling.keys[-1]
            sibling.keys.pop()
            sibling.children.pop()

    def _borrow_from_next(self, node: BPlusTreeNode, index: int):
        # Rotate a key from the right sibling through the parent.
        child   = node.children[index]
        sibling = node.children[index + 1]

        if child.is_leaf:
            # Take the first key/value from right sibling
            child.keys.append(sibling.keys[0])
            child.values.append(sibling.values[0])
            sibling.keys.pop(0)
            sibling.values.pop(0)
            node.keys[index] = sibling.keys[0]      # Update separator in parent
        else:
            # Bring parent separator down; push sibling's first key up
            child.keys.append(node.keys[index])
            child.children.append(sibling.children[0])
            node.keys[index] = sibling.keys[0]
            sibling.keys.pop(0)
            sibling.children.pop(0)

    def _merge(self, node: BPlusTreeNode, index: int):
        left  = node.children[index]
        right = node.children[index + 1]

        if left.is_leaf:
            left.keys.extend(right.keys)
            left.values.extend(right.values)
            left.next = right.next                   # Maintain linked-list
        else:
            # Bring the separator key down from parent
            left.keys.append(node.keys[index])
            left.keys.extend(right.keys)
            left.children.extend(right.children)

        node.keys.pop(index)
        node.children.pop(index + 1)

    #  Update


    def update(self, key, new_value) -> bool:
        
        #Returns True on success. Time complexity: O(log n)
        
        leaf = self._find_leaf(self.root, key)
        for i, k in enumerate(leaf.keys):
            if k == key:
                leaf.values[i] = new_value
                return True
        return False

    #  Range Query
   
    def range_query(self, start_key, end_key) -> list:
        # Returns all key-value pairs in the inclusive range [start_key, end_key]
        # using leaf links for efficient traversal (O(log n + k))
        result = []
        leaf = self._find_leaf(self.root, start_key)
        while leaf is not None:
            for i, k in enumerate(leaf.keys):
                if k > end_key:
                    return result
                if k >= start_key:
                    result.append((k, leaf.values[i]))
            leaf = leaf.next
        return result

    #  Get All


    def get_all(self) -> list:
 
        result = []
        # Navigate to leftmost leaf
        node = self.root
        while not node.is_leaf:
            node = node.children[0]
        # Walk the linked list
        while node is not None:
            for i, k in enumerate(node.keys):
                result.append((k, node.values[i]))
            node = node.next
        return result

    def _get_all(self, node: BPlusTreeNode, result: list):

        if node.is_leaf:
            for i, k in enumerate(node.keys):
                result.append((k, node.values[i]))
        else:
            for child in node.children:
                self._get_all(child, result)


    #-----------------------------Visualisation---------------------------------------------
    
    def visualize_tree(self, filename: str = None):

        dot = Digraph(comment="B+ Tree")
        dot.attr(
            rankdir="TB",
            splines="curved",
            nodesep="0.6",
            ranksep="0.8",
            bgcolor="white",
        )
        dot.attr("node", shape="plaintext", fontname="Arial", fontsize="13")
        dot.attr("edge", arrowsize="0.8")

        if self.root and self.root.keys:
            self._add_nodes(dot, self.root)
            self._add_edges(dot, self.root)

        if filename:
            dot.render(filename, format="png", cleanup=True, view=False)

        return dot


    _INTERNAL_BG  = "#AED6F1"  
    _INTERNAL_BOR = "#1A5276"   
    _LEAF_BG      = "#ABEBC6"  
    _LEAF_BOR     = "#1E8449"   

    @classmethod
    def _html_internal(cls, node: "BPlusTreeNode") -> str:

        n = len(node.keys)

        cells = ""
        # Left anchor port
        cells += (
            f'<TD PORT="c0" WIDTH="1" HEIGHT="1" BORDER="0"> </TD>'
        )
        for i, k in enumerate(node.keys):
            cells += (
                f'<TD BGCOLOR="{cls._INTERNAL_BG}" BORDER="1" '
                f'STYLE="ROUNDED" CELLPADDING="6"><B>{k}</B></TD>'
            )
            cells += (
                f'<TD PORT="c{i+1}" WIDTH="1" HEIGHT="1" BORDER="0"> </TD>'
            )
        return (
            f'<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="2" CELLPADDING="0">'
            f"<TR>{cells}</TR></TABLE>>"
        )

    @classmethod
    def _html_leaf(cls, node: "BPlusTreeNode") -> str:

        cells = ""
        for i, k in enumerate(node.keys):
            cells += (
                f'<TD BGCOLOR="{cls._LEAF_BG}" BORDER="1" '
                f'STYLE="ROUNDED" CELLPADDING="6">{k}</TD>'
            )
        cells += '<TD PORT="nx" WIDTH="1" BORDER="0"> </TD>'
        return (
            f'<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="2" CELLPADDING="0">'
            f"<TR>{cells}</TR></TABLE>>"
        )

    def _add_nodes(self, dot: Digraph, node: BPlusTreeNode):
        node_id = str(id(node))

        if node.is_leaf:
            dot.node(node_id, label=self._html_leaf(node))
        else:
            dot.node(node_id, label=self._html_internal(node))
            for child in node.children:
                self._add_nodes(dot, child)

    def _add_edges(self, dot: Digraph, node: BPlusTreeNode):
        node_id = str(id(node))

        if not node.is_leaf:
            n = len(node.keys)
            for idx, child in enumerate(node.children):
                child_id = str(id(child))
                # Distribute children evenly across the port anchors
                port = f"c{idx}"
                dot.edge(
                    f"{node_id}:{port}",
                    child_id,
                    color="black",
                    penwidth="1.5",
                )
                self._add_edges(dot, child)

        if node.is_leaf and node.next is not None:
            next_id = str(id(node.next))
            dot.edge(
                f"{node_id}:nx",
                next_id,
                style="dashed",
                color="#1E8449",
                penwidth="1.8",
                arrowhead="normal",
                constraint="false",
            )

    #  Utility
   

    def height(self) -> int:
        h, node = 1, self.root
        while not node.is_leaf:
            node = node.children[0]
            h += 1
        return h

    def __len__(self) -> int:
        return len(self.get_all())

    def __contains__(self, key) -> bool:
        return self.search(key) is not None

    def __repr__(self):
        return f"BPlusTree(order={self.order}, size={len(self)}, height={self.height()})"
