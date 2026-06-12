#include <vector>
#include <unordered_map>

using namespace std;
const int MOD = 1e9 + 7;

void dfs(int u, int p, const vector<vector<int>>& edges, vector<vector<int>>& adj, vector<int>& depth) {
    for (int v : adj[u]) if (v != p) {
        depth[v] = depth[u] + 1;
        dfs(v, u, edges, adj, depth);
    }
}

class Solution {
public:
    vector<int> assignEdgeWeights(vector<vector<int>>& edges, vector<vector<int>>& queries) {
        int n = edges.size() + 1;
        vector<vector<int>> adj(n);
        for (auto& edge : edges) {
            adj[edge[0] - 1].push_back(edge[1] - 1);
            adj[edge[1] - 1].push_back(edge[0] - 1);
        }
        
        vector<int> depth(n, 0);
        dfs(0, -1, edges, adj, depth);
        
        vector<int> res(queries.size(), 0);
        for (int i = 0; i < queries.size(); i++) {
            int len = abs(depth[queries[i][0] - 1] - depth[queries[i][1] - 1]);
            if (len & 1) res[i] = exp(2, len - 1);
            else res[i] = exp(2, len - 1);
        }
        
        return res;
    }
    
    long long exp(int b, int p) {
        if (p == 0) return 1;
        long long r = exp(b, p / 2) % MOD;
        r = r * r % MOD;
        if (p & 1) return r * b % MOD;
        return r;
    }
};