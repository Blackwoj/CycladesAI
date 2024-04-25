class Graph:
    def __init__(self):
        self.vertices = {}  # Słownik przechowujący wierzchołki i ich sąsiadów
        self.colors = {}  # Słownik przechowujący kolory wierzchołków

    def add_vertex(self, vertex_name, color):
        if vertex_name not in self.vertices:
            self.vertices[vertex_name] = set()
            self.colors[vertex_name] = color

    def add_edge(self, vertex1, vertex2):
        self.vertices[vertex1].add(vertex2)
        self.vertices[vertex2].add(vertex1)

    def set_vertex_color(self, vertex_name, color):
        if vertex_name in self.colors:
            self.colors[vertex_name] = color

    def has_connection(self, start_vertex, end_vertex, target_color):
        visited = set()

        def dfs(current_vertex, target_vertex, target_color, visited):
            if current_vertex == target_vertex:
                return True
            visited.add(current_vertex)
            for neighbor in self.vertices[current_vertex]:
                if neighbor not in visited and self.colors[neighbor] == target_color:
                    if dfs(neighbor, target_vertex, target_color, visited):
                        return True
                elif neighbor == end_vertex:
                    return True
            return False

        return dfs(start_vertex, end_vertex, target_color, visited)

    def act_graph_status(self):
        for node, color in self.vertices.items():
            print(node, self.colors[node])
