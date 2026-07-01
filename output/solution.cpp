class Solution {
public:
    int maximumSafenessFactor(vector<vector<int>>& grid) {
        int n = grid.size();
        int maxSafeness = 0;
        
        // Calculate Manhattan distance to the nearest thief for each cell
        vector<vector<int>> dist(n, vector<int>(n, INT_MAX));
        queue<pair<int, int>> q;
        
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                if (grid[i][j] == 1) {
                    dist[i][j] = 0;
                    q.push({i, j});
                }
            }
        }
        
        vector<int> dirs = {-1, 0, 1, 0, -1};
        while (!q.empty()) {
            int x = q.front().first;
            int y = q.front().second;
            q.pop();
            
            for (int k = 0; k < 4; k++) {
                int nx = x + dirs[k];
                int ny = y + dirs[k + 1];
                
                if (nx >= 0 && nx < n && ny >= 0 && ny < n && dist[nx][ny] > dist[x][y] + 1) {
                    dist[nx][ny] = dist[x][y] + 1;
                    q.push({nx, ny});
                }
            }
        }
        
        // Find the maximum safeness factor for all paths
        set<int> safeness;
        function<void(int, int, int)> dfs = [&](int x, int y, int currSafeness) {
            if (x == n - 1 && y == n - 1) {
                safeness.insert(currSafeness);
                return;
            }
            
            for (int k = 0; k < 4; k++) {
                int nx = x + dirs[k];
                int ny = y + dirs[k + 1];
                
                if (nx >= 0 && nx < n && ny >= 0 && ny < n) {
                    dfs(nx, ny, min(currSafeness, dist[nx][ny]));
                }
            }
        };
        
        dfs(0, 0, INT_MAX);
        
        return *safeness.rbegin();
    }
};