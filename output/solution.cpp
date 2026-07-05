class Solution {
public:
    vector<int> pathsWithMaxScore(vector<string>& board) {
        int n = board.size();
        vector<vector<vector<int>>> dp(n, vector<vector<int>>(n, vector<int>(2, 0)));
        
        dp[n - 1][n - 1][0] = board[n - 1][n - 1] == 'S' ? 0 : board[n - 1][n - 1] - '0';
        dp[n - 1][n - 1][1] = 1;
        
        for (int i = n - 1; i >= 0; --i) {
            for (int j = n - 1; j >= 0; --j) {
                if (i == n - 1 && j == n - 1) continue;
                if (board[i][j] == 'X' || board[i][j] == 'E') {
                    dp[i][j][1] = 0;
                    if (board[i][j] == 'E') {
                        dp[i][j][0] = 0;
                    }
                    continue;
                }
                
                vector<int> maxScoreAndCount(2, 0);
                if (i + 1 < n && dp[i + 1][j][0] > maxScoreAndCount[0]) {
                    maxScoreAndCount[0] = dp[i + 1][j][0];
                    maxScoreAndCount[1] = dp[i + 1][j][1];
                }
                else if (i + 1 < n && dp[i + 1][j][0] == maxScoreAndCount[0]) {
                    maxScoreAndCount[1] = (maxScoreAndCount[1] + dp[i + 1][j][1]) % 1000000007;
                }
                
                if (j + 1 < n && dp[i][j + 1][0] > maxScoreAndCount[0]) {
                    maxScoreAndCount[0] = dp[i][j + 1][0];
                    maxScoreAndCount[1] = dp[i][j + 1][1];
                }
                else if (j + 1 < n && dp[i][j + 1][0] == maxScoreAndCount[0]) {
                    maxScoreAndCount[1] = (maxScoreAndCount[1] + dp[i][j + 1][1]) % 1000000007;
                }
                
                if (i + 1 < n && j + 1 < n && dp[i + 1][j + 1][0] > maxScoreAndCount[0]) {
                    maxScoreAndCount[0] = dp[i + 1][j + 1][0];
                    maxScoreAndCount[1] = dp[i + 1][j + 1][1];
                }
                else if (i + 1 < n && j + 1 < n && dp[i + 1][j + 1][0] == maxScoreAndCount[0]) {
                    maxScoreAndCount[1] = (maxScoreAndCount[1] + dp[i + 1][j + 1][1]) % 1000000007;
                }
                
                dp[i][j][0] = maxScoreAndCount[0] + board[i][j] - '0';
                dp[i][j][1] = maxScoreAndCount[1];
            }
        }
        
        return {dp[0][0][0], dp[0][0][1]};
    }
};