class Solution {
public:
    bool findSafeWalk(vector<vector<int>>& grid, int health) {
        int m = grid.size();
        int n = grid[0].size();
        int maxHealth = m + n;
        vector<vector<bool>> dp(m, vector<bool>(n, false));
        dp[0][0] = true;
        
        // Try to reach every cell in the first row
        for (int i = 1; i < n; ++i) {
            if (grid[0][i] == 0 && dp[0][i-1]) {
                dp[0][i] = true;
            } else if (grid[0][i] == 1 && dp[0][i-1] && health > 1) {
                dp[0][i] = true;
            }
        }
        
        // Try to reach every cell in the first column
        for (int i = 1; i < m; ++i) {
            if (grid[i][0] == 0 && dp[i-1][0]) {
                dp[i][0] = true;
            } else if (grid[i][0] == 1 && dp[i-1][0] && health > 1) {
                dp[i][0] = true;
            }
        }
        
        // Fill the rest of the dp table
        for (int i = 1; i < m; ++i) {
            for (int j = 1; j < n; ++j) {
                if (grid[i][j] == 0) {
                    dp[i][j] = (dp[i-1][j] || dp[i][j-1]);
                } else {
                    dp[i][j] = (dp[i-1][j] || dp[i][j-1]) && health > 1;
                }
            }
        }
        
        return dp[m-1][n-1];
    }
};