class Solution {
public:
    int minElement(vector<int>& nums) {
        int min_sum = INT_MAX;
        for (int num : nums) {
            int sum = 0;
            while (num > 0) {
                sum += num % 10;
                num /= 10;
            }
            min_sum = min(min_sum, sum);
        }
        return min_sum;
    }
};