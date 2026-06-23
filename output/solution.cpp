const int MOD = 1e9 + 7;
class Solution {
public:
    int numberOfArrays(int n, int l, int r) {
        vector<vector<long long>> dp(n, vector<long long>(2, 0));
        dp[0][0] = r - l + 1;
        dp[1][0] = r - l;
        
        // Compute dp values for n >= 2
        for (int i = 1; i < n; i++) {
            vector<vector<long long>> next(2, vector<long long>(2, 0));
            for (int prevInc = 0; prevInc < 2; prevInc++) {
                for (int prevDec = 0; prevDec < 2; prevDec++) {
                    for (int j = l; j <= r; j++) {
                        if (prevInc == 1 && prevDec == 0 && j < l + i) next[0][0] = (next[0][0] + dp[i-1][0]) % MOD; 
                        if (prevInc == 0 && prevDec == 1 && j > r - i) next[1][1] = (next[1][1] + dp[i-1][1]) % MOD; 
                        if (prevInc == 0 && prevDec == 0 && j > l + i - 1 && j < r - i + 1) next[0][1] = (next[0][1] + dp[i-1][0]) % MOD;
                        if (prevInc == 1 && prevDec == 1 && j > l + i - 1 && j < r - i + 1) next[1][0] = (next[1][0] + dp[i-1][1]) % MOD;
                    }
                }
            }
            dp = next;
        }
        
        // Compute final answer
        long long res = (dp[0][0] + dp[0][1] + dp[1][0] + dp[1][1]) % MOD;
        
        return res;
    }
};