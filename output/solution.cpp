#include <vector>
using namespace std;

const int MOD = 1e9 + 7;

class Solution {
public:
    int numberOfZigZagArrays(int n, int lower, int upper) {
        long long dp[2][2] = {0}; // 0 for decreasing, 1 for increasing
        for (int i = lower; i <= upper; i++) {
            long long newDp[2][2] = {0};
            if (!dp[0][0] && !dp[0][1] && !dp[1][0] && !dp[1][1]) {
                newDp[0][0] = (upper - i < 1 ? 0 : upper - i);
                newDp[0][1] = (i - lower < 1 ? 0 : i - lower);
                newDp[1][0] = (upper - i < 1 ? 0 : upper - i);
                newDp[1][1] = (i - lower < 1 ? 0 : i - lower);
            } else {
                newDp[0][0] = (dp[0][1] + dp[1][1]) % MOD;
                newDp[0][1] = (dp[0][0] + dp[1][0]) % MOD;
                newDp[1][0] = (dp[0][1] + dp[1][1]) % MOD;
                newDp[1][1] = (dp[0][0] + dp[1][0]) % MOD;
            }
            dp[0][0] = newDp[0][0];
            dp[0][1] = newDp[0][1];
            dp[1][0] = newDp[1][0];
            dp[1][1] = newDp[1][1];
        }
        long long ans = (dp[0][0] + dp[0][1] + dp[1][0] + dp[1][1]) % MOD;
        return ans;
    }
};