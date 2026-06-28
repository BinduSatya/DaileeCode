class Solution {
public:
    int maximumElementAfterDecrementingAndRearranging(vector<int>& arr) {
        sort(arr.begin(), arr.end());
        int max_val = 1;
        for (int i = 1; i < arr.size(); i++) {
            max_val = min(max_val + 1, arr[i]);
        }
        return max_val;
    }
};