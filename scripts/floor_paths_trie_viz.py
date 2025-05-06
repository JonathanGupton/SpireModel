import collections
import pickle
import uuid  # For unique node IDs in visualization

import marisa_trie
import graphviz

# --- Configuration ---

# Choose a byte representation for None that won't clash with your actual strings
# Using a descriptive string encoded to bytes.
NONE_REPR_BYTES = b"[NONE]"

# Choose a separator byte that won't appear in your encoded element representations
# Null byte is usually a safe choice.
SEPARATOR_BYTE = b"\x00"

# --- Data Cleaning and Preparation ---

# Example Counter data (assuming correction of typos from the prompt)
# NOTE: The keys in the prompt example are very long and somewhat garbled.
# I'm using shorter, cleaner examples based on the pattern, plus the originals
# (assuming the parts like ")2(" were metadata, not part of the key tuple).
# You should replace this with your actual large Counter object.
# data = collections.Counter({
#     (): 5024008,
#     ('M',): 100,
#     ('R',): 50,
#     ('M', 'M'): 20,
#     ('M', 'R'): 15,
#     ('M', None, 'T'): 5,
#     ('R', 'B', None, 'M'): 8,
#     # Example from prompt (assuming cleanup)
#     ('M', 'M', '\n', 'M', 'M', 'R', 'M', '?', 'T', 'R', '?', 'M', 'R', 'M', 'R', 'B', None, 'M', '?', '?', 'M', 'M', 'R', 'M', '\n', 'M', 'M', 'R', 'M', '?', 'T', 'R', '?', 'M', 'R', 'M', 'R', 'B', None, 'M', '?', '?', 'M', 'M', 'R', 'M', '\n', 'T', 'M'): 1,
#     ('M', 'M', '?', 'M', '?', 'E', '\n', 'R', 'T', '?', 'M', 'E', 'M', 'E', 'R', 'B', None, 'M', '?', 'M', 'M', 'M', 'E', 'M', 'E', 'T', 'E', 'M', '?', 'M', '?', 'R', 'B', None, 'M', '?', 'M', '\n', 'R', 'T', '?', 'M', 'E', 'M', 'E', 'R', 'B', None, 'M', '?', 'M', 'M', 'M', 'E', 'M', 'E', 'T', 'E', 'M', '?', 'M', '?', 'R', 'B', None, 'M', '?', 'M', '\n', '?', 'E', 'R', 'E', 'T', 'E', 'M', 'M', '?', 'E', 'R', 'B'): 1,
#     ('M', '?', '?', 'M', '?', 'E', 'M', '\n', 'T', 'R', '\n', 'T', 'R', '\n', 'M', 'T', '?', 'R'): 1,
#     # Simplified version of the key with ")2(" - assuming count is 2
#     ('M', 'M', '\n', '?', 'M', 'R', 'M', 'R', 'T', '?', '\n', 'M', 'M', 'M', 'R'): 2,
#      # Simplified version of the key with ")7(" - assuming count is 7
#     ('M', '?', '?', '?', 'M', 'R', 'M', 'M', 'T', 'R', 'M', 'R', 'M', 'M', 'R'): 7,
#     # Another complex one from prompt (assuming cleanup and count is 1)
#      ('M', 'M', 'M', 'M', 'M', 'R', '\n', 'T', 'M', 'E', 'M', 'R', 'T', 'M', 'R', 'E', '\n', '?', 'R', 'B', None, 'M', '?', '?', 'M', '?', 'R', 'M', 'R', 'T', '?', 'M', '\n', 'R', 'T', 'R'): 1,
#
# })

# --- Key Encoding Function ---


def encode_key_tuple(key_tuple: tuple) -> bytes:
    """Encodes a tuple of Optional[str] into a bytes object for marisa_trie."""
    if not key_tuple:
        return b""  # Empty tuple maps to empty bytes

    encoded_elements = []
    for element in key_tuple:
        if element is None:
            encoded_elements.append(NONE_REPR_BYTES)
        elif isinstance(element, str):
            # Ensure the string doesn't contain the separator byte after encoding
            # Using utf-8 is standard. Replace invalid bytes if necessary.
            element_bytes = element.encode("utf-8", errors="replace")
            if SEPARATOR_BYTE in element_bytes:
                # This case should be rare if the separator is chosen well (like \x00)
                # If it happens, you might need a more complex encoding/escaping scheme
                raise ValueError(
                    f"Element '{element}' contains separator byte after encoding."
                )
            encoded_elements.append(element_bytes)
        else:
            raise TypeError(f"Unsupported element type in key tuple: {type(element)}")

    return SEPARATOR_BYTE.join(encoded_elements)


# --- Marisa-Trie Creation ---


