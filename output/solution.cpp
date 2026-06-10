class Solution {
public:
    long long maxTotalValue(vector<int>& nums, int k) {
        int n = nums.size();
        vector<vector<long long>> dp(n + 1, vector<long long>(k + 1, 0));
        
        for (int i = 1; i <= n; i++) {
            for (int j = 1; j <= k && j <= i * (i + 1) / 2; j++) {
                long long maxVal = 0;
                for (int l = 0; l < i; l++) {
                    long long val = *max_element(nums.begin() + l, nums.begin() + i) - *min_element(nums.begin() + l, nums.begin() + i) + dp[l][j - 1];
                    maxVal = max(maxVal, val);
                }
                dp[i][j] = maxVal;
            }
        }
        
        return dp[n][k];
    }
};