class Solution {
public:
    int minScore(int n, vector<vector<int>>& roads) {
        // Sort roads in ascending order of distances
        sort(roads.begin(), roads.end(), [](const vector<int>& a, const vector<int>& b) {
            return a[2] < b[2];
        });

        // Initialize Union-Find data structure
        vector<int> parent(n + 1);
        for (int i = 1; i <= n; i++) {
            parent[i] = i;
        }

        // Function to find the parent of a node
        auto find = [&](int x, vector<int>& parent) -> int {
            if (parent[x] != x) {
                parent[x] = find(parent[x], parent);
            }
            return parent[x];
        };

        // Function to union two nodes
        auto unionNodes = [&](int x, int y, vector<int>& parent) {
            int rootX = find(x, parent);
            int rootY = find(y, parent);
            if (rootX != rootY) {
                parent[rootX] = rootY;
            }
        };

        // Iterate over sorted roads and union nodes
        int minScore = INT_MAX;
        for (const auto& road : roads) {
            if (find(1, parent) != find(n, parent)) {
                unionNodes(road[0], road[1], parent);
                minScore = min(minScore, road[2]);
            }
        }

        return minScore;
    }
};