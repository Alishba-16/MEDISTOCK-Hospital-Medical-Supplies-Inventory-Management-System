"""
================================================================================
MEDISTOCK — HOSPITAL MEDICAL SUPPLIES INVENTORY MANAGEMENT SYSTEM
MODULE 1 (CORE DSA): Manual Singly Linked List Queue Implementation
Course: Data Structures & Algorithms (Group C — Queue Implementation)
================================================================================
Strictly implements a manual `Node` class and `Queue` class from scratch using
explicit `front` and `rear` pointers (no Python `deque` or `queue.Queue`).

Required Methods Implemented:
  1. enqueue(item)    : Insert element at rear — O(1)
  2. dequeue()        : Remove and return element from front — O(1)
  3. peek()           : Return front element without removing — O(1)
  4. is_empty()       : Check whether queue is empty — O(1)
  5. size()           : Return number of elements in queue — O(1)
  6. display()        : Return all elements from FRONT to REAR — O(n)
  7. search(id)       : Find element(s) by ID or keyword without altering order — O(n)
  8. delete(id)       : Remove a specific element while preserving FIFO order — O(n)
  9. update(id, data) : Update a specific element in-place while preserving order — O(n)

Edge Cases Handled:
  - Empty queue (`front is None` and `rear is None`)
  - Single-element queue (`front is rear`)
  - Multiple elements
  - Removing the last element (resets both `front` and `rear` to `None`)
  - Updating or deleting a front, middle, or rear element
  - Maintaining accurate `front` and `rear` pointers after every operation
================================================================================
"""

from __future__ import annotations
import random
import time
from typing import Any, Callable, Dict, List, Optional


class Node:
    """
    Singly Linked List Node for the manual Queue data structure.
    Holds `data` and a `next` reference to the subsequent Node in the queue.
    """

    def __init__(self, data: Any, node_id: Optional[str] = None, memory_address: Optional[str] = None):
        self.data: Any = data
        self.next: Optional[Node] = None
        self.id: str = (
            node_id
            or self._extract_id(data)
            or f"NODE-{int(time.time() * 1000) % 100000}-{random.randint(100, 999)}"
        )
        self.memory_address: str = memory_address or f"0x{random.randint(0x7F1000, 0x7FFFFF):06X}"

    @staticmethod
    def _extract_id(data: Any) -> Optional[str]:
        if isinstance(data, dict):
            for key in ("id", "batch_id", "request_id", "req_id"):
                if key in data and data[key] is not None:
                    return str(data[key])
        return None

    def __repr__(self) -> str:
        next_addr = self.next.memory_address if self.next else "NULL"
        return f"<Node id={self.id} addr={self.memory_address} next={next_addr}>"


# Alias for convenience
QueueNode = Node


