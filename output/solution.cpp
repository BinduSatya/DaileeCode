class Solution {
public:
    vector<int> leftRightDifference(vector<int>& nums) {
        int n = nums.size();
        vector<int> answer(n);
        
        for (int i = 0; i < n; i++) {
            int leftSum = 0;
            int rightSum = 0;
            
            // Calculate leftSum
            for (int j = 0; j < i; j++) {
                leftSum += nums[j];
            }
            
            // Calculate rightSum
            for (int j = i + 1; j < n; j++) {
                rightSum += nums[j];
            }
            
            // Calculate absolute difference
            answer[i] = abs(leftSum - rightSum);
        }
        
        return answer;
    }
};