def build_marisa_trie(counter_data: collections.Counter) -> marisa_trie.Trie:
    """Builds a marisa_trie.Trie from the Counter object."""
    print("Encoding keys for marisa-trie...")
    marisa_data = []
    for key_tuple, count in counter_data.items():
        if not isinstance(key_tuple, tuple):
            print(
                f"Warning: Skipping invalid key type: {type(key_tuple)} ({key_tuple})"
            )
            continue
        try:
            byte_key = encode_key_tuple(key_tuple)
            marisa_data.append((byte_key, (count,)))  # Value must be a tuple for Trie
        except (TypeError, ValueError) as e:
            print(f"Warning: Skipping key {key_tuple} due to encoding error: {e}")
            continue

    print(f"Building marisa-trie with {len(marisa_data)} items...")
    # Use value_format='=i' if counts are within signed 32-bit integer range
    # Use value_format='=I' for unsigned 32-bit integer
    # Use value_format='=q' for signed 64-bit integer (safer for large counts)
    # The value provided during construction MUST be a tuple containing one integer
    # matching the format.
    try:
        # Attempt with 64-bit signed int first, adjust if needed
        trie = marisa_trie.Trie(data=marisa_data)
        # Check if a known key works
        test_key = ("M", "M")
        if test_key in counter_data:
            encoded_test_key = encode_key_tuple(test_key)
            retrieved_value = trie.get(encoded_test_key)
            print(
                f"Test retrieval for {test_key}: {retrieved_value} (Expected: ({counter_data[test_key]},))"
            )
            assert retrieved_value == (counter_data[test_key],)  # Verify value format
        print("Marisa-Trie built successfully.")
        return trie
    except Exception as e:
        print(f"Error building marisa-trie: {e}")
        print(
            "Check value_format compatibility with your count values if errors occur."
        )
        return None


# --- Trie Visualization (using a standard dict-based Trie) ---

# Special marker for the end of a path/key in the visualization trie
END_MARKER = object()
# Key to store the count value in the visualization trie node
COUNT_VALUE_KEY = object()


def add_to_viz_trie(viz_trie_root, key_tuple, count):
    """Adds a key tuple and its count to the dictionary-based visualization Trie."""
    node = viz_trie_root
    for element in key_tuple:
        # Use str(element) for node keys in the dict to handle None gracefully
        element_key = str(element)
        if element_key not in node:
            node[element_key] = {}
        node = node[element_key]

    # Mark the end of the sequence and store the count
    node[END_MARKER] = True
    node[COUNT_VALUE_KEY] = count


def build_viz_trie(counter_data: collections.Counter):
    """Builds a dictionary-based Trie suitable for visualization."""
    print("Building visualization trie...")
    viz_root = {}
    # Handle the empty tuple case separately if it has a count
    if () in counter_data:
        viz_root[END_MARKER] = True
        viz_root[COUNT_VALUE_KEY] = counter_data[()]

    for key_tuple, count in counter_data.items():
        if not key_tuple:  # Skip empty tuple, already handled
            continue
        if not isinstance(key_tuple, tuple):  # Skip invalid keys
            continue
        add_to_viz_trie(viz_root, key_tuple, count)
    print("Visualization trie built.")
    return viz_root


