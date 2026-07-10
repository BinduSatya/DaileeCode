class Solution {
public:
    vector<int> shortestPath(int n, vector<int>& nums, int maxDiff, vector<vector<int>>& queries) {
        vector<unordered_map<int, int>> graph(n);
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                if (i != j && abs(nums[i] - nums[j]) <= maxDiff) {
                    graph[i][j] = 1;
                }
            }
        }
        
        vector<int> results;
        for (auto& query : queries) {
            int start = query[0], end = query[1];
            if (start == end) {
                results.push_back(0);
                continue;
            }
            
            queue<pair<int, int>> q;
            q.push({start, 0});
            vector<bool> visited(n, false);
            visited[start] = true;
            
            bool found = false;
            while (!q.empty()) {
                auto [node, dist] = q.front();
                q.pop();
                
                for (auto& neighbor : graph[node]) {
                    if (!visited[neighbor.first]) {
                        visited[neighbor.first] = true;
                        if (neighbor.first == end) {
                            results.push_back(dist + 1);
                            found = true;
                            break;
                        }
                        q.push({neighbor.first, dist + 1});
                    }
                }
                
                if (found) break;
            }
            
            if (!found) results.push_back(-1);
        }
        
        return results;
    }
};