class Queue:
    """
    Manually implemented FIFO Queue backed by a Singly Linked List (`Node`).
    Maintains explicit `front` and `rear` pointers.
    """

    def __init__(self, name: str = "LinkedListQueue"):
        self.name: str = name
        self.front: Optional[Node] = None
        self.rear: Optional[Node] = None
        self._size: int = 0
        self.last_operation: str = f"Initialized {self.name} (front=NULL, rear=NULL)"

    @staticmethod
    def _matches_id(item: Any, target_id: Any) -> bool:
        """Checks if `item` matches `target_id` by exact ID field or callable predicate."""
        if callable(target_id):
            return bool(target_id(item))
        if isinstance(item, dict):
            target_str = str(target_id).strip().upper()
            for key in ("id", "batch_id", "request_id", "req_id"):
                if key in item and str(item[key]).strip().upper() == target_str:
                    return True
        return str(item).strip().upper() == str(target_id).strip().upper()

    # =========================================================================
    # 1. enqueue(item) — Insert at rear: O(1)
    # =========================================================================
    def enqueue(self, item: Any) -> Node:
        """
        Creates a new Node and inserts it at the REAR of the queue in O(1) time.
        Handles both empty queue (`front = rear = new_node`) and non-empty queue.
        """
        new_node = Node(item)
        if self.is_empty():
            self.front = new_node
            self.rear = new_node
        else:
            assert self.rear is not None
            self.rear.next = new_node
            self.rear = new_node

        self._size += 1
        self.last_operation = f"enqueue({new_node.id}) -> inserted at REAR ({new_node.memory_address}) [O(1)]"
        return new_node

    # =========================================================================
    # 2. dequeue() — Remove from front: O(1)
    # =========================================================================
    def dequeue(self) -> Optional[Any]:
        """
        Removes and returns the FRONT element of the queue in O(1) time.
        If removing the last element, resets both `front` and `rear` to `None`.
        """
        if self.is_empty() or self.front is None:
            self.last_operation = "dequeue() on empty queue -> None [O(1)]"
            return None

        removed_node = self.front
        removed_data = removed_node.data

        # Advance front pointer to the next node
        self.front = removed_node.next

        # Edge case: removing the last element from a single-element queue
        if self.front is None:
            self.rear = None

        removed_node.next = None
        self._size -= 1
        next_front = self.front.id if self.front else "NULL"
        self.last_operation = f"dequeue() -> removed {removed_node.id}; new FRONT={next_front} [O(1)]"
        return removed_data

    # =========================================================================
    # 3. peek() — Return front element without removing: O(1)
    # =========================================================================
    def peek(self) -> Optional[Any]:
        """Returns the data stored at the FRONT node without modifying the queue."""
        if self.is_empty() or self.front is None:
            self.last_operation = "peek() on empty queue -> None [O(1)]"
            return None
        self.last_operation = f"peek() -> FRONT is {self.front.id} ({self.front.memory_address}) [O(1)]"
        return self.front.data

    # =========================================================================
    # 4. is_empty() — Check whether queue is empty: O(1)
    # =========================================================================
    def is_empty(self) -> bool:
        """Returns True if the queue contains no elements (`front is None`)."""
        return self.front is None or self._size == 0

    # =========================================================================
    # 5. size() — Return queue length: O(1)
    # =========================================================================
    def size(self) -> int:
        """Returns the total number of elements currently in the queue."""
        return self._size

    # =========================================================================
    # 6. display() — Return all elements from FRONT to REAR: O(n)
    # =========================================================================
    def display(self) -> List[Any]:
        """Traverses the linked list from `front` to `rear` and returns all element data."""
        items: List[Any] = []
        current = self.front
        while current is not None:
            items.append(current.data)
            current = current.next
        self.last_operation = f"display() -> traversed {len(items)} node(s) from FRONT to REAR [O(n)]"
        return items

    def display_nodes(self) -> List[Dict[str, Any]]:
        """
        Returns metadata for every node in the linked list from FRONT to REAR
        so the GUI can draw the exact `Node -> next` pointer chain.
        """
        nodes_info: List[Dict[str, Any]] = []
        current = self.front
        idx = 1
        while current is not None:
            nodes_info.append({
                "position": idx,
                "id": current.id,
                "memory_address": current.memory_address,
                "next_address": current.next.memory_address if current.next else "NULL",
                "is_front": current is self.front,
                "is_rear": current is self.rear,
                "data": current.data,
            })
            current = current.next
            idx += 1
        return nodes_info

    # =========================================================================
    # 7. search(id_or_query) — Find element without changing queue order: O(n)
    # =========================================================================
    def search(self, query: Any) -> Optional[Any]:
        """
        Searches for an element by ID (or predicate) without changing queue order.
        Returns the matching item's `data` dictionary (or `None` if not found).
        """
        if self.is_empty():
            self.last_operation = f"search('{query}') on empty queue -> None [O(n)]"
            return None

        current = self.front
        pos = 1
        query_str = str(query).strip().lower()

        while current is not None:
            if self._matches_id(current.data, query):
                self.last_operation = f"search('{query}') -> found {current.id} at position #{pos} [O(n)]"
                return current.data
            if isinstance(current.data, dict) and query_str:
                for val in current.data.values():
                    if query_str in str(val).lower():
                        self.last_operation = f"search('{query}') -> matched {current.id} at position #{pos} [O(n)]"
                        return current.data
            current = current.next
            pos += 1

        self.last_operation = f"search('{query}') -> not found [O(n)]"
        return None

    def search_all(self, query: str) -> List[Dict[str, Any]]:
        """Returns all matching nodes (with position and pointer metadata) for GUI filtering."""
        q = str(query).strip().lower()
        results: List[Dict[str, Any]] = []
        current = self.front
        pos = 1
        while current is not None:
            matched = False
            if not q:
                matched = True
            elif isinstance(current.data, dict):
                for v in current.data.values():
                    if q in str(v).lower():
                        matched = True
                        break
            elif q in str(current.data).lower():
                matched = True

            if matched:
                results.append({
                    "position": pos,
                    "id": current.id,
                    "memory_address": current.memory_address,
                    "next_address": current.next.memory_address if current.next else "NULL",
                    "is_front": current is self.front,
                    "is_rear": current is self.rear,
                    "data": current.data,
                })
            current = current.next
            pos += 1
        return results

    # =========================================================================
    # 8. delete(id) — Remove a selected element while preserving order: O(n)
    # =========================================================================
    def delete(self, target_id: Any) -> Optional[Any]:
        """
        Removes the node matching `target_id` while preserving the relative FIFO
        order of all remaining nodes.
        Correctly handles:
          - Empty queue
          - Deleting the only node in a single-element queue (`front` and `rear` -> `None`)
          - Deleting the `front` node
          - Deleting a middle node
          - Deleting the `rear` node (`rear` updated to `previous` node)
        """
        if self.is_empty() or self.front is None:
            self.last_operation = f"delete('{target_id}') on empty queue -> None [O(n)]"
            return None

        current: Optional[Node] = self.front
        previous: Optional[Node] = None

        while current is not None:
            if self._matches_id(current.data, target_id) or current.id.upper() == str(target_id).strip().upper():
                removed_data = current.data

                # Case A: Removing the FRONT node
                if previous is None:
                    self.front = current.next
                    if self.front is None:
                        # Queue had only 1 element and is now empty
                        self.rear = None
                else:
                    # Case B: Removing a middle or REAR node
                    previous.next = current.next
                    if current.next is None:
                        # Removed node was the REAR node -> update rear pointer
                        self.rear = previous

                current.next = None
                self._size -= 1
                self.last_operation = f"delete('{target_id}') -> unlinked node {current.id}; size={self._size} [O(n)]"
                return removed_data

            previous = current
            current = current.next

        self.last_operation = f"delete('{target_id}') -> target not found [O(n)]"
        return None

    # =========================================================================
    # 9. update(id, data) — Update an element while preserving order: O(n)
    # =========================================================================
    def update(self, target_id: Any, updated_data: Any) -> bool:
        """
        Finds the node matching `target_id` and updates its payload in-place
        without altering its position or pointers in the linked list.
        Handles front, middle, and rear nodes identically.
        """
        if self.is_empty() or self.front is None:
            self.last_operation = f"update('{target_id}') on empty queue -> False [O(n)]"
            return False

        current = self.front
        pos = 1
        while current is not None:
            if self._matches_id(current.data, target_id) or current.id.upper() == str(target_id).strip().upper():
                if isinstance(current.data, dict) and isinstance(updated_data, dict):
                    current.data.update(updated_data)
                else:
                    current.data = updated_data
                self.last_operation = f"update('{target_id}') -> updated node at position #{pos} in-place [O(n)]"
                return True
            current = current.next
            pos += 1

        self.last_operation = f"update('{target_id}') -> target not found [O(n)]"
        return False

    def clear(self) -> None:
        """Resets the queue to an empty state."""
        self.front = None
        self.rear = None
        self._size = 0
        self.last_operation = "Cleared queue (front=NULL, rear=NULL)"

    def __len__(self) -> int:
        return self._size


# Alias for compatibility
LinkedListQueue = Queue