def visualize_trie(
    viz_trie_root, filename="trie_visualization", max_depth=10, max_nodes=1000
):
    """Visualizes the dictionary-based Trie using Graphviz."""
    print(f"Generating visualization (max_depth={max_depth}, max_nodes={max_nodes})...")
    dot = graphviz.Digraph(comment="Trie Visualization", format="png")
    dot.attr(rankdir="LR")  # Left-to-right layout often better for Tries

    node_count = 0
    edge_count = 0

    # Root node
    root_id = "root_" + str(uuid.uuid4())  # Unique ID for root
    root_label = "START"
    is_terminal_root = viz_trie_root.get(END_MARKER, False)
    root_attrs = {"shape": "doublecircle" if is_terminal_root else "circle"}
    if is_terminal_root:
        count = viz_trie_root.get(COUNT_VALUE_KEY, "?")
        root_label += f"\n(Count: {count})"
        root_attrs["style"] = "filled"
        root_attrs["fillcolor"] = "lightblue"

    dot.node(root_id, root_label, **root_attrs)
    node_count += 1

    # Queue for BFS traversal (node_dict, parent_id, current_depth)
    queue = collections.deque([(viz_trie_root, root_id, 0)])
    visited_nodes = {root_id}  # Keep track of graphviz node IDs created

    while queue:
        if node_count > max_nodes:
            print(
                f"Warning: Visualization truncated due to reaching max_nodes limit ({max_nodes})."
            )
            dot.node(
                "trunc_nodes",
                f"... {node_count - max_nodes}+ more nodes omitted ...",
                shape="plaintext",
            )
            break

        current_node_dict, parent_node_id, depth = queue.popleft()

        if depth >= max_depth:
            if depth == max_depth:  # Add truncation indicators only once per branch
                trunc_id = f"trunc_{parent_node_id}"
                if trunc_id not in visited_nodes:
                    dot.node(trunc_id, "...", shape="plaintext")
                    dot.edge(parent_node_id, trunc_id, style="dotted")
                    visited_nodes.add(trunc_id)
            continue  # Stop traversing deeper

        # Sort items for consistent layout (optional)
        sorted_items = sorted(current_node_dict.items(), key=lambda item: str(item[0]))

        for element_key, child_node_dict in sorted_items:
            # Skip our special markers
            if element_key == END_MARKER or element_key == COUNT_VALUE_KEY:
                continue

            # Create a unique ID for the child node
            # Using parent ID + element ensures uniqueness along the path
            child_node_id = f"{parent_node_id}_{element_key}_{str(uuid.uuid4())[:4]}"  # Add short uuid to help uniqueness if needed

            if (
                child_node_id in visited_nodes
            ):  # Should ideally not happen with UUID part
                continue

            is_terminal = child_node_dict.get(END_MARKER, False)
            node_label = str(
                element_key
            )  # Label is the element itself ('M', 'None', '?')

            node_attrs = {"shape": "doublecircle" if is_terminal else "circle"}
            if is_terminal:
                count = child_node_dict.get(COUNT_VALUE_KEY, "?")
                node_label += f"\n(Count: {count})"
                node_attrs["style"] = "filled"
                node_attrs["fillcolor"] = "lightcoral" if count == 1 else "lightgreen"

            # Add node only if within limits
            if node_count < max_nodes:
                dot.node(child_node_id, node_label, **node_attrs)
                visited_nodes.add(child_node_id)
                node_count += 1
                # Add edge from parent
                dot.edge(parent_node_id, child_node_id)
                edge_count += 1
                # Add child to queue for further traversal
                queue.append((child_node_dict, child_node_id, depth + 1))
            else:
                # Stop adding nodes if limit reached, break inner loop
                break

    print(f"Graph generated with {node_count} nodes and {edge_count} edges.")
    try:
        dot.render(filename, view=False)
        print(f"Visualization saved to {filename}.png (and .gv)")
    except Exception as e:
        print(f"Error rendering graph with Graphviz: {e}")
        print("Ensure Graphviz executables are installed and in your system's PATH.")
        print("On Ubuntu/Debian: sudo apt-get install graphviz")
        print("On macOS (using Homebrew): brew install graphviz")
        print("On Windows: Download from graphviz.org and add bin directory to PATH.")


# --- Main Execution ---

if __name__ == "__main__":
    with open(r"../floor_paths.pkl", "rb") as f:
        data = pickle.load(f)

    # 1. Build the marisa-trie (optional, but part of the request)
    m_trie = build_marisa_trie(data)

    if m_trie:
        # Example: Look up a key in the marisa-trie
        key_to_lookup = ("M", None, "T")
        encoded_key = encode_key_tuple(key_to_lookup)
        value = m_trie.get(encoded_key)
        if value:
            print(
                f"Lookup in marisa-trie for {key_to_lookup}: Count = {value[0]}"
            )  # Value is tuple (count,)
        else:
            print(f"Key {key_to_lookup} not found in marisa-trie.")

        # Example: Prefix search (find all keys starting with ('M', 'M'))
        prefix_to_search = ("M", "M")
        encoded_prefix = encode_key_tuple(prefix_to_search)
        print(f"\nKeys in marisa-trie starting with {prefix_to_search}:")
        # Note: marisa-trie returns byte keys, you'd need to decode them back if needed
        # This is complex due to the separator and None encoding.
        # We primarily built it for storage/lookup efficiency per the prompt.
        count_limit = 5
        found_count = 0
        try:
            for i, key_bytes in enumerate(m_trie.iterkeys(encoded_prefix)):
                if i < count_limit:
                    # Attempting to decode is illustrative but can be tricky
                    # print(f"  - {key_bytes}") # Raw bytes key
                    pass  # Decoding logic omitted for brevity
                else:
                    print(f"  ... (and potentially more)")
                    break
                found_count += 1
            if found_count == 0:
                print("  (None found)")
        except KeyError:
            print("  (Prefix not found or no keys start with it)")

    # 2. Build the visualization Trie (dictionary-based)
    viz_trie = build_viz_trie(data)

    # 3. Visualize the dictionary-based Trie
    # Adjust max_depth and max_nodes if the graph is too large or too small
    # For very large Tries, visualization might become slow and cluttered.
    visualize_trie(viz_trie, filename="my_counter_trie_viz", max_depth=8, max_nodes=200)
