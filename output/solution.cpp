#include <vector>
#include <queue>
using namespace std;
const int MOD = 1e9 + 7;

class Solution {
public:
    int edgeScore(vector<vector<int>>& edges, int node) {
        vector<vector<int>> graph(edges.size() + 1);
        for (auto& edge : edges) {
            graph[edge[0]].push_back(edge[1]);
            graph[edge[1]].push_back(edge[0]);
        }
        return dfs(graph, node, 1);
    }

    int dfs(vector<vector<int>>& graph, int target, int node) {
        if (node == target) return 1;
        int ans = 0;
        for (int child : graph[node]) {
            ans = (ans + dfs(graph, target, child)) % MOD;
        }
        ans = (ans * 2) % MOD;
        return ans;
    }

    int assignEdgeWeights(vector<vector<int>>& edges) {
        vector<vector<int>> graph(edges.size() + 1);
        for (auto& edge : edges) {
            graph[edge[0]].push_back(edge[1]);
            graph[edge[1]].push_back(edge[0]);
        }
        queue<pair<int, int>> q;
        q.push({1, 0});
        int maxDepth = -1;
        pair<int, int> deepest;
        while (!q.empty()) {
            auto node = q.front();
            q.pop();
            if (node.second > maxDepth) {
                maxDepth = node.second;
                deepest = node;
            }
            for (int child : graph[node.first]) {
                q.push({child, node.second + 1});
            }
        }
        return edgeScore(edges, deepest.first);
    }
};