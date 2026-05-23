class Solution {
public:
    bool check(vector<int>& nums) {
        int count = 0;
        for (int i = 0; i < nums.size() - 1; i++) {
            if (nums[i] > nums[i + 1]) {
                count++;
            }
        }
        if (nums.back() > nums.front()) {
            count++;
        }
        return count <= 1;
    }
};