class Solution {
public:
    long long maxTotalValue(vector<int>& nums, int k) {
        int n = nums.size();
        long long res = 0;
        for (int l = 0; l < n; l++) {
            int mx = nums[l], mn = nums[l];
            for (int r = l; r < n; r++) {
                mx = max(mx, nums[r]);
                mn = min(mn, nums[r]);
                res = max(res, static_cast<long long>(mx - mn) * k);
            }
        }
        return res;
    }
};