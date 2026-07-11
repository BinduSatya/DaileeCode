class Solution {
public:
    int countCompleteComponents(int n, vector<vector<int>>& edges) {
        vector<vector<int>> graph(n);
        for (auto& edge : edges) {
            graph[edge[0]].push_back(edge[1]);
            graph[edge[1]].push_back(edge[0]);
        }
        
        vector<bool> visited(n, false);
        int count = 0;
        
        for (int i = 0; i < n; i++) {
            if (!visited[i]) {
                vector<int> component;
                dfs(graph, i, visited, component);
                
                bool isComplete = true;
                for (int u : component) {
                    for (int v : component) {
                        if (u != v && find(graph[u].begin(), graph[u].end(), v) == graph[u].end()) {
                            isComplete = false;
                            break;
                        }
                    }
                    if (!isComplete) break;
                }
                
                if (isComplete) count++;
            }
        }
        
        return count;
    }
    
    void dfs(vector<vector<int>>& graph, int node, vector<bool>& visited, vector<int>& component) {
        visited[node] = true;
        component.push_back(node);
        
        for (int neighbor : graph[node]) {
            if (!visited[neighbor]) {
                dfs(graph, neighbor, visited, component);
            }
        }
    }